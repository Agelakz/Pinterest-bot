import re
from typing import Dict, List, Optional
from services.keyword_planner import KeywordPlanner

class ProductClassifier:
    """
    Stateless Product Intelligence Engine.
    Determines canonical category for a given product title based on aliases and brands.
    Scoring: Alias match (+70), Brand match (+30).
    Resolves conflict using First Match Rule (index position) and highest score.
    """
    
    CANONICAL_CATEGORIES = [
        "Skincare", "Makeup", "Fashion Pria", "Fashion Wanita", "Hijab & Muslim",
        "Tas & Dompet", "Sepatu & Alas Kaki", "Peralatan Dapur", "Perabotan Rumah",
        "Elektronik Rumah", "Gadget & Aksesoris", "Audio & Komputer", "Olahraga & Outdoor",
        "Bayi & Anak", "Kesehatan", "Otomotif", "Perawatan Tubuh", "Makanan & Minuman",
        "Stationery & Hobi", "General"
    ]
    
    ALIAS_MAPPING = {
        "Makeup": [
            "cushion", "foundation", "lip tint", "lipstick", "mascara", "bedak", 
            "blush", "eyeliner", "concealer", "make up", "lipstik", "lipcream"
        ],
        "Skincare": [
            "serum", "sunscreen", "toner", "facial wash", "moisturizer", 
            "essence", "skincare", "sabun cuci muka", "sunblock", "micellar"
        ],
        "Fashion Wanita": [
            "dress", "blouse", "rok", "cardigan", "atasan wanita", "kemeja wanita",
            "celana wanita", "kebaya", "daster", "tunik"
        ],
        "Fashion Pria": [
            "kaos pria", "hoodie pria", "jaket pria", "celana pria", "kemeja pria",
            "sweater pria", "hoodie oversize", "hoodie", "kaos oversize"
        ],
        "Hijab & Muslim": [
            "hijab", "pashmina", "gamis", "mukena", "baju koko", "sarung", "peci"
        ],
        "Tas & Dompet": [
            "tas", "dompet", "sling bag", "tote bag", "backpack", "ransel"
        ],
        "Sepatu & Alas Kaki": [
            "sepatu", "sandal", "sneakers", "heels", "wedges", "slip on"
        ],
        "Peralatan Dapur": [
            "panci", "wajan", "spatula", "blender", "piring", "gelas", "pisau dapur",
            "anti lengket", "penggorengan", "tumbler", "botol minum", "termos", "kotak makan"
        ],
        "Perabotan Rumah": [
            "lemari", "meja", "kursi", "rak", "sprei", "selimut", "bantal", "guling",
            "dekorasi"
        ],
        "Elektronik Rumah": [
            "kipas angin", "mesin cuci", "kulkas", "setrika", "vacuum", "televisi"
        ],
        "Gadget & Aksesoris": [
            "powerbank", "casing", "case hp", "kabel data", "charger", "smartphone",
            "tripod"
        ],
        "Audio & Komputer": [
            "tws", "earphone", "headset", "speaker", "laptop", "keyboard", "mouse",
            "monitor", "headphone"
        ],
        "Perawatan Tubuh": [
            "body lotion", "shampoo", "sabun mandi", "deodoran", "parfum", "hair oil",
            "body wash"
        ],
        "Olahraga & Outdoor": [
            "matras yoga", "sepeda", "raket", "tenda", "dumbell", "sepatu bola"
        ]
    }
    
    # Map KeywordPlanner.KNOWN_BRANDS to Canonical
    BRAND_MAPPING = {
        "skintific": "Skincare",
        "somethinc": "Skincare",
        "wardah": "Makeup",
        "make over": "Makeup",
        "emina": "Makeup",
        "hanasui": "Makeup",
        "scarlett": "Perawatan Tubuh",
        "the originote": "Skincare",
        "azarine": "Skincare",
        "dior": "Makeup",
        "maybelline": "Makeup",
        "goto": "Perabotan Rumah",
        "philips": "Elektronik Rumah",
        "xiaomi": "Gadget & Aksesoris",
        "samsung": "Gadget & Aksesoris",
        "apple": "Gadget & Aksesoris",
        "oxone": "Peralatan Dapur",
        "jiniso": "Fashion Wanita",
        "erigo": "Fashion Pria",
        "glad2glow": "Skincare"
    }

    def _normalize(self, text: str) -> str:
        # Lowercase
        text = text.lower()
        # Remove weird symbols but keep alphanumeric and spaces
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        # Remove duplicate whitespaces
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def classify(self, title: str) -> str:
        norm_title = self._normalize(title)
        
        best_alias_cat = None
        best_alias_index = float('inf')
        alias_score = 0
        
        # 1. Alias Match (+70) with First Match Rule
        for cat, aliases in self.ALIAS_MAPPING.items():
            for alias in aliases:
                # Use regex boundaries to match exact words
                pattern = r'\b' + re.escape(alias) + r'\b'
                match = re.search(pattern, norm_title)
                if match:
                    idx = match.start()
                    # Priority: Lowest index (appears first)
                    if idx < best_alias_index:
                        best_alias_index = idx
                        best_alias_cat = cat
                        alias_score = 70
                        
        # 2. Brand Match (+30)
        best_brand_cat = None
        brand_score = 0
        
        # We reuse the set logic from KeywordPlanner but map to our categories
        for brand, cat in self.BRAND_MAPPING.items():
            if norm_title.startswith(brand) or f" {brand} " in f" {norm_title} ":
                best_brand_cat = cat
                brand_score = 30
                break
                
        # 3. Conflict Resolution
        if alias_score == 0 and brand_score == 0:
            return "General"
            
        if alias_score > brand_score:
            return best_alias_cat
        elif brand_score > alias_score:
            return best_brand_cat
        else:
            # Fallback if both scores exist but theoretically alias_score (70) > brand_score (30) always.
            return best_alias_cat or "General"
