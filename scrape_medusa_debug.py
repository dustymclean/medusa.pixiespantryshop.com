"""
DEBUG Medusa Scraper:
- Auto-login with credentials
- Scrape ONLY in-stock items (simplified)
- Print progress to terminal
"""
import asyncio
from playwright.async_api import async_playwright

# Credentials
MEDUSA_URL = "https://medusadistribution.com/login"
USERNAME = "admin@pixies-pantry.com"
PASSWORD = "PixiesPantry1!"

async def scrape_medusa():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)  # Run visible for debugging
        page = await browser.new_page()
        
        print("🔍 Attempting to log in...")
        await page.goto(MEDUSA_URL)
        await page.fill('input[name="email"]', USERNAME)
        await page.fill('input[name="password"]', PASSWORD)
        await page.click('button[type="submit"]')
        
        # Wait for login to complete
        try:
            await page.wait_for_url("https://medusadistribution.com/dashboard", timeout=10000)
            print("✅ Login successful!")
        except Exception as e:
            print(f"❌ Login failed: {e}")
            await browser.close()
            return
        
        print("🔍 Navigating to Products...")
        await page.click('a[href="/products"]')
        await page.wait_for_selector(".product-list")
        print("✅ Products page loaded!")
        
        print("🔍 Filtering for in-stock items...")
        await page.click('button:has-text("Filters")')
        await page.click('input[type="checkbox"][value="in_stock"]')
        await page.click('button:has-text("Apply")')
        await page.wait_for_timeout(2000)
        print("✅ Filter applied!")
        
        print("🔍 Extracting product data...")
        rows = await page.query_selector_all(".product-list tbody tr")
        print(f"📊 Found {len(rows)} in-stock products!")
        
        for i, row in enumerate(rows[:5]):  # Print first 5 for debugging
            sku = await row.query_selector("td:nth-child(1)")
            name = await row.query_selector("td:nth-child(2)")
            price = await row.query_selector("td:nth-child(5)")
            stock = await row.query_selector("td:nth-child(7)")
            
            print(f"Product {i+1}:")
            print(f"  SKU: {await sku.inner_text() if sku else 'N/A'}")
            print(f"  Name: {await name.inner_text() if name else 'N/A'}")
            print(f"  Price: {await price.inner_text() if price else 'N/A'}")
            print(f"  Stock: {await stock.inner_text() if stock else 'N/A'}")
            print("---")
        
        await browser.close()
        print("✅ Debug scrape complete!")

if __name__ == "__main__":
    asyncio.run(scrape_medusa())