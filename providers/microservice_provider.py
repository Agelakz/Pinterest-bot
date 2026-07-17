import logging
import os
import requests
from typing import List, Dict, Any
from requests.exceptions import RequestException

from providers.base_provider import SearchProvider, TiktokVideoCandidate

logger = logging.getLogger(__name__)

class MicroserviceProvider(SearchProvider):
    """
    Search provider that acts as a thin HTTP client to tiktok-downloader-pro microservice.
    Does not implement TikWM logic directly; merely fetches and normalizes the JSON response.
    """
    def __init__(self):
        # Default fallback to 9002 assuming Next.js runs there.
        self.base_url = os.environ.get("TIKTOK_SEARCH_API_URL", "http://localhost:3000")
        self.timeout = 15.0

    def search_videos(self, keyword: str) -> List[TiktokVideoCandidate]:
        logger.info(f"Calling Search Service at {self.base_url} for '{keyword}'")
        
        endpoint = f"{self.base_url.rstrip('/')}/api/search"
        params = {"q": keyword}
        
        try:
            resp = requests.get(endpoint, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
        except RequestException as e:
            logger.error(f"HTTP request to Search Service failed: {e}")
            raise Exception(f"Microservice HTTP error: {str(e)}")
        except ValueError as e:
            logger.error("Failed to parse JSON response from Search Service.")
            raise Exception("Invalid JSON response from Search Service")

        if not data.get("success"):
            error_msg = data.get("error", "Unknown microservice error")
            logger.warning(f"Search Service returned business error: {error_msg}")
            raise Exception(f"Microservice error: {error_msg}")

        results = data.get("data", [])
        if not results:
            logger.info("Search Service returned empty data.")
            return []

        candidates = []
        for item in results:
            try:
                # Normalisasi dari TiktokSearchResultItem -> TiktokVideoCandidate
                # Note: `item["durationFormatted"]` usually "0:15". We parse to int if possible.
                duration_str = item.get("durationFormatted", "0:0")
                duration_secs = 15
                if ":" in duration_str:
                    parts = duration_str.split(":")
                    if len(parts) == 2 and parts[1].isdigit():
                        duration_secs = int(parts[1])
                
                video_url = item.get("url", "")
                
                candidate = TiktokVideoCandidate(
                    id=item.get("id", ""),
                    title=item.get("title", ""),
                    author=item.get("author", {}).get("username", "").replace("@", ""),
                    duration=duration_secs,
                    thumbnail=item.get("coverUrl", ""),
                    video_url=video_url
                )
                candidates.append(candidate)
            except Exception as e:
                logger.warning(f"Failed to normalize an item from Search Service: {e}")
                continue
                
        logger.info(f"Candidates received: {len(candidates)}")
        return candidates