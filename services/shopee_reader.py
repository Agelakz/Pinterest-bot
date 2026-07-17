import json
import logging
import random
from pathlib import Path
from typing import Dict, Any, List, Optional, Set

logger = logging.getLogger(__name__)


class ShopeeReader:
    """
    Single source of truth for reading Shopee Affiliate product database.
    Supports deduplication via posted_products.json + better randomization.
    """

    def __init__(self, json_path: str | Path, posted_file: str = "posted_products.json"):
        self.json_path = Path(json_path)
        self.posted_file = Path(posted_file)
        self.products: List[Dict[str, Any]] = []
        self.posted_ids: Set[str] = set()

    def _load_posted(self):
        if self.posted_file.exists():
            try:
                with open(self.posted_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.posted_ids = set(data.get("posted", []))
            except Exception:
                self.posted_ids = set()
        else:
            self.posted_ids = set()

    def _save_posted(self, product_id: str):
        self.posted_ids.add(product_id)
        try:
            with open(self.posted_file, 'w', encoding='utf-8') as f:
                json.dump({"posted": list(self.posted_ids)}, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save posted_products.json: {e}")

    def _format_success(self, data: Any) -> Dict[str, Any]:
        return {"success": True, "data": data}

    def _format_error(self, message: str) -> Dict[str, Any]:
        return {"success": False, "error": message, "data": None}

    def load_products(self) -> Dict[str, Any]:
        logger.info("Loading Shopee products...")
        if not self.json_path.exists():
            return self._format_error(f"File not found: {self.json_path}")

        try:
            with open(self.json_path, 'r', encoding='utf-8-sig') as f:
                raw_data = json.load(f)
        except UnicodeDecodeError:
            with open(self.json_path, 'r', encoding='latin-1') as f:
                raw_data = json.load(f)
        except Exception as e:
            return self._format_error(f"Error reading file: {e}")

        if not isinstance(raw_data, list):
            return self._format_error("JSON root must be a list")

        valid_products = []
        for item in raw_data:
            if isinstance(item, dict) and "nama" in item and "link_affiliate" in item:
                item["kategori"] = item.get("kategori", "")
                valid_products.append(item)

        self.products = valid_products
        self._load_posted()
        logger.info(f"Loaded {len(self.products)} products | Already posted: {len(self.posted_ids)}")
        return self._format_success(self.products)

    def get_random_unposted_product(self) -> Dict[str, Any]:
        """
        Return a truly random product that has NOT been posted yet.
        Uses shuffle for better randomness.
        """
        if not self.products:
            return self._format_error("Products not loaded")

        # Filter unposted
        unposted = [
            p for p in self.products
            if (p.get("id") not in self.posted_ids) and (p.get("nama") not in self.posted_ids)
        ]

        if not unposted:
            logger.warning("All products have been posted. Resetting posted_products.json...")
            if self.posted_file.exists():
                self.posted_file.unlink()
            self.posted_ids.clear()
            unposted = self.products

        # Shuffle for better randomness
        random.shuffle(unposted)
        product = unposted[0]

        logger.info(f"Selected random unposted product: {product.get('nama', 'Unknown')}")
        return self._format_success(product)

    def mark_as_posted(self, product: Dict[str, Any]):
        """Mark product as posted after successful publish."""
        pid = product.get("id") or product.get("nama")
        if pid:
            self._save_posted(pid)
            logger.info(f"Marked product as posted: {pid}")