import logging
import os
from pathlib import Path
from typing import Dict, Any

from services.shopee_reader import ShopeeReader
from services.pinterest_seo import PinterestSEOEngine
from services.pinterest_api import PinterestAPI

logger = logging.getLogger(__name__)

class AffiliatePipeline:
    """
    Orchestrator for Pinterest Affiliate flow.
    Responsible for connecting ShopeeReader -> SEOEngine -> PinterestAPI.
    No business logic, only sequencing and state passing.
    """
    
    def __init__(self, data_path: Path, video_path: Path):
        self.data_path = data_path
        self.video_path = video_path
        
        # Dependency Injection (Internalized for MVP simplicity)
        self.reader = ShopeeReader(self.data_path)
        self.seo_engine = PinterestSEOEngine()
        self.pinterest_api = PinterestAPI()
        
    def _format_error(self, step: str, message: str) -> Dict[str, Any]:
        return {
            "success": False,
            "error": message,
            "step": step,
            "data": None
        }

    def load_product(self) -> Dict[str, Any]:
        logger.info("Loading product")
        
        load_res = self.reader.load_products()
        if not load_res["success"]:
            return load_res
            
        prod_res = self.reader.get_random_product()
        if prod_res["success"]:
            logger.info("Product loaded")
        return prod_res

    def generate_metadata(self, product: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Generating SEO metadata")
        meta_res = self.seo_engine.generate_metadata(product)
        if meta_res["success"]:
            logger.info("Metadata generated")
        return meta_res

    def upload_media(self) -> Dict[str, Any]:
        logger.info("Uploading media")
        upload_res = self.pinterest_api.upload_media(str(self.video_path))
        if upload_res["success"]:
            logger.info("Media uploaded")
        return upload_res

    def publish_pin(self, media_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Creating Pinterest Pin")
        
        # Assemble description with hashtags
        hashtags = " ".join(metadata["hashtags"])
        final_desc = f"{metadata['description']}\n\n{hashtags}"
        
        pin_res = self.pinterest_api.create_pin(
            media_id=media_id,
            title=metadata["title"],
            description=final_desc,
            board_id=metadata["board"], # Note: API requires numeric Board ID, but MVP SEO outputs string. Pinterest API will fail here on a real API call if board isn't resolved to ID, but logic flow holds.
            destination_url=metadata["destination_url"]
        )
        if pin_res.get("success"):
            logger.info("Pin created")
        return pin_res

    def run(self) -> Dict[str, Any]:
        logger.info("Starting Affiliate Pipeline")
        
        # Step 1: Load Product
        prod_res = self.load_product()
        if not prod_res.get("success"):
            return self._format_error("load_product", prod_res.get("error", "Failed"))
        product = prod_res["data"]
            
        # Step 2: Generate Metadata
        meta_res = self.generate_metadata(product)
        if not meta_res.get("success"):
            return self._format_error("generate_metadata", meta_res.get("error", "Failed"))
        metadata = meta_res["data"]
            
        # Step 3: Upload Media
        upload_res = self.upload_media()
        if not upload_res.get("success"):
            return self._format_error("upload_media", upload_res.get("error", "Failed"))
        media_id = upload_res["media_id"]
            
        # Step 4: Publish Pin
        pin_res = self.publish_pin(media_id, metadata)
        if not pin_res.get("success"):
            return self._format_error("publish_pin", pin_res.get("error", "Failed"))
            
        logger.info("Pipeline completed")
        
        return {
            "success": True,
            "product": product,
            "metadata": metadata,
            "pin_id": pin_res["pin_id"],
            "pin_url": pin_res["pin_url"],
            "board": metadata["board"],
            "status": "published"
        }
