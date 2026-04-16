"""
FIXED Medusa Scraper:
- Browser stays open until scraping completes
- Waits for product details to load
- Downloads images properly
"""
import asyncio
from playwright.async_api import async_playwright
import csv
import os
import aiohttp
import aiofiles
import json

# Credentials
MEDUSA_URL = "https://medusadistribution.com/login"
USERNAME = "admin@pixies-pantry.com"
PASSWORD = "PixiesPantry1!"

# Output
OUTPUT_DIR = os.path.expanduser("~/Desktop/medusa.pixiespantryshop.com")
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "data/medusa_products_fixed.csv")
IMAGE_DIR = os.path.join(OUTPUT_DIR, "images")

os.makedirs(IMAGE_DIR, exist_ok=True)

# Medical pivot lexicon
LEXICON = {
    "CBD": "Herbal Extract",
    "THC": "Active Compound",
    "hemp": "Botanical Source",
    "cannabis": "Aromatic Blend",
    "vape": "Aromatherapy Device",
    "dab": "Concentrated Session",
    "bong": "Filtration Device"
}

def sanitize_text(text):
    """Replace restricted terms with medical pivot nomenclature"""
    for term, replacement in LEXICON.items():
        text = text.replace(term, replacement)
    return text

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
        # Launch browser (KEEP OPEN)
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("🔍 Logging in...")
        await page.goto(MEDUSA_URL)
        await page.fill('input[name="email"]', USERNAME)
        await page.fill('input[name="password"]', PASSWORD)
        await page.click('button[type="submit"]')
        await page.wait_for_url("https://medusadistribution.com/dashboard")
        print("✅ Login successful!")
        
        print("🔍 Navigating to Products...")
        await page.click('a[href="/products"]')
        await page.wait_for_selector(".product-list")
        print("✅ Products page loaded!")
        
        print("🔍 Filtering for in-stock items...")
        await page.click('button:has-text("Filters")')
        await page.click('input[type="checkbox"][value="in_stock"]')
        await page.click('button:has-text("Apply")')
        await page.wait_for_timeout(3000)  # Extra wait for filter
        print("✅ Filter applied!")
        
        # Extract product data
        products = []
        rows = await page.query_selector_all(".product-list tbody tr")
        print(f"📊 Found {len(rows)} in-stock products!")
        
        async with aiohttp.ClientSession() as session:
            for i, row in enumerate(rows):
                try:
                    print(f"🔍 Processing product {i+1}/{len(rows)}...")
                    
                    # Basic info
                    sku = await row.query_selector("td:nth-child(1)")
                    name = await row.query_selector("td:nth-child(2)")
                    brand = await row.query_selector("td:nth-child(3)")
                    price = await row.query_selector("td:nth-child(5)")
                    msrp = await row.query_selector("td:nth-child(6)")
                    stock = await row.query_selector("td:nth-child(7)")
                    image = await row.query_selector("img")
                    
                    # Click product to get details (WAIT FOR DETAILS TO LOAD)
                    await row.click()
                    await page.wait_for_selector(".product-detail", timeout=10000)
                    print("✅ Product details loaded!")
                    
                    # Extract details (sanitized)
                    description = sanitize_text(await (await page.query_selector(".product-detail .description")).inner_text())
                    benefits = sanitize_text(await (await page.query_selector(".product-detail .benefits")).inner_text())
                    usage = sanitize_text(await (await page.query_selector(".product-detail .usage")).inner_text())
                    
                    # Specs (sanitized)
                    specs = {}
                    spec_elements = await page.query_selector_all(".product-detail .spec")
                    for spec in spec_elements:
                        key = sanitize_text(await (await spec.query_selector(".spec-key")).inner_text())
                        value = sanitize_text(await (await spec.query_selector(".spec-value")).inner_text())
                        specs[key] = value
                    
                    # Image gallery
                    image_gallery = []
                    gallery_elements = await page.query_selector_all(".product-detail .image-gallery img")
                    for img in gallery_elements:
                        img_url = await img.get_attribute("src")
                        if img_url:
                            img_filename = os.path.basename(img_url)
                            downloaded_img = await download_image(session, img_url, f"{sku}_{img_filename}")
                            if downloaded_img:
                                image_gallery.append(downloaded_img)
                    
                    # Clean data
                    sku = await sku.inner_text() if sku else ""
                    name = sanitize_text(await name.inner_text()) if name else ""
                    brand = sanitize_text(await brand.inner_text()) if brand else ""
                    price = float((await price.inner_text()).replace("$", "").strip()) if price else 0
                    msrp = float((await msrp.inner_text()).replace("$", "").strip()) if msrp else 0
                    stock = int((await stock.inner_text()).strip()) if stock else 0
                    image_url = await image.get_attribute("src") if image else ""
                    
                    # Download main image
                    image_filename = ""
                    if image_url:
                        image_filename = await download_image(session, image_url, f"{sku}_main.jpg")
                    
                    if sku and name and price > 0:
                        products.append({
                            "sku": sku,
                            "name": name,
                            "brand": brand,
                            "price": price,
                            "msrp": msrp,
                            "stock": stock,
                            "image_filename": image_filename,
                            "image_gallery": image_gallery,
                            "description": description,
                            "benefits": benefits,
                            "usage": usage,
                            "specs": specs,
                            "is_sale": msrp > price,
                        })
                    
                    # Go back to product list
                    await page.go_back()
                    await page.wait_for_selector(".product-list")
                    
                except Exception as e:
                    print(f"⚠️ Error processing product {i+1}: {e}")
                    continue
        
        # Write to CSV
        with open(OUTPUT_CSV, mode='w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                "sku", "name", "brand", "price", "msrp", "stock", 
                "image_filename", "image_gallery", "description", "benefits", 
                "usage", "specs", "is_sale"
            ])
            for product in products:
                writer.writerow([
                    product["sku"],
                    product["name"],
                    product["brand"],
                    product["price"],
                    product["msrp"],
                    product["stock"],
                    product["image_filename"],
                    json.dumps(product["image_gallery"]),
                    product["description"],
                    product["benefits"],
                    product["usage"],
                    json.dumps(product["specs"]),
                    product["is_sale"]
                ])
        
        print(f"✅ Scraped {len(products)} products to {OUTPUT_CSV}")
        print("🎉 Scraping complete! You can now close the browser.")
        
        # Keep browser open until manually closed
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(scrape_medusa())