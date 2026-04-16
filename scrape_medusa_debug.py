"""
DEBUG Medusa Scraper:
- Manual login test
- Extended timeouts
- Debug output
"""
import asyncio
from playwright.async_api import async_playwright

# Credentials
MEDUSA_URL = "https://medusadistribution.com/login"
USERNAME = "admin@pixies-pantry.com"
PASSWORD = "PixiesPantry1!"

async def scrape_medusa():
    async with async_playwright() as p:
        # Launch browser (visible for debugging)
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("🔍 Opening login page...")
        await page.goto(MEDUSA_URL, timeout=60000)  # 60s timeout
        print("✅ Page loaded!")
        
        # Wait for email field (with debug)
        try:
            print("🔍 Waiting for email field...")
            await page.wait_for_selector('input[name="email"]', timeout=60000)
            print("✅ Email field found!")
        except Exception as e:
            print(f"❌ Email field not found: {e}")
            print("📸 Taking screenshot for debugging...")
            await page.screenshot(path="debug_login_page.png")
            print("📸 Screenshot saved to debug_login_page.png")
            await browser.close()
            return
        
        # Fill login form
        print("🔍 Filling login form...")
        await page.fill('input[name="email"]', USERNAME)
        await page.fill('input[name="password"]', PASSWORD)
        await page.click('button[type="submit"]')
        
        # Wait for dashboard
        try:
            print("🔍 Waiting for dashboard...")
            await page.wait_for_url("https://medusadistribution.com/dashboard", timeout=60000)
            print("✅ Login successful!")
        except Exception as e:
            print(f"❌ Login failed: {e}")
            print("📸 Taking screenshot...")
            await page.screenshot(path="debug_login_error.png")
            print("📸 Screenshot saved to debug_login_error.png")
            await browser.close()
            return
        
        print("🎉 Debug complete! You can now close the browser.")
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(scrape_medusa())