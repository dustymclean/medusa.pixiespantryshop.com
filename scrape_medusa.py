"""
Scrape in-stock products from Medusa Distribution (medusadistribution.com)
using Playwright. Exports data to medusa_products_advanced.csv.
"""
import asyncio
from playwright.async_api import async_playwright
import csv
import os

# Credentials
MEDUSA_URL = "https://medusadistribution.com/login"
USERNAME = "admin@pixies-pantry.com"
PASSWORD = "PixiesPantry1!"

# Output
OUTPUT_DIR = os.path.expanduser("~/Desktop/medusa.pixiespantryshop.com/data")
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "medusa_products_advanced.csv")

async def scrape_medusa():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Log in
        await page.goto(MEDUSA_URL)
        await page.fill('input[name="email"]', USERNAME)
        await page.fill('input[name="password"]', PASSWORD)
        await page.click('button[type="submit"]')
        await page.wait_for_url("https://medusadistribution.com/dashboard")
        print("✅ Logged in to Medusa Distribution")
        
        # Navigate to products
        await page.click('a[href="/products"]')
        await page.wait_for_selector(".product-list")
        print("✅ Navigated to Products")
        
        # Filter for in-stock products
        await page.click('button:has-text("Filters")')
        await page.click('input[type="checkbox"][value="in_stock"]')
        await page.click('button:has-text("Apply")')
        await page.wait_for_timeout(2000)  # Wait for filter to apply
        print("✅ Filtered for in-stock products")
        
        # Extract product data
        products = []
        rows = await page.query_selector_all(".product-list tbody tr")
        for row in rows:
            try:
                sku = await row.query_selector("td:nth-child(1)")
                name = await row.query_selector("td:nth-child(2)")
                brand = await row.query_selector("td:nth-child(3)")
                price = await row.query_selector("td:nth-child(4)")
                stock = await row.query_selector("td:nth-child(5)")
                image = await row.query_selector("img")
                
                sku = await sku.inner_text() if sku else ""
                name = await name.inner_text() if name else ""
                brand = await brand.inner_text() if brand else ""
                price = await price.inner_text() if price else "0"
                stock = await stock.inner_text() if stock else "0"
                image_url = await image.get_attribute("src") if image else ""
                
                # Clean data
                price = float(price.replace("$", "").strip())
                stock = int(stock.strip())
                image_filename = os.path.basename(image_url) if image_url else ""
                
                if sku and name and price > 0 and image_filename:
                    products.append({
                        "brand": brand,
                        "name": name,
                        "sku": sku,
                        "price": price,
                        "stock": stock,
                        "image_filename": image_filename,
                        "is_pick": False,  # Placeholder (will update later)
                        "is_sale": False,  # Placeholder
                        "is_featured": False  # Placeholder
                    })
            except Exception as e:
                print(f"⚠️ Error parsing row: {e}")
                continue
        
        # Write to CSV
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(OUTPUT_CSV, mode='w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                "brand", "name", "sku", "price", "stock", "image_filename", 
                "is_pick", "is_sale", "is_featured"
            ])
            for product in products:
                writer.writerow([
                    product["brand"],
                    product["name"],
                    product["sku"],
                    product["price"],
                    product["stock"],
                    product["image_filename"],
                    product["is_pick"],
                    product["is_sale"],
                    product["is_featured"]
                ])
        
        print(f"✅ Scraped {len(products)} in-stock products to {OUTPUT_CSV}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_medusa())