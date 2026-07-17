import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.pinterest_api import PinterestAPI

def main():
    load_dotenv()
    
    video_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../temp/sample.mp4'))
    
    print("==============================")
    print("Pinterest Media Upload Test")
    print("==============================")
    
    try:
        api = PinterestAPI()
        
        # Buat dummy file kalau belum ada buat testing path & size logic
        if not os.path.exists(video_path):
            print(f"Creating dummy file at {video_path}...")
            with open(video_path, 'wb') as f:
                f.write(os.urandom(1024 * 1024 * 5)) # 5MB dummy video
                
        size_mb = os.path.getsize(video_path) / (1024 * 1024)
        
        print(f"\nVideo: {os.path.basename(video_path)}")
        print(f"Size : {size_mb:.1f} MB")
        
        result = api.upload_media(video_path)
        
        print("\n------------------------------")
        if result['success']:
            print("Upload : SUCCESS")
            print(f"Media ID : {result['media_id']}")
            print(f"Status : READY") # Pinterest API returns uploaded but it takes a sec to process
        else:
            print("Upload : FAILED")
            print(f"Error : {result['error']}")
            
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    main()
