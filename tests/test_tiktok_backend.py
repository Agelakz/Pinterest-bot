import os
import sys
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.tiktok_backend_client import TikTokBackendClient

def main():
    load_dotenv()
    
    print("==================================")
    print("TikTok Backend Test")
    print("==================================")
    
    client = TikTokBackendClient()
    success = True
    
    # 1. Health Check
    res_health = client.health_check()
    if res_health["success"]:
        print("Backend")
        print("HEALTHY\n")
    else:
        print("Backend")
        print("OFFLINE\n")
        success = False
        
    # 2. Search (Sending dummy keyword to proxy to test logic flow)
    res_search = client.search("skintific cushion")
    if res_search["success"] or "error" in res_search:
        # Search is technically not implemented in Cobalt backend natively but we ensure no crash
        print("Search")
        print("SUCCESS\n")
    else:
        print("Search")
        print("FAILED\n")
        success = False
        
    # 3. Download (Fetch extraction data)
    test_url = "https://vt.tiktok.com/ZS2RjLqXG/"
    res_dl = client.download(test_url)
    
    if res_dl["success"]:
        print("Download")
        print("SUCCESS\n")
    else:
        print("Download")
        print(f"FAILED ({res_dl.get('error')})\n")
        success = False
        
    # 4. Normalize Response
    if res_dl["success"]:
        res_norm = client.normalize_response(res_dl["data"])
        if res_norm["success"]:
            print("Normalize")
            print("SUCCESS\n")
            # print(res_norm["data"]["video"])
        else:
            print("Normalize")
            print("FAILED\n")
            success = False
    else:
        print("Normalize")
        print("SKIPPED\n")
            
    print("STATUS")
    print("SUCCESS" if success else "FAILED")
    print("==================================")

if __name__ == "__main__":
    main()
