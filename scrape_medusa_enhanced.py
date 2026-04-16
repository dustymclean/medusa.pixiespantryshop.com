"""
Scrape Medusa Distribution for a FULL catalog experience:
- MSRP, Wholesale Price, Descriptions, Images, Specs
- Badges (Pixie's Pick, On Sale, Featured)
- In-stock products only
"""
import asyncio
from playwright.async_api import async_playwright
import csv
import os
import aiohttp
import aiofiles

# Credentials
MEDUSA_URL = "https://medusadistribution.com/login"
USERNAME = "admin@pixies-pantry.com"
PASSWORD = "Pixie'sPantry1!"

# Output
OUTPUT_DIR = os.path.expanduser("~/Desktop/medusa.pixiespantryshop.com")
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "data/medusa_products_enhanced.csv")
IMAGE_DIR = os.path.join(OUTPUT_DIR, "images")

os.makedirs(IMAGE_DIR, exist_ok=True)

async def download_image(session, url, filename):
    """Download an image and save it to the images directory"""
    try:
        async with session.get(url) as response:
            if response.status == 200:
                async with aiofiles.open(os.path.join(IMAGE_DIR, filename), 'wb') as f:
                    await f.write(await response.read())
                return filename
    except Exception as e:
        print(f"⚠️ Failed to download image {url}: {e}")
    return ""

async def scrape_medusa():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)  # Run visible for debugging
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
        
        async with aiohttp.ClientSession() as session:
            for row in rows:
                try:
                    sku = await row.query_selector("td:nth-child(1)")
                    name = await row.query_selector("td:nth-child(2)")
                    brand = await row.query_selector("td:nth-child(3)")
                    price = await row.query_selector("td:nth-child(4)")
                    msrp = await row.query_selector("td:nth-child(5)")
                    wholesale_price = await row.query_selector("td:nth-child(6)")
                    stock = await row.query_selector("td:nth-child(7)")
                    image = await row.query_selector("img")
                    
                    sku = await sku.inner_text() if sku else ""
                    name = await name.inner_text() if name else ""
                    brand = await brand.inner_text() if brand else ""
                    price = await price.inner_text() if price else "0"
                    msrp = await msrp.inner_text() if msrp else "0"
                    wholesale_price = await wholesale_price.inner_text() if wholesale_price else "0"
                    stock = await stock.inner_text() if stock else "0"
                    image_url = await image.get_attribute("src") if image else ""
                    
                    # Click product to get full details
                    await row.click()
                    await page.wait_for_selector(".product-detail")
                    
                    # Extract description and specs
                    description = await page.query_selector(".product-detail .description")
                    description = await description.inner_text() if description else ""
                    
                    specs = {}
                    spec_elements = await page.query_selector_all(".product-detail .spec")
                    for spec in spec_elements:
                        key = await spec.query_selector(".spec-key")
                        value = await spec.query_selector(".spec-value")
                        if key and value:
                            specs[await key.inner_text()] = await value.inner_text()
                    
                    await page.go_back()
                    await page.wait_for_selector(".product-list")
                    
                    # Clean data
                    price = float(price.replace("$", "").strip())
                    msrp = float(msrp.replace("$", "").strip())
                    wholesale_price = float(wholesale_price.replace("$", "").strip())
                    stock = int(stock.strip())
                    image_filename = os.path.basename(image_url) if image_url else ""
                    
                    # Download image
                    if image_url:
                        image_filename = await download_image(session, image_url, f"{sku}.jpg")
                    
                    if sku and name and price > 0 and image_filename:
                        products.append({
                            "brand": brand,
                            "name": name,
                            "sku": sku,
                            "price": price,
                            "msrp": msrp,
                            "wholesale_price": wholesale_price,
                            "stock": stock,
                            "image_filename": image_filename,
                            "description": description,
                            "specs": specs,
                            "is_pick": False,  # Placeholder (update later)
                            "is_sale": msrp > price,  # Auto-detect sale
                            "is_featured": False  # Placeholder
                        })
                except Exception as e:
                    print(f"⚠️ Error parsing row: {e}")
                    continue
        
        # Write to CSV
        with open(OUTPUT_CSV, mode='w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                "brand", "name", "sku", "price", "msrp", "wholesale_price", "stock", 
                "image_filename", "description", "specs", "is_pick", "is_sale", "is_featured"
            ])
            for product in products:
                writer.writerow([
                    product["brand"],
                    product["name"],
                    product["sku"],
                    product["price"],
                    product["msrp"],
                    product["wholesale_price"],
                    product["stock"],
                    product["image_filename"],
                    product["description"],
                    str(product["specs"]),
                    product["is_pick"],
                    product["is_sale"],
                    product["is_featured"]
                ])
        
        print(f"✅ Scraped {len(products)} in-stock products to {OUTPUT_CSV}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_medusa())