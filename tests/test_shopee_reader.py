import os
import sys
import logging
from pathlib import Path

# Setup logging for the test output
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.shopee_reader import ShopeeReader

def main():
    print("========================================")
    print("Shopee Reader Test")
    print("========================================")
    
    json_path = Path(__file__).parent.parent / "data" / "shopee_products.json"
    reader = ShopeeReader(json_path)
    
    # 1. Load Products
    res_load = reader.load_products()
    if not res_load["success"]:
        print(f"\nFAILED to load: {res_load['error']}")
        sys.exit(1)
        
    print(f"\nProducts Loaded : {len(res_load['data'])}")
    
    # 2. Random Product
    res_random = reader.get_random_product()
    print("\nRandom Product :")
    if res_random["success"]:
        print(res_random["data"]["nama"])
    else:
        print(f"FAILED: {res_random['error']}")

    # 3. Category Search
    cat_query = "Beauty"
    res_cat = reader.get_by_category(cat_query)
    print(f"\nCategory Search :\n{cat_query}")
    if res_cat["success"]:
        print(f"Result : {len(res_cat['data'])} products")
    else:
        print(f"FAILED: {res_cat['error']}")
        
    # 4. Keyword Search
    kw_query = "cushion"
    res_kw = reader.find_by_keyword(kw_query)
    print(f"\nKeyword Search :\n\"{kw_query.capitalize()}\"")
    if res_kw["success"]:
        print(f"Result : {len(res_kw['data'])} products")
    else:
        print(f"FAILED: {res_kw['error']}")
        
    print("\nSTATUS :")
    print("SUCCESS")
    print("========================================")

if __name__ == "__main__":
    main()
