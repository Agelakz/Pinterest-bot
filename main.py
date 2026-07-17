import logging
import json
import os
from pathlib import Path
from typing import Dict, Any

from services.shopee_reader import ShopeeReader
from services.keyword_planner import KeywordPlanner
from services.tiktok_search_service import TiktokSearchService
from services.search_orchestrator import SearchOrchestrator
from services.candidate_selector import CandidateSelector
from services.tiktok_backend_client import TikTokBackendClient
from services.download_manager import DownloadManager
from services.ai_seo_engine import AISeoEngine
from services.pinterest_api import PinterestAPI
from services.category_intelligence import ProductClassifier
from services.board_cache import BoardCache
from services.board_resolver import BoardResolver
from services.board_creator import BoardCreator
from services.board_manager import BoardManager

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class Pipeline:
    """
    End-to-End Pipeline for Pinterest Affiliate Flow.
    Connects Shopee -> Keyword -> TikTok Search -> Tiktok Backend -> S3 Upload -> Pinterest.
    """
    def __init__(self, data_path: Path):
        self.data_path = data_path
        
        # Inisialisasi Modules
        self.reader = ShopeeReader(self.data_path)
        self.planner = KeywordPlanner()
        self.search_service = TiktokSearchService()
        # Sesuai Orchestrator bawaan, argumen inisialnya data_path
        self.orchestrator = SearchOrchestrator(self.data_path)
        self.selector = CandidateSelector(self.data_path)
        self.tiktok_client = TikTokBackendClient()
        self.download_manager = DownloadManager(temp_dir=Path(os.getcwd()) / "temp")
        self.seo_engine = AISeoEngine()
        self.pinterest_api = PinterestAPI()
        
        # Inisialisasi fallback board ID environment
        self.default_board_id = os.getenv("PINTEREST_BOARD_ID", "972285075743699003")
        
        # Inisialisasi Board Intelligence (Dependency Injection)
        classifier = ProductClassifier()
        cache = BoardCache(self.pinterest_api.session, self.pinterest_api.csrftoken)
        resolver = BoardResolver(classifier, cache)
        creator = BoardCreator(self.pinterest_api.session, self.pinterest_api.csrftoken)
        self.board_manager = BoardManager(cache, resolver, creator)
        
    def _format_error(self, step: str, message: str) -> Dict[str, Any]:
        return {
            "success": False,
            "step": step,
            "error": message
        }

    def run(self) -> Dict[str, Any]:
        logger.info("Starting Complete E2E Pipeline")
        
        # 1. Load Product
        logger.info("Loading product...")
        load_res = self.reader.load_products()
        if not load_res.get("success"):
            return self._format_error("load_product", load_res.get("error", "Failed loading products"))
            
        prod_res = self.reader.get_random_unposted_product()
        if not prod_res.get("success"):
            return self._format_error("get_random_product", prod_res.get("error", "Failed getting random product"))
        product = prod_res["data"]
        logger.info("Product loaded")
        
        # 2. Generate Keyword
        logger.info("Generating keywords...")
        kw_res = self.planner.generate_search_keywords(product)
        if not kw_res.get("success"):
            return self._format_error("generate_keyword", kw_res.get("error", "Failed generating keyword"))
        keywords = kw_res["keywords"]
        logger.info(f"Keywords generated: {keywords}")
        
        # 3 & 4. Search Videos & Combine Candidates
        logger.info("Searching videos...")
        # Bypass bug orchestrator bawaan yang double-load product. 
        # Kita execute search loop manual sesuai rule E2E Phase 11
        candidates = []
        product_name = product.get("nama", "").lower()
        product_words = [w for w in product_name.split() if len(w) > 3]

        for kw in keywords:
            res = self.search_service.search(kw)
            if res.get("success") and res.get("videos"):
                for v in res["videos"]:
                    title = (v.get("title") or "").lower()
                    match_count = sum(1 for w in product_words if w in title)
                    if match_count >= 2:
                        candidates.append(v)

        # Fallback jika tidak ada yang match
        if not candidates:
            for kw in keywords:
                res = self.search_service.search(kw)
                if res.get("success") and res.get("videos"):
                    candidates.extend(res["videos"])
        
        if not candidates:
            return self._format_error("search_video", "All keywords failed or returned zero valid videos.")
            
        # Search service returns Dict. Convert Dict -> Object expected by CandidateSelector
        from providers.base_provider import TiktokVideoCandidate
        candidate_objects = []
        for c in candidates:
            candidate_objects.append(TiktokVideoCandidate(**c))
            
        search_res = {"success": True, "candidates": candidate_objects}
        if not search_res.get("success"):
            return self._format_error("search_video", search_res.get("error", "Failed searching video"))
        candidates = search_res["candidates"]
        
        if not candidates:
            return self._format_error("search_video", "No video candidates found")
            
        # 5. Pilih Kandidat Terbaik
        logger.info("Selecting best candidate...")
        
        # Smart Candidate Failover: Urutkan kandidat berdasarkan score tertinggi
        ranked_candidates = sorted(
            candidates, 
            key=lambda c: self.selector.score_video(c.__dict__, product.get("nama", product.get("name", ""))), 
            reverse=True
        )
        
        max_download_attempts = int(os.getenv("MAX_DOWNLOAD_ATTEMPTS", "10"))
        candidates_to_try = ranked_candidates[:max_download_attempts]
        
        video = None
        download_url = None
        local_path = None
        
        for i, cand in enumerate(candidates_to_try, 1):
            score = self.selector.score_video(cand.__dict__, product.get("nama", product.get("name", "")))
            logger.info(f"\nCandidate {i}/{min(len(candidates_to_try), max_download_attempts)}")
            logger.info(f"Score: {score}")
            logger.info(f"Trying: {cand.video_url}")
            
            # 6 & 7. Minta link download dari TikTokBackendClient
            backend_res = self.tiktok_client.download(cand.video_url)
            if not backend_res.get("success"):
                logger.info(f"Backend failed: {backend_res.get('error')}")
                logger.info("Trying next candidate...")
                continue
                
            # Response format success dari backend ada di dalam key "data" -> "url" (Cobalt API format)
            candidate_download_url = backend_res.get("data", {}).get("url")
            if not candidate_download_url:
                logger.info("Backend failed: empty download url returned")
                logger.info("Trying next candidate...")
                continue
                
            # 8. Download Video Fisik
            logger.info("Downloading video to local...")
            dl_res = self.download_manager.download(candidate_download_url)
            if not dl_res.get("success"):
                logger.info(f"Download failed: {dl_res.get('error')}")
                logger.info("Trying next candidate...")
                continue
                
            # DownloadManager return key nya "path" bukan "filepath"
            local_path = dl_res["path"]
            video = cand
            download_url = candidate_download_url
            logger.info(f"Success\nDownload URL acquired: {local_path}")
            break
            
        if not video or not local_path:
            return self._format_error("download_video", "No downloadable candidate found")
        
        # 9. Generate Pinterest SEO
        logger.info("Generating SEO metadata...")
        seo_res = self.seo_engine.generate_metadata(product)
        if not seo_res.get("success"):
            return self._format_error("generate_seo", seo_res.get("error", "Failed generating SEO"))
        seo = seo_res["data"]
        logger.info("SEO generated")
        
        # 9.5 Determine Dynamic Board ID
        logger.info("Resolving Canonical Board ID...")
        try:
            dynamic_board_id = self.board_manager.resolve_board(product.get("nama", ""))
        except Exception as e:
            logger.warning(f"Board resolution threw exception: {e}")
            dynamic_board_id = None
            
        if dynamic_board_id:
            logger.info(f"Publishing to dynamic Board ID: {dynamic_board_id}")
            final_board_id = dynamic_board_id
        else:
            logger.warning(f"Failed to resolve or create Pinterest Board. Falling back to default Board ID: {self.default_board_id}")
            final_board_id = self.default_board_id
        
        # 10. Upload menggunakan Pinterest Provider yang SUDAH ADA
        logger.info("Uploading to Pinterest...")
        try:
            upload_res = self.pinterest_api.upload_media(str(local_path))
            if not upload_res.get("success"):
                return self._format_error("upload_media", upload_res.get("error", "Failed uploading media to Pinterest"))
            media_id = upload_res["media_id"]
            
            hashtags = " ".join(seo["hashtags"])
            final_desc = f"{seo['description']}\n\n{hashtags}"
            
            pin_res = self.pinterest_api.create_pin(
                media_info=upload_res,
                title=seo["title"],
                description=final_desc,
                board_id=final_board_id,
                destination_url=seo["destination_url"]
            )
            
            if not pin_res.get("success"):
                return self._format_error("create_pin", pin_res.get("error", "Failed creating pin"))
                
            logger.info("Publish success")
            
            # 11. Cleanup jika sukses
            self.download_manager.cleanup()
            
            return {
                "success": True,
                "product": product,
                "video": {
                    "id": video.id,
                    "title": video.title,
                    "author": video.author,
                    "duration": video.duration,
                    "thumbnail": video.thumbnail,
                    "url": video.video_url
                },
                "seo": seo,
                "publish": {
                    "pin_id": pin_res.get("pin_id"),
                    "url": pin_res.get("pin_url")
                }
            }
            
        except Exception as e:
            return self._format_error("upload_pinterest", str(e))

if __name__ == "__main__":
    import time
    
    data_path = Path(os.getcwd()) / "data" / "shopee_products.json"
    
    while True:
        try:
            logger.info("=== STARTING NEW PIPELINE CYCLE ===")
            pipeline = Pipeline(data_path)
            result = pipeline.run()
            
            print("\n=== PIPELINE RESULT ===")
            print(json.dumps(result, indent=2))
            
            if not result.get("success"):
                logger.error("Cycle failed. Will retry on next tick.")
                
        except Exception as e:
            logger.error(f"Critical pipeline error: {e}")
            
        logger.info("Sleeping for 2 hours before next cycle...")
        time.sleep(2 * 60 * 60)  # 2 hours in seconds
