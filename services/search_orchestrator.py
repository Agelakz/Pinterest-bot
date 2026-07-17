import logging
from pathlib import Path
from typing import Dict, Any, List

from services.shopee_reader import ShopeeReader
from services.keyword_planner import KeywordPlanner
from services.tiktok_search_service import TiktokSearchService

logger = logging.getLogger(__name__)

class SearchOrchestrator:
    """
    Search Orchestrator MVP.
    Gathers product data -> Generates keywords -> Searches TikTok backend for candidates.
    Only collects and deduplicates candidates. Does NOT select or download them.
    """

    def __init__(self, data_path: Path):
        self.data_path = data_path
        
        # Dependency Injection (Internalized for MVP)
        self.reader = ShopeeReader(self.data_path)
        self.keyword_planner = KeywordPlanner()
        self.search_service = TiktokSearchService()

    def _format_success(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {"success": True, **data}

    def _format_error(self, message: str) -> Dict[str, Any]:
        return {"success": False, "error": message, "data": None}

    def run(self) -> Dict[str, Any]:
        """Main flow to gather candidate videos for a random product."""
        
        # 1. Load Product
        logger.info("Loading product")
        load_res = self.reader.load_products()
        if not load_res.get("success"):
            return self._format_error(f"Failed to load products: {load_res.get('error')}")
            
        prod_res = self.reader.get_random_product()
        if not prod_res.get("success"):
            return self._format_error(f"Failed to get product: {prod_res.get('error')}")
        product = prod_res["data"]
        
        # 2. Generate Keywords
        kw_res = self.keyword_planner.generate_search_keywords(product)
        if not kw_res.get("success"):
            return self._format_error(f"Failed to generate keywords: {kw_res.get('error')}")
            
        keywords = kw_res["keywords"]
        logger.info(f"Generated {len(keywords)} keywords")
        
        if not keywords:
            return self._format_error("No keywords generated")

        # 3. Search Loop
        all_videos: List[Dict[str, Any]] = []
        
        for keyword in keywords:
            logger.info(f"Searching keyword: {keyword}")
            
            search_res = self.search_service.search(keyword)
            if not search_res.get("success"):
                logger.warning(f"Search failed for '{keyword}', skipping. Error: {search_res.get('error')}")
                continue
                
            raw_data = search_res.get("data", {})
            
            # Normalization logic to extract array of videos
            found_items = []
            if isinstance(raw_data, list):
                found_items = raw_data
            elif isinstance(raw_data, dict) and "videos" in raw_data:
                found_items = raw_data["videos"]
            elif isinstance(raw_data, dict) and "url" in raw_data:
                # Fallback: the backend returned a single direct video instead of a search list
                found_items = [raw_data]
                
            logger.info(f"Found {len(found_items)} videos for keyword")
            
            # Item already normalized by TiktokSearchService (TiktokVideoCandidate instances or dicts)
            for raw_item in found_items:
                # Handle dataclass or dictionary transparently
                if hasattr(raw_item, '__dict__'):
                    vid_dict = raw_item.__dict__
                else:
                    vid_dict = raw_item
                
                if vid_dict.get("id") or vid_dict.get("video_url"):
                    all_videos.append(vid_dict)

        if not all_videos:
            return self._format_error("All keywords failed or returned zero valid videos.")

        # 4. Deduplicate
        total_found = len(all_videos)
        seen = set()
        deduped = []
        
        for vid in all_videos:
            # Use ID first, fallback to URL
            uid = vid.get("id") or vid.get("download_url")
            
            if uid and uid not in seen:
                seen.add(uid)
                deduped.append(vid)

        # Limit to 50 candidates
        final_videos = deduped[:50]
        
        logger.info(f"Deduplicated to {len(final_videos)} videos")

        return self._format_success({
            "product": product,
            "keywords": keywords,
            "videos": final_videos
        })
