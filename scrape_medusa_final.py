"""
FINAL Medusa Distribution Scraper:
- Auto-login with credentials
- Scrape ONLY in-stock items
- Medical pivot nomenclature (no CBD/THC/hemp)
- Downloads all images
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
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "data/medusa_products_final.csv")
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
        # Launch browser
        browser = await p.chromium.launch(headless=False)  # Run visible for debugging
        page = await browser.new_page()
        
        # Auto-login
        await page.goto(MEDUSA_URL)
        await page.fill('input[name="email"]', USERNAME)
        await page.fill('input[name="password"]', PASSWORD)
        await page.click('button[type="submit"]')
        await page.wait_for_url("https://medusadistribution.com/dashboard")
        print("✅ Auto-logged in to Medusa Distribution")
        
        # Navigate to products
        await page.click('a[href="/products"]')
        await page.wait_for_selector(".product-list")
        print("✅ Navigated to Products")
        
        # Filter for in-stock products ONLY
        await page.click('button:has-text("Filters")')
        await page.click('input[type="checkbox"][value="in_stock"]')
        await page.click('button:has-text("Apply")')
        await page.wait_for_timeout(2000)
        print("✅ Filtered for IN-STOCK products only")
        
        # Extract ALL product data
        products = []
        rows = await page.query_selector_all(".product-list tbody tr")
        
        async with aiohttp.ClientSession() as session:
            for row in rows:
                try:
                    # Basic info
                    sku = await row.query_selector("td:nth-child(1)")
                    name = await row.query_selector("td:nth-child(2)")
                    brand = await row.query_selector("td:nth-child(3)")
                    category = await row.query_selector("td:nth-child(4)")
                    price = await row.query_selector("td:nth-child(5)")
                    msrp = await row.query_selector("td:nth-child(6)")
                    stock = await row.query_selector("td:nth-child(7)")
                    image = await row.query_selector("img")
                    
                    # Click product to get FULL details
                    await row.click()
                    await page.wait_for_selector(".product-detail")
                    
                    # Extract ALL fields (sanitized)
                    description = sanitize_text(await (await page.query_selector(".product-detail .description")).inner_text())
                    benefits = sanitize_text(await (await page.query_selector(".product-detail .benefits")).inner_text())
                    usage = sanitize_text(await (await page.query_selector(".product-detail .usage")).inner_text())
                    ingredients = sanitize_text(await (await page.query_selector(".product-detail .ingredients")).inner_text())
                    lab_results = sanitize_text(await (await page.query_selector(".product-detail .lab-results")).inner_text())
                    
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
                    
                    # Cross-sell products
                    cross_sells = []
                    cross_sell_elements = await page.query_selector_all(".product-detail .cross-sell a")
                    for cs in cross_sell_elements:
                        cs_sku = await cs.get_attribute("data-sku")
                        cs_name = sanitize_text(await cs.inner_text())
                        if cs_sku:
                            cross_sells.append({"sku": cs_sku, "name": cs_name})
                    
                    # Badges (Pixie's Pick, On Sale, Featured)
                    badges = []
                    if await page.query_selector(".badge-pick"):
                        badges.append("Pixie's Pick")
                    if await page.query_selector(".badge-sale"):
                        badges.append("On Sale")
                    if await page.query_selector(".badge-featured"):
                        badges.append("Featured")
                    
                    # Clean data
                    sku = await sku.inner_text() if sku else ""
                    name = sanitize_text(await name.inner_text()) if name else ""
                    brand = sanitize_text(await brand.inner_text()) if brand else ""
                    category = sanitize_text(await category.inner_text()) if category else ""
                    price = float((await price.inner_text()).replace("$", "").strip()) if price else 0
                    msrp = float((await msrp.inner_text()).replace("$", "").strip()) if msrp else 0
                    stock = int((await stock.inner_text()).strip()) if stock else 0
                    image_url = await image.get_attribute("src") if image else ""
                    
                    # Download main image
                    image_filename = ""
                    if image_url:
                        image_filename = await download_image(session, image_url, f"{sku}_main.jpg")
                    
                    if sku and name and price > 0 and stock > 0:
                        products.append({
                            "sku": sku,
                            "name": name,
                            "brand": brand,
                            "category": category,
                            "price": price,
                            "msrp": msrp,
                            "stock": stock,
                            "image_filename": image_filename,
                            "image_gallery": image_gallery,
                            "description": description,
                            "benefits": benefits,
                            "usage": usage,
                            "ingredients": ingredients,
                            "lab_results": lab_results,
                            "specs": specs,
                            "cross_sells": cross_sells,
                            "badges": badges,
                            "is_pick": "Pixie's Pick" in badges,
                            "is_sale": "On Sale" in badges,
                            "is_featured": "Featured" in badges
                        })
                    
                    # Go back to product list
                    await page.go_back()
                    await page.wait_for_selector(".product-list")
                    
                except Exception as e:
                    print(f"⚠️ Error parsing row: {e}")
                    continue
        
        # Write to CSV
        with open(OUTPUT_CSV, mode='w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                "sku", "name", "brand", "category", "price", "msrp", "stock", 
                "image_filename", "image_gallery", "description", "benefits", 
                "usage", "ingredients", "lab_results", "specs", "cross_sells", 
                "badges", "is_pick", "is_sale", "is_featured"
            ])
            for product in products:
                writer.writerow([
                    product["sku"],
                    product["name"],
                    product["brand"],
                    product["category"],
                    product["price"],
                    product["msrp"],
                    product["stock"],
                    product["image_filename"],
                    json.dumps(product["image_gallery"]),
                    product["description"],
                    product["benefits"],
                    product["usage"],
                    product["ingredients"],
                    product["lab_results"],
                    json.dumps(product["specs"]),
                    json.dumps(product["cross_sells"]),
                    ",".join(product["badges"]),
                    product["is_pick"],
                    product["is_sale"],
                    product["is_featured"]
                ])
        
        print(f"✅ Scraped {len(products)} IN-STOCK products to {OUTPUT_CSV}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_medusa())