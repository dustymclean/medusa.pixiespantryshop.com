"""
FINAL Medusa Scraper:
- Auto-login + scrape ALL in-stock products
- Extract: name, price, stock, images, descriptions, specs
- Save to medusa_products.json (React-ready)
"""
import asyncio
from playwright.async_api import async_playwright
import json
import os
import aiohttp
import aiofiles

# Credentials
MEDUSA_URL = "https://medusadistribution.com/login"
USERNAME = "admin@pixies-pantry.com"
PASSWORD = "PixiesPantry1!"

# Output
OUTPUT_DIR = os.path.expanduser("~/Desktop/medusa.pixiespantryshop.com")
OUTPUT_JSON = os.path.join(OUTPUT_DIR, "src/medusa_products.json")
IMAGE_DIR = os.path.join(OUTPUT_DIR, "public/images")

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
                return f"/images/{filename}"
    except Exception as e:
        print(f"⚠️ Failed to download image {url}: {e}")
    return ""

async def scrape_medusa():
    async with async_playwright() as p:
        # Launch browser (visible for debugging)
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("🔍 Logging in to Medusa Distribution...")
        await page.goto(MEDUSA_URL, timeout=60000)
        await page.fill('input[name="email"]', USERNAME)
        await page.fill('input[name="password"]', PASSWORD)
        await page.click('button[type="submit"]')
        await page.wait_for_url("https://medusadistribution.com/dashboard", timeout=60000)
        print("✅ Login successful!")
        
        print("🔍 Navigating to Products...")
        await page.click('a[href="/products"]')
        await page.wait_for_selector(".product-list", timeout=60000)
        print("✅ Products page loaded!")
        
        print("🔍 Filtering for in-stock items...")
        await page.click('button:has-text("Filters")')
        await page.click('input[type="checkbox"][value="in_stock"]')
        await page.click('button:has-text("Apply")')
        await page.wait_for_timeout(3000)
        print("✅ Filter applied!")
        
        # Extract ALL product data
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
                    category = await row.query_selector("td:nth-child(4)")
                    price = await row.query_selector("td:nth-child(5)")
                    msrp = await row.query_selector("td:nth-child(6)")
                    stock = await row.query_selector("td:nth-child(7)")
                    image = await row.query_selector("img")
                    
                    # Click product to get details
                    await row.click()
                    await page.wait_for_selector(".product-detail", timeout=30000)
                    
                    # Extract ALL fields (sanitized)
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
                            img_filename = f"{sku}_{len(image_gallery)}.jpg"
                            downloaded_img = await download_image(session, img_url, img_filename)
                            if downloaded_img:
                                image_gallery.append(downloaded_img)
                    
                    # Clean data
                    sku = await sku.inner_text() if sku else f"prod_{i+1}"
                    name = sanitize_text(await name.inner_text()) if name else "Unnamed Product"
                    brand = sanitize_text(await brand.inner_text()) if brand else "Unknown Brand"
                    category = sanitize_text(await category.inner_text()) if category else "Uncategorized"
                    price = float((await price.inner_text()).replace("$", "").strip()) if price else 0
                    msrp = float((await msrp.inner_text()).replace("$", "").strip()) if msrp else 0
                    stock = int((await stock.inner_text()).strip()) if stock else 0
                    image_url = await image.get_attribute("src") if image else ""
                    
                    # Download main image
                    main_image = ""
                    if image_url:
                        main_image = await download_image(session, image_url, f"{sku}_main.jpg")
                    
                    # Determine badge
                    badge = ""
                    if stock == 0:
                        badge = "Sold Out"
                    elif stock < 5:
                        badge = "Low Stock"
                    elif msrp > price:
                        badge = "On Sale"
                    
                    if sku and name and price > 0:
                        products.append({
                            "id": sku,
                            "name": name,
                            "category": category,
                            "brand": brand,
                            "price": price,
                            "msrp": msrp,
                            "inStock": stock,
                            "badge": badge,
                            "description": description,
                            "benefits": benefits,
                            "usage": usage,
                            "specs": specs,
                            "imageUrl": main_image,
                            "imageGallery": image_gallery
                        })
                    
                    # Go back to product list
                    await page.go_back()
                    await page.wait_for_selector(".product-list")
                    
                except Exception as e:
                    print(f"⚠️ Error processing product {i+1}: {e}")
                    continue
        
        # Save to JSON
        with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2)
        
        print(f"✅ Scraped {len(products)} products to {OUTPUT_JSON}")
        print("🎉 Scraping complete! You can now close the browser.")
        
        # Keep browser open until manually closed
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(scrape_medusa())