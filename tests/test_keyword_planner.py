import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.keyword_planner import KeywordPlanner

def main():
    print("=====================================")
    print("Keyword Planner Test")
    print("=====================================")
    
    planner = KeywordPlanner()
    
    product = {
        "nama": "SKINTIFIC Cover All Perfect Cushion High Coverage Poreless & Flawless Foundation 24H Long-lasting Make up",
        "kategori": "Beauty",
        "link_affiliate": "https://shope.ee/test"
    }
    
    res = planner.generate_search_keywords(product)
    
    success = True
    if res.get("success"):
        brand = planner.extract_brand(product)
        print(f"\nBrand\n{brand.upper()}")
        
        print(f"\nKeywords")
        for k in res["keywords"]:
            print(f"✔ {k}")
            
        print("\nSTATUS")
        print("SUCCESS")
    else:
        print("\nSTATUS")
        print("FAILED")
        print(f"Error: {res.get('error')}")
        success = False
        
    print("=====================================")

if __name__ == "__main__":
    main()
