import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.search_orchestrator import SearchOrchestrator

# Mocking TikTokBackendClient to simulate a search endpoint that returns lists of candidates
class MockTikTokClient:
    def search(self, keyword):
        # Return dummy candidates. We intentionally create duplicates across different keywords
        return {
            "success": True,
            "data": [
                {"videoId": "1001", "url": "http://vid1", "filename": "v1.mp4", "title": f"Test {keyword} 1"},
                {"videoId": "1002", "url": "http://vid2", "filename": "v2.mp4", "title": f"Test {keyword} 2"},
                {"videoId": "1001", "url": "http://vid1", "filename": "v1.mp4", "title": f"Duplicate"} # Duplicate id
            ]
        }
        
    def normalize_response(self, raw_item):
        return {
            "success": True, 
            "data": {
                "video": {
                    "id": raw_item.get("videoId"),
                    "title": raw_item.get("title", ""),
                    "author": "mock_author",
                    "duration": 10,
                    "thumbnail": "mock_thumb.jpg",
                    "download_url": raw_item.get("url"),
                    "filename": raw_item.get("filename"),
                    "codec": "mock",
                    "resolution": "1080",
                    "watermark": False
                }
            }
        }

def main():
    load_dotenv()
    
    print("===================================")
    print("Search Orchestrator Test")
    print("===================================")
    
    base_dir = Path(__file__).parent.parent
    data_path = base_dir / "data" / "shopee_products.json"
    
    orchestrator = SearchOrchestrator(data_path)
    # Inject Mock
    orchestrator.tiktok_client = MockTikTokClient()
    
    res = orchestrator.run()
    
    success = True
    if res.get("success"):
        prod_name = res["product"]["nama"]
        if len(prod_name) > 30:
            prod_name = prod_name[:27] + "..."
            
        print("\nProduct")
        print(prod_name)
        
        print("\nKeywords")
        print(len(res["keywords"]))
        
        # In our mock, each keyword returns 3 items
        total_raw = len(res["keywords"]) * 3
        print("\nVideos Found")
        print(total_raw)
        
        print("\nAfter Dedup")
        print(len(res["videos"]))
        
        print("\nSTATUS")
        print("SUCCESS")
    else:
        print("\nSTATUS")
        print("FAILED")
        print(res.get("error"))
        success = False
        
    print("===================================")

if __name__ == "__main__":
    main()
