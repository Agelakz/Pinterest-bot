#!/usr/bin/env python3
"""
Isolated Runtime Validation: Create Board → Immediate Publish
Strictly uses existing BoardCreator + PinterestAPI.
Does not modify any production code.
"""

import os
import sys
import json
import logging
from datetime import datetime
from curl_cffi import requests
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from services.board_creator import BoardCreator
from services.pinterest_api import PinterestAPI
from services.pinterest_seo import PinterestSEOEngine

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


def load_cookies(cookies_file: str = "cookies.json"):
    """Load curl_cffi session exactly like PinterestAPI."""
    session = requests.Session(impersonate="chrome110")

    if not os.path.exists(cookies_file):
        raise FileNotFoundError(f"Cookies file not found: {cookies_file}")

    with open(cookies_file, 'r') as f:
        cookies_data = json.load(f)

    if isinstance(cookies_data, list):
        for cookie in cookies_data:
            session.cookies.set(
                cookie['name'],
                cookie['value'],
                domain=cookie.get('domain', '.pinterest.com')
            )
    elif isinstance(cookies_data, dict):
        for name, value in cookies_data.items():
            session.cookies.set(name, value, domain=".pinterest.com")

    csrftoken = None
    for cookie in session.cookies.jar:
        if cookie.name == "csrftoken":
            csrftoken = cookie.value
            break

    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
        "X-Requested-With": "XMLHttpRequest",
        "X-Pinterest-AppState": "active",
        "X-CSRFToken": csrftoken or "",
        "Origin": "https://id.pinterest.com",
        "Referer": "https://id.pinterest.com/pin-creation-tool/"
    })

    return session, csrftoken


def main():
    print("=" * 60)
    print("CREATE → IMMEDIATE PUBLISH VALIDATION")
    print("=" * 60)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    board_name = f"CreatePublishTest {timestamp}"

    try:
        # 1. Load session
        session, csrftoken = load_cookies("cookies.json")

        # 2. Load first product
        products = json.loads(Path("data/shopee_products.json").read_text())
        product = products[0]

        # 3. Generate SEO
        seo_engine = PinterestSEOEngine()
        seo_res = seo_engine.generate_metadata(product)
        if not seo_res.get("success"):
            print(f"SEO generation failed: {seo_res.get('error')}")
            return
        seo = seo_res["data"]

        # 4. Create new board (BoardCreator only)
        creator = BoardCreator(session=session, csrftoken=csrftoken)
        create_result = creator.create(board_name)

        if not create_result.success:
            print(f"Board creation failed: {create_result}")
            return

        new_board_id = create_result.board_id
        print(f"\nCreated Board ID:   {new_board_id}")
        print(f"Created Board Name: {create_result.board_name}")

        # 5. Initialize PinterestAPI (reuses same session)
        pinterest = PinterestAPI()
        pinterest.session = session
        pinterest.csrftoken = csrftoken

        # 6. Upload media (use a small test video if available, otherwise skip)
        # For this validation we assume a media file exists or use existing logic
        # In real run, we would call download first. For isolation, we print placeholder.
        print("\n[INFO] Skipping actual download for isolation test.")
        print("[INFO] Using dummy media_info for create_pin validation...")

        # 7. Publish using the NEWLY created board_id
        # Note: In real execution this would use real media_info from upload_media()
        # Here we only validate that board_id flows correctly into create_pin
        try:
            # This is the critical test: passing newly created board_id directly
            pin_res = pinterest.create_pin(
                media_info={"media_id": "DUMMY_FOR_VALIDATION"},
                title=seo["title"][:100],
                description=seo["description"],
                board_id=new_board_id,
                destination_url=seo["destination_url"]
            )

            if pin_res.get("success"):
                print("\n" + "=" * 60)
                print("CREATE → PUBLISH SUCCESS")
                print("=" * 60)
                print(f"Board ID:     {new_board_id}")
                print(f"Board Name:   {create_result.board_name}")
                print(f"Pin ID:       {pin_res.get('pin_id', 'N/A')}")
                print(f"Pin URL:      {pin_res.get('url', 'N/A')}")
                print("=" * 60)
            else:
                print(f"\nPublish failed: {pin_res}")

        except Exception as publish_err:
            print("\n" + "=" * 60)
            print("PUBLISH FAILURE REPORT")
            print("=" * 60)
            print(f"Exception: {type(publish_err).__name__}: {publish_err}")
            import traceback
            traceback.print_exc()

    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()