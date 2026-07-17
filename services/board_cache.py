import json
import logging
import urllib.parse
import time
from typing import Dict, Any, List, Optional
from curl_cffi import requests

logger = logging.getLogger(__name__)


class BoardCache:
    """
    Board Cache Memory.
    Mirrors Pinterest Web Builder behavior where all boards are loaded once
    and search is performed locally in-memory.
    No Board Creation, strictly Read-Only caching.
    """

    def __init__(self, session: requests.Session, csrftoken: str):
        """
        Requires an authenticated curl_cffi session and csrftoken.
        """
        self.session = session
        self.csrftoken = csrftoken
        self.boards: List[Dict[str, Any]] = []

    def refresh(self) -> bool:
        """
        Fetches all boards from Pinterest BoardPickerBoardsResource 
        and updates the in-memory cache.
        """
        logger.info("Loading Pinterest Boards...")

        # Endpoint based on pinpapantest.har
        url = "https://id.pinterest.com/resource/BoardPickerBoardsResource/get/"

        payload_data = {
            "options": {
                "field_set_key": "board_picker",
                "filter": "all"
            },
            "context": {}
        }

        query_params = {
            "source_url": "/pin-creation-tool/",
            "data": json.dumps(payload_data, separators=(',', ':')),
            "_": str(int(time.time() * 1000))
        }

        headers = {
            # Pinterest-specific headers (do not change)
            "X-Pinterest-AppState": "active",
            "X-Requested-With": "XMLHttpRequest",
            "X-Pinterest-Source-Url": "/pin-creation-tool/",
            "X-CSRFToken": self.csrftoken or "",

            # Browser fingerprint alignment (from HAR)
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Origin": "https://id.pinterest.com",
            "Referer": "https://id.pinterest.com/pin-creation-tool/",
            "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "priority": "u=1, i"
        }

        try:
            req_url = f"{url}?{urllib.parse.urlencode(query_params)}"
            logger.info(f"BoardPicker URL: {req_url[:120]}...")
            logger.info(f"Cookie count sent: {len(self.session.cookies)}")

            response = self.session.get(req_url, headers=headers)

            logger.info(f"BoardPicker HTTP Status: {response.status_code}")

            if response.status_code != 200:
                logger.error(f"Failed to fetch boards. HTTP {response.status_code}")
                logger.debug(f"Response headers: {dict(response.headers)}")
                logger.debug(f"Response body: {response.text[:500]}")
                return False

            res_json = response.json()
            resource_data = res_json.get("resource_response", {}).get("data", {})
            self.boards = resource_data.get("all_boards", [])

            logger.info(f"Total Boards: {len(self.boards)}")
            return True

        except Exception as e:
            logger.error(f"Error fetching boards: {e}")
            return False

    def get_all(self) -> List[Dict[str, Any]]:
        """Return the internal memory list of board objects."""
        return self.boards

    def find_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Performs a local exact match search (case-insensitive).
        Mimics React local filtering.
        """
        target = name.strip().lower()
        for board in self.boards:
            board_name = board.get("name", "").strip().lower()
            if board_name == target:
                return board

        return None