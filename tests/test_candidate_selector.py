import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.candidate_selector import CandidateSelector

# Mocking SearchOrchestrator to feed deterministic candidate lists
class MockSearchOrchestrator:
    def run(self):
        return {
            "success": True,
            "product": {
                "nama": "SKINTIFIC Cover All Perfect Cushion",
                "kategori": "Beauty",
                "link_affiliate": "https://shopee.co.id/test"
            },
            "videos": [
                {
                    "id": "1", "title": "", "author": "john", "duration": 0, "thumbnail": "thumb1.jpg", 
                    "download_url": "http://vid1", "filename": "v1.mp4"
                }, # Bad: 0 duration, no title
                {
                    "id": "2", "title": "Review Cushion Korea", "author": "jane", "duration": 30, "thumbnail": "thumb2.jpg", 
                    "download_url": "http://vid2", "filename": "v2.mp4"
                }, # Good duration, relevance (cushion), title, author, thumb = 10+5+10+40+5+10+20 = 100
                {
                    "id": "3", "title": "Skincare Tips", "author": "doe", "duration": 90, "thumbnail": "thumb3.jpg", 
                    "download_url": "http://vid3", "filename": "v3.mp4"
                }, # No duration bonus, irrelevant = 10+5+10+0+5+10+0 = 40
                {
                    "id": "4", "title": "Makeup tutorial", "author": "", "duration": 45, "thumbnail": "", 
                    "download_url": "", "filename": ""
                }, # Invalid: no url/filename. Should be skipped.
            ]
        }


def main():
    load_dotenv()
    
    print("======================================")
    print("Candidate Selector Test")
    print("======================================")
    
    base_dir = Path(__file__).parent.parent
    data_path = base_dir / "data" / "shopee_products.json"
    
    selector = CandidateSelector(data_path)
    # Inject Mock
    selector.orchestrator = MockSearchOrchestrator()
    
    res = selector.run()
    
    success = True
    if res.get("success"):
        
        print("\nCandidates")
        print(res["candidate_count"])
        
        print("\nBest Score")
        print(res["selected_video"]["score"])
        
        print("\nSelected")
        print(res["selected_video"]["filename"])
        
        print("\nSTATUS")
        print("SUCCESS")
    else:
        print("\nSTATUS")
        print("FAILED")
        print(res.get("error"))
        success = False
        
    print("======================================")

if __name__ == "__main__":
    main()
