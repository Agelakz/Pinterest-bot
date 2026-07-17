import os
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.download_manager import DownloadManager

def main():
    print("==================================")
    print("Download Manager Test")
    print("==================================")
    
    # We use a reliable small public MP4 url for testing rather than 
    # hitting the proxy directly to isolate download manager logic.
    test_url = "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/Big_Buck_Bunny_360_10s_1MB.mp4"
    test_filename = "test_download.mp4"
    
    manager = DownloadManager()
    
    # Run test
    res = manager.download(test_url, test_filename)
    
    success = True
    if res.get("success"):
        print(f"\nDownload File")
        print(res["filename"])
        
        print("\nValidasi")
        print("SUCCESS")
        
        print("\nLokasi File")
        print(res["path"])
        
        print(f"\nUkuran")
        print(f"{res['size']} bytes")
    else:
        print("\nDownload FAILED")
        print(res.get('error'))
        success = False
        
    print("\nCleanup")
    cleanup_res = manager.cleanup()
    if cleanup_res["success"]:
        print(f"SUCCESS (Deleted {cleanup_res['data']['deleted_count']} files)")
    else:
        print("FAILED")
        success = False
        
    print("\nSTATUS")
    print("SUCCESS" if success else "FAILED")
    print("==================================")

if __name__ == "__main__":
    main()
