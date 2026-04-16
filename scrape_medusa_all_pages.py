"""
FIXED Medusa Scraper:
- Auto-detects login fields (no hardcoded selectors)
- Scrapes ALL pages (handles pagination)
- Saves to medusa_products.json
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
        
        print("🔍 Opening login page...")
        await page.goto(MEDUSA_URL, timeout=60000)
        print("✅ Page loaded!")
        
        # Auto-detect login fields
        email_field = await page.query_selector("input[type='email'], input[name*='email'], input[placeholder*='email']")
        password_field = await page.query_selector("input[type='password'], input[name*='password'], input[placeholder*='password']")
        login_button = await page.query_selector("button[type='submit'], button:has-text('login'), button:has-text('sign in')")
        
        if not email_field or not password_field or not login_button:
            print("❌ Could not find login fields. Taking screenshot...")
            await page.screenshot(path="debug_login_fields.png")
            print("📸 Screenshot saved to debug_login_fields.png")
            await browser.close()
            return
        
        print("🔍 Filling login form...")
        await email_field.fill(USERNAME)
        await password_field.fill(PASSWORD)
        await login_button.click()
        
        # Wait for dashboard
        try:
            await page.wait_for_url("**/dashboard", timeout=60000)
            print("✅ Login successful!")
        except Exception as e:
            print(f"❌ Login failed: {e}")
            await page.screenshot(path="debug_login_error.png")
            print("📸 Screenshot saved to debug_login_error.png")
            await browser.close()
            return
        
        print("🔍 Navigating to Products...")
        await page.click("a[href*='/products'], a:has-text('products'), a:has-text('inventory')")
        await page.wait_for_selector(".product-list, .inventory-list", timeout=60000)
        print("✅ Products page loaded!")
        
        # Scrape ALL pages
        products = []
        page_num = 1
        
        while True:
            print(f"📄 Scraping page {page_num}...")
            
            # Wait for products to load
            await page.wait_for_selector(".product-list tbody tr, .inventory-list tbody tr", timeout=30000)
            rows = await page.query_selector_all(".product-list tbody tr, .inventory-list tbody tr")
            
            if not rows:
                print("❌ No products found on this page. Stopping.")
                break
            
            print(f"📊 Found {len(rows)} products on page {page_num}.")
            
            async with aiohttp.ClientSession() as session:
                for i, row in enumerate(rows):
                    try:
                        print(f"🔍 Processing product {i+1}/{len(rows)} on page {page_num}...")
                        
                        # Basic info
                        sku = await row.query_selector("td:nth-child(1), div[data-sku]")
                        name = await row.query_selector("td:nth-child(2), div[data-name]")
                        brand = await row.query_selector("td:nth-child(3), div[data-brand]")
                        price = await row.query_selector("td:nth-child(4), div[data-price]")
                        stock = await row.query_selector("td:nth-child(5), div[data-stock]")
                        image = await row.query_selector("img")
                        
                        # Click product to get details
                        await row.click()
                        await page.wait_for_selector(".product-detail, .modal", timeout=30000)
                        
                        # Extract details (sanitized)
                        description = sanitize_text(await (await page.query_selector(".description, .product-info")).inner_text())
                        
                        # Specs (sanitized)
                        specs = {}
                        spec_elements = await page.query_selector_all(".spec, .attribute")
                        for spec in spec_elements:
                            key = sanitize_text(await spec.query_selector(".key, .label").inner_text())
                            value = sanitize_text(await spec.query_selector(".value, .data").inner_text())
                            specs[key] = value
                        
                        # Image gallery
                        image_gallery = []
                        gallery_elements = await page.query_selector_all(".image-gallery img, .thumbnails img")
                        for img in gallery_elements:
                            img_url = await img.get_attribute("src")
                            if img_url:
                                img_filename = f"{sku}_{len(image_gallery)}.jpg"
                                downloaded_img = await download_image(session, img_url, img_filename)
                                if downloaded_img:
                                    image_gallery.append(downloaded_img)
                        
                        # Clean data
                        sku = await sku.inner_text() if sku else f"prod_{page_num}_{i+1}"
                        name = sanitize_text(await name.inner_text()) if name else "Unnamed Product"
                        brand = sanitize_text(await brand.inner_text()) if brand else "Unknown Brand"
                        price = float((await price.inner_text()).replace("$", "").strip()) if price else 0
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
                        elif price < (specs.get("MSRP", price) or price):
                            badge = "On Sale"
                        
                        if sku and name and price > 0:
                            products.append({
                                "id": sku,
                                "name": name,
                                "brand": brand,
                                "price": price,
                                "inStock": stock,
                                "badge": badge,
                                "description": description,
                                "specs": specs,
                                "imageUrl": main_image,
                                "imageGallery": image_gallery
                            })
                        
                        # Go back to product list
                        await page.go_back()
                        await page.wait_for_selector(".product-list, .inventory-list")
                        
                    except Exception as e:
                        print(f"⚠️ Error processing product {i+1}: {e}")
                        continue
            
            # Try to go to next page
            next_button = await page.query_selector("a[rel='next'], button:has-text('next'), button:has-text('>')")
            if not next_button:
                print("✅ No more pages. Scraping complete!")
                break
            
            await next_button.click()
            await page.wait_for_timeout(3000)  # Wait for next page to load
            page_num += 1
        
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