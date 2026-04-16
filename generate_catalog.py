"""
Generate the Medusa storefront catalog CSV from the Dyspensr Master Catalog.
Includes badge logic (Pixie's Pick, On Sale, Featured) and product data.
"""
import csv
import os
import sys

# Add the Pixies_Vape_Shop directory to the path so we can import dashboard_config
sys.path.append(os.path.expanduser("~/Desktop/Pixies_Vape_Shop"))
from dashboard_config import get_product_badges, is_pick, is_on_sale, is_featured

# Paths
INPUT_CSV = os.path.expanduser("~/Desktop/Dyspensr_Master_Catalog_Priced.csv")
OUTPUT_DIR = os.path.expanduser("~/Desktop/medusa.pixiespantryshop.com/data")
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "medusa_products_advanced.csv")

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def clean_price(price_str):
    """Clean and convert price string to float"""
    if not price_str or str(price_str).strip() == "":
        return 0.0
    try:
        return float(str(price_str).replace("$", "").strip())
    except ValueError:
        return 0.0

def transform_catalog():
    """Transform the Dyspensr catalog into the Medusa frontend format"""
    products = []
    
    with open(INPUT_CSV, mode='r', encoding='utf-8') as file:
        # Read the entire file as a list of rows
        rows = list(csv.reader(file))
        if not rows:
            print("⚠️ No rows found in the input CSV.")
            return
            
        # Extract header and data rows
        header = rows[0]
        data_rows = rows[1:]
        
        # Debug: Print header and first row
        print("🔍 Header:", header)
        print("🔍 First row:", data_rows[0] if data_rows else "No data rows")
        
        # Find the index of the "SKU" column
        try:
            sku_index = header.index("SKU")
        except ValueError:
            print("⚠️ 'SKU' column not found in the CSV header.")
            return
            
        # Find other relevant columns
        brand_index = header.index("Brand") if "Brand" in header else None
        name_index = header.index("Product Name") if "Product Name" in header else None
        clean_name_index = header.index("Clean Product Name") if "Clean Product Name" in header else name_index
        price_index = header.index("Your Online Price") if "Your Online Price" in header else None
        retail_price_index = header.index("Your Retail Price") if "Your Retail Price" in header else None
        stock_index = header.index("Inventory Class") if "Inventory Class" in header else None
        image_index = header.index("Image URL") if "Image URL" in header else None
        status_index = header.index("Status") if "Status" in header else None
        
        print(f"🔍 Column indices - SKU: {sku_index}, Brand: {brand_index}, Name: {name_index}, Price: {price_index}, Image: {image_index}")
        
        for row in data_rows:
            sku = row[sku_index].strip() if sku_index < len(row) else ""
            if not sku:
                continue
                
            # Skip Toker Poker products (they have their own store)
            brand = row[brand_index].strip() if brand_index and brand_index < len(row) else ""
            if brand.lower() == "toker poker":
                continue
                
            # Skip inactive products
            status = row[status_index].strip().lower() if status_index and status_index < len(row) else "active"
            if status in ["hidden", "inactive", ""]:
                continue
                
            # Clean data
            name = row[name_index].strip() if name_index and name_index < len(row) else ""
            clean_name = row[clean_name_index].strip() if clean_name_index and clean_name_index < len(row) else name
            # Use "Your Online Price" (index 18) as the primary price source, fall back to "Your Retail Price" (index 17)
            price = clean_price(row[18]) if len(row) > 18 and row[18].strip() else clean_price(row[17]) if len(row) > 17 and row[17].strip() else 0
            # Use "Inventory Class" (index 13) as stock
            stock = int(row[13].strip()) if len(row) > 13 and row[13].strip() else 0
            image_url = row[image_index].strip() if image_index and image_index < len(row) else ""
            
            # Skip if no image, price, or stock
            if not image_url:
                print(f"⚠️ Skipping {sku}: No image URL")
                continue
            if price <= 0:
                print(f"⚠️ Skipping {sku}: Invalid price ({price})")
                continue
            if stock <= 0:
                print(f"⚠️ Skipping {sku}: Out of stock")
                continue
                
            # Extract image filename
            image_filename = os.path.basename(image_url)
            
            # Get badges
            badges = get_product_badges(sku)
            badge_types = [badge["type"] for badge in badges]
            
            # Add to products
            products.append({
                "brand": brand,
                "name": clean_name,
                "sku": sku,
                "price": price,
                "stock": stock,
                "image_filename": image_filename,
                "is_pick": "pick" in badge_types,
                "is_sale": "sale" in badge_types,
                "is_featured": "featured" in badge_types
            })
    
    # Write to CSV
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
    
    print(f"✅ Catalog generated: {len(products)} products written to {OUTPUT_CSV}")

if __name__ == "__main__":
    transform_catalog()