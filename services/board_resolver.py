import logging
from dataclasses import dataclass
from typing import Optional
from services.category_intelligence import ProductClassifier
from services.board_cache import BoardCache

logger = logging.getLogger(__name__)

@dataclass
class BoardResolution:
    board_name: str
    board_id: Optional[str]
    exists: bool

class BoardResolver:
    """
    Resolves a product title into a Pinterest board ID using existing classifier and cache memory.
    Strictly performs offline local resolution (No API Calls, No Create operations).
    """
    
    def __init__(self, classifier: ProductClassifier, cache: BoardCache):
        self.classifier = classifier
        self.cache = cache
        
    def resolve(self, product_title: str) -> BoardResolution:
        # 1. Determine canonical category name
        board_name = self.classifier.classify(product_title)
        
        # 2. Look up in local memory cache
        board_obj = self.cache.find_by_name(board_name)
        
        if board_obj:
            logger.info(f"Board found: {board_name}")
            return BoardResolution(
                board_name=board_name,
                board_id=board_obj.get("id"),
                exists=True
            )
        else:
            logger.info(f"Board not found: {board_name}")
            return BoardResolution(
                board_name=board_name,
                board_id=None,
                exists=False
            )
