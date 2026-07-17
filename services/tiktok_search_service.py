import logging
import os
from typing import Dict, Any

from providers.base_provider import SearchProvider
from services.search_provider import ProviderFactory

logger = logging.getLogger(__name__)

class TiktokSearchService:
    """Service to orchestrate TikTok video searches.
    
    This service sits between the Orchestrator and the specific search provider.
    It handles validation, formatting, and exception containment.
    """

    def __init__(self, provider: SearchProvider = None):
        """Initialize with a specific search provider, or load from ENV if None.
        
        Args:
            provider: Optional explicit provider. If None, reads from SEARCH_PROVIDER env var.
        """
        if provider is None:
            # Gunakan environ untuk read langsung (karena MVP python-dotenv kdg ga dipanggil)
            provider_name = os.environ.get("SEARCH_PROVIDER", "microservice")
            self.provider = ProviderFactory.get_provider(provider_name)
        else:
            self.provider = provider

    def search(self, keyword: str) -> Dict[str, Any]:
        """Search for videos using the configured provider.
        
        Args:
            keyword: The search term.
            
        Returns:
            Dict containing success status and list of videos.
        """
        if not keyword or not keyword.strip():
            logger.warning("Empty keyword provided to search.")
            return {
                "success": False,
                "error": "Keyword cannot be empty.",
                "videos": []
            }

        logger.info(f"Initiating search for keyword: '{keyword}' using provider: {self.provider.__class__.__name__}")
        
        try:
            candidates = self.provider.search_videos(keyword)
            videos = [c.to_dict() for c in candidates]
            
            logger.info(f"Search successful. Found {len(videos)} videos for keyword: '{keyword}'")
            return {
                "success": True,
                "videos": videos
            }
            
        except Exception as e:
            logger.error(f"Search failed for keyword '{keyword}': {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "videos": []
            }