import logging
import re
from typing import Dict, Any, List, Set

logger = logging.getLogger(__name__)


class KeywordPlanner:
    """
    Improved Keyword Planner.
    Generates more specific and relevant TikTok search keywords
    based on product name + brand + category.
    """

    BANNED_WORDS = {
        "free", "official", "gratis", "100%", "spf", "pa+++", "ori",
        "original", "murah", "diskon", "terbaik", "grosir", "promo"
    }

    def _format_success(self, data: Any) -> Dict[str, Any]:
        return {"success": True, **data}

    def _format_error(self, message: str) -> Dict[str, Any]:
        return {"success": False, "error": message}

    def sanitize_keyword(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r'[^a-z\s]', ' ', text)
        words = text.split()
        clean_words = [w for w in words if w not in self.BANNED_WORDS and len(w) > 1]
        return " ".join(clean_words[:6]).strip()

    def extract_brand(self, product: Dict[str, Any]) -> str:
        name = product.get("nama", "").lower()
        KNOWN_BRANDS = {
            "skintific", "somethinc", "wardah", "make over", "emina", "hanasui",
            "scarlett", "the originote", "azarine", "dior", "maybelline",
            "goto", "philips", "xiaomi", "samsung", "apple", "oxone", "jiniso", "erigo"
        }
        for brand in KNOWN_BRANDS:
            if name.startswith(brand) or f" {brand} " in f" {name} ":
                return brand
        first_word = re.split(r'[^a-zA-Z0-9]', name)[0].strip()
        if first_word and len(first_word) > 2 and first_word not in self.BANNED_WORDS:
            return first_word
        return ""

    def generate_search_keywords(self, product: Dict[str, Any]) -> Dict[str, Any]:
        raw_name = product.get("nama", "")
        clean_name = self.sanitize_keyword(raw_name)
        brand = self.extract_brand(product)
        category = product.get("kategori", "").lower()

        keywords = set()

        # 1. Full product name (most specific)
        if clean_name:
            keywords.add(clean_name)

        # 2. Brand + key product words
        if brand:
            words = clean_name.split()
            if len(words) >= 2:
                keywords.add(f"{brand} {words[0]} {words[1]}")
            else:
                keywords.add(f"{brand} {clean_name}")

        # 3. Category + main product word
        if category and clean_name:
            main_word = clean_name.split()[0]
            keywords.add(f"{category} {main_word}")

        # 4. Just product name without brand (fallback)
        if clean_name:
            keywords.add(clean_name)

        # Limit to 4 best keywords
        final_keywords = list(keywords)[:4]

        if not final_keywords:
            return self._format_error("Failed to generate keywords")

        logger.info(f"Generated keywords: {final_keywords}")
        return self._format_success({"keywords": final_keywords})