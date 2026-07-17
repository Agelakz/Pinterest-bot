import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.pinterest_api import PinterestAPI

def main():
    load_dotenv()
    
    # Nilai dummy dari mockup test case
    media_id = "1234567890123"
    board_id = "9876543210987"
    title = "Test Video"
    description = "Test deskripsi untuk otomatisasi Pin Video"
    destination_url = "https://example.com"
    
    print("==============================")
    print("Pinterest Create Pin Test")
    print("==============================")
    print("Media : READY")
    print("Board : Affiliate")
    print(f"Title : {title}")
    print(f"Destination : {destination_url}")
    print("------------------------------")
    
    try:
        api = PinterestAPI()
        # Eksekusi (akan HTTP Error kalau media_id atau board_id di atas ga riil, tapi logic tervalidasi)
        result = api.create_pin(
            media_id=media_id,
            title=title,
            description=description,
            board_id=board_id,
            destination_url=destination_url
        )
        
        if result['success']:
            print("Create Pin : SUCCESS")
            print(f"Pin ID : {result['pin_id']}")
            print(f"URL : {result['pin_url']}")
        else:
            print("Create Pin : FAILED")
            print(f"Error : {result['error']}")
            
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    main()
