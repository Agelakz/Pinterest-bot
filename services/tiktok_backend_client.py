import os
import logging
import httpx
from typing import Dict, Any

logger = logging.getLogger(__name__)

class TikTokBackendClient:
    """
    Client wrapper to interact with the local TikTok Backend service.
    Normalizes the Cobalt-style response to Pinterest automation standard.
    """

    def __init__(self, backend_url: str = None):
        self.backend_url = backend_url or os.getenv("COBALT_API_URL", "https://co.wuk.sh/api/json")
        self.client = httpx.Client(
            timeout=30.0,
            headers={"Accept": "application/json"}
        )

    def _format_success(self, data: Any) -> Dict[str, Any]:
        return {"success": True, "data": data}

    def _format_error(self, message: str) -> Dict[str, Any]:
        return {"success": False, "error": message, "data": None}

    def health_check(self) -> Dict[str, Any]:
        """Check if the backend is reachable."""
        logger.info("Connecting TikTok Backend")
        try:
            resp = self.client.get(self.backend_url)
            if resp.status_code in [200, 405]: # 405 is fine for GET on POST-only root endpoint, means it's alive
                logger.info("Backend Healthy")
                return self._format_success({"status": "healthy"})
            return self._format_error(f"Unexpected status code: {resp.status_code}")
        except Exception as e:
            logger.error(f"Backend offline: {e}")
            return self._format_error(f"Backend offline: {e}")

    def search(self, keyword: str) -> Dict[str, Any]:
        """
        Pass a search keyword to the backend.
        (Note: the provided Cobalt backend primarily expects direct video URLs, 
        but if a search feature exists on the backend, this passes it forward).
        """
        logger.info(f"Searching keyword: {keyword}")
        try:
            payload = {"url": keyword, "downloadMode": "search"} 
            resp = self.client.post(self.backend_url, json=payload)
            
            if resp.status_code != 200:
                return self._format_error(f"Search failed HTTP {resp.status_code}: {resp.text}")
                
            return self._format_success(resp.json())
        except Exception as e:
            return self._format_error(f"Search error: {e}")

    def download(self, video_url: str) -> Dict[str, Any]:
        """Fetch extraction metadata from backend for a specific video URL."""
        logger.info(f"Requesting download metadata for: {video_url}")
        try:
            payload = {"url": video_url}
            resp = self.client.post(self.backend_url, json=payload)
            
            if resp.status_code != 200:
                return self._format_error(f"Download metadata failed HTTP {resp.status_code}: {resp.text}")
            
            data = resp.json()
            if data.get("status") == "error":
                return self._format_error(f"Backend returned error: {data.get('error')}")
                
            logger.info("Download metadata received")
            return self._format_success(data)
        except Exception as e:
            return self._format_error(f"Download error: {e}")

    def normalize_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts the Cobalt-style dictionary into the standard 
        Pinterest pipeline format.
        """
        if not response:
            return self._format_error("Empty response to normalize")
            
        try:
            meta = response.get("metadata", {})
            
            # Use dictionary get with defaults
            normalized = {
                "id": response.get("videoId", ""),
                "title": response.get("title", ""),
                "author": response.get("author", ""),
                "duration": response.get("duration", 0),
                "thumbnail": response.get("thumbnail", ""),
                "download_url": response.get("url", ""),
                "filename": response.get("filename", "video.mp4"),
                "codec": meta.get("codec", "unknown"),
                "resolution": meta.get("resolution", "unknown"),
                "watermark": meta.get("watermark", False)
            }
            
            logger.info("Response normalized")
            return self._format_success({"video": normalized})
            
        except Exception as e:
            return self._format_error(f"Normalization failed: {e}")
