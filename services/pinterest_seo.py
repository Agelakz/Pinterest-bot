import logging
import re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class PinterestSEOEngine:
    """
    Rule-based Pinterest SEO Engine (MVP).
    Generates metadata from Shopee product info without AI.
    """

    BANNED_WORDS = {"terbaik", "termurah", "paling murah", "100%", "dijamin", "bagus banget", "ori"}

    def _format_success(self, data: Any) -> Dict[str, Any]:
        return {"success": True, "data": data}

    def _format_error(self, message: str) -> Dict[str, Any]:
        return {"success": False, "error": message, "data": None}

    def _clean_text(self, text: str) -> str:
        """Removes banned words and extra spaces."""
        cleaned = text
        for word in self.BANNED_WORDS:
            # Case insensitive replace
            cleaned = re.sub(rf'\b{re.escape(word)}\b', '', cleaned, flags=re.IGNORECASE)
        # Remove multiple spaces
        return re.sub(r'\s+', ' ', cleaned).strip()

    def _validate_product(self, product: Dict[str, Any]) -> bool:
        if not product:
            return False
        if not product.get("nama") or not product.get("link_affiliate"):
            return False
        if not product["link_affiliate"].startswith("https://"):
            return False
        return True

    def generate_title(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Generate title max 100 chars."""
        if not self._validate_product(product):
            return self._format_error("Invalid product data")
            
        # Clean title
        nama = self._clean_text(product["nama"])
        
        # Pinterest title limit is 100.
        if len(nama) > 100:
            # Truncate nicely
            nama = nama[:97].rsplit(' ', 1)[0] + "..."
            
        return self._format_success(nama)

    def generate_description(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Generate natural description (approx 200-400 chars) highlighting benefits."""
        if not self._validate_product(product):
            return self._format_error("Invalid product data")
            
        nama = self._clean_text(product["nama"])
        category = product.get("kategori", "").strip().lower()
        
        # Rule-based natural generation based on category clues
        if "beauty" in category or "skincare" in category:
            desc = f"Temukan manfaat luar biasa dari {nama}. Produk ini diformulasikan khusus untuk memberikan hasil yang maksimal, cocok digunakan untuk perawatan rutin Anda sehari-hari. Dapatkan tampilan yang lebih segar dan merona tanpa repot."
        elif "fashion" in category:
            desc = f"Tampil lebih gaya dan percaya diri dengan {nama}. Didesain dengan material berkualitas yang nyaman dipakai sepanjang hari. Pilihan tepat untuk melengkapi gaya kasual maupun formal Anda kapan saja."
        elif "home" in category or "kitchen" in category:
            desc = f"Bawa kenyamanan dan fungsionalitas ke rumah Anda dengan {nama}. Solusi praktis yang didesain untuk memudahkan aktivitas harian, awet, dan memiliki desain minimalis yang cocok untuk berbagai sudut ruangan."
        else:
            desc = f"Tingkatkan kualitas aktivitas Anda dengan {nama}. Produk fungsional pilihan yang dirancang untuk menjawab kebutuhan Anda. Mudah digunakan, praktis, dan memberikan hasil yang bisa Anda andalkan setiap saat."
        
        return self._format_success(desc)

    def generate_keywords(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Extract 5-10 keywords from title and category."""
        if not self._validate_product(product):
            return self._format_error("Invalid product data")
            
        nama = self._clean_text(product["nama"]).lower()
        category = product.get("kategori", "").lower()
        
        # Tokenize by word boundary, strip non-alphanumeric
        words = re.findall(r'\b[a-z]{3,}\b', nama)
        
        # Add category if valid
        if len(category) >= 3:
            words.append(category)
            
        # Hardcode some general fillers to ensure min 5 length if too short
        words.extend(["rekomendasi", "shopee", "affiliate", "review", "haul", "viral"])
        
        # Unique list, preserving some semblance of order
        seen = set()
        unique_keywords = []
        for w in words:
            if w not in seen and w not in self.BANNED_WORDS:
                seen.add(w)
                unique_keywords.append(w)
                
        # Limit 5-10
        final_keywords = unique_keywords[:10]
        
        return self._format_success(final_keywords)

    def generate_hashtags(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Generate max 8 hashtags from keywords."""
        kw_resp = self.generate_keywords(product)
        if not kw_resp["success"]:
            return kw_resp
            
        keywords = kw_resp["data"]
        
        # Convert to hashtags, limit 8
        hashtags = [f"#{kw.replace(' ', '')}" for kw in keywords[:8]]
        return self._format_success(hashtags)

    def generate_board(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Map product title to canonical board name using ProductClassifier."""
        if not self._validate_product(product):
            return self._format_error("Invalid product data")
            
        from services.category_intelligence import ProductClassifier
        classifier = ProductClassifier()
        board_name = classifier.classify(product.get("nama", ""))
        
        return self._format_success(board_name)

    def generate_alt_text(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Generate descriptive alt text for accessibility."""
        if not self._validate_product(product):
            return self._format_error("Invalid product data")
            
        nama = self._clean_text(product["nama"])
        alt = f"Gambar detail dari {nama} yang dapat digunakan untuk referensi visual dan rekomendasi produk harian."
        
        # Limit reasonable length
        return self._format_success(alt[:100].strip())

    def generate_metadata(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate all SEO metadata."""
        logger.info("Generating Pinterest SEO metadata...")
        
        if not self._validate_product(product):
            return self._format_error("Invalid product data")
            
        metadata = {
            "title": self.generate_title(product)["data"],
            "description": self.generate_description(product)["data"],
            "keywords": self.generate_keywords(product)["data"],
            "hashtags": self.generate_hashtags(product)["data"],
            "board": self.generate_board(product)["data"],
            "alt_text": self.generate_alt_text(product)["data"],
            "destination_url": product["link_affiliate"]
        }
        
        logger.info("Title generated")
        logger.info("Keywords generated")
        logger.info("Metadata completed")
        
        return self._format_success(metadata)