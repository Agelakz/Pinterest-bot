#!/usr/bin/env python3
"""
Isolated Runtime Validation for BoardCreator
Strictly uses existing BoardCreator implementation.
Does not modify any production code.
"""

import os
import sys
import json
import logging
from datetime import datetime
from curl_cffi import requests

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from services.board_creator import BoardCreator

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


def load_session_and_csrftoken(cookies_file: str = "cookies.json"):
    """Load session and csrftoken exactly like PinterestAPI does."""
    session = requests.Session(impersonate="chrome110")

    if not os.path.exists(cookies_file):
        raise FileNotFoundError(f"Cookies file not found: {cookies_file}")

    try:
        if cookies_file.endswith('.txt'):
            # Netscape format (simplified)
            with open(cookies_file, 'r') as f:
                for line in f:
                    if line.startswith('#') or not line.strip():
                        continue
                    parts = line.strip().split('\t')
                    if len(parts) >= 7:
                        domain, _, path, _, _, name, value = parts[:7]
                        session.cookies.set(name, value, domain=domain, path=path)
        else:
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
    except Exception as e:
        logger.error(f"Failed to load cookies: {e}")
        raise

    csrftoken = None
    for cookie in session.cookies.jar:
        if cookie.name == "csrftoken":
            csrftoken = cookie.value
            break

    if not csrftoken:
        logger.warning("csrftoken not found in cookies. POST may fail.")

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
    print("BOARD CREATE RUNTIME TEST")
    print("=" * 60)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    board_name = f"Runtime Validation {timestamp}"

    print(f"\nBoard Name: {board_name}")
    print("-" * 60)

    try:
        session, csrftoken = load_session_and_csrftoken("cookies.json")
        creator = BoardCreator(session=session, csrftoken=csrftoken)

        result = creator.create(board_name)

        print(f"Success:      {result.success}")
        print(f"Board ID:     {result.board_id}")
        print(f"Board Name:   {result.board_name}")
        print("-" * 60)

    except Exception as e:
        print(f"Success:      False")
        print(f"Exception:    {type(e).__name__}: {e}")
        print(f"Board ID:     None")
        print("-" * 60)
        import traceback
        traceback.print_exc()

    print("=" * 60)


if __name__ == "__main__":
    main()