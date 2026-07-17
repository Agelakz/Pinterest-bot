import json
import logging
from dataclasses import dataclass
from typing import Optional
from curl_cffi import requests

logger = logging.getLogger(__name__)


@dataclass
class BoardCreateResult:
    success: bool
    board_id: Optional[str]
    board_name: str


class BoardCreator:
    """
    Board Creator.
    Responsible for creating new Pinterest boards via POST /resource/BoardResource/create/.
    Strictly mimics Pinterest Web Builder HAR behavior.
    """

    def __init__(self, session: requests.Session, csrftoken: str):
        self.session = session
        self.csrftoken = csrftoken

    def create(self, name: str) -> BoardCreateResult:
        url = "https://id.pinterest.com/resource/BoardResource/create/"

        payload_data = {
            "options": {
                "name": name,
                "description": "",
                "privacy": "public",
                "collab_board_email": True,
                "aux_data": {
                    "source": "board_picker"
                }
            },
            "context": {}
        }

        form_data = {
            "source_url": "/pin-creation-tool/",
            "data": json.dumps(payload_data, separators=(',', ':'))
        }

        headers = {
            "X-CSRFToken": self.csrftoken,
            "X-Pinterest-AppState": "active",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": "https://id.pinterest.com/pin-creation-tool/"
        }

        try:
            response = self.session.post(url, data=form_data, headers=headers)

            if response.status_code != 200:
                logger.error("[FORENSIC] Board Create Failed")
                logger.error(f"  URL: {url}")
                logger.error(f"  HTTP Status: {response.status_code}")
                logger.error(f"  Request Payload: {form_data}")
                logger.error(f"  Response Headers: {dict(response.headers)}")
                logger.error(f"  Response Body (raw): {response.text}")

                try:
                    res_json = response.json()
                    logger.error(f"  Response JSON: {json.dumps(res_json, indent=2)}")
                    if "resource_response" in res_json:
                        logger.error(f"  resource_response: {res_json.get('resource_response')}")
                    if "code" in res_json:
                        logger.error(f"  code: {res_json.get('code')}")
                    if "message" in res_json:
                        logger.error(f"  message: {res_json.get('message')}")
                    if "error" in res_json:
                        logger.error(f"  error: {res_json.get('error')}")
                except Exception:
                    logger.error("  Response is not valid JSON")

                return BoardCreateResult(success=False, board_id=None, board_name=name)

            res_json = response.json()
            data = res_json.get("resource_response", {}).get("data", {})
            board_id = data.get("id")
            board_name = data.get("name", name)

            if board_id:
                logger.info(f"Created board: {board_name} ({board_id})")
                return BoardCreateResult(success=True, board_id=board_id, board_name=board_name)
            else:
                logger.error(f"Failed creating board: {name} (No ID in response)")
                return BoardCreateResult(success=False, board_id=None, board_name=name)

        except Exception as e:
            logger.error(f"Error creating board {name}: {e}")
            return BoardCreateResult(success=False, board_id=None, board_name=name)