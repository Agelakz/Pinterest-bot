import unittest
from unittest.mock import MagicMock
from services.board_resolver import BoardResolver, BoardResolution
from services.category_intelligence import ProductClassifier
from services.board_cache import BoardCache

class TestBoardResolver(unittest.TestCase):
    
    def setUp(self):
        self.classifier = ProductClassifier()
        self.mock_cache = MagicMock(spec=BoardCache)
        
        # Simulasi cache memory: Hanya punya Makeup, Fashion Wanita, dan General
        def mock_find(name):
            boards = {
                "makeup": {"id": "111", "name": "Makeup"},
                "fashion wanita": {"id": "222", "name": "Fashion Wanita"},
                "general": {"id": "333", "name": "General"}
            }
            return boards.get(name.lower())
            
        self.mock_cache.find_by_name.side_effect = mock_find
        self.resolver = BoardResolver(self.classifier, self.mock_cache)

    def test_case_1_exists(self):
        # Product: Skintific Cushion -> Category: Makeup -> Board exists
        res = self.resolver.resolve("Skintific Cushion Velvet")
        self.assertTrue(res.exists)
        self.assertEqual(res.board_name, "Makeup")
        self.assertEqual(res.board_id, "111")

    def test_case_2_not_exists(self):
        # Product: Glad2Glow -> Category: Skincare -> Board DOES NOT exist in cache
        res = self.resolver.resolve("Glad2Glow Sunscreen")
        self.assertFalse(res.exists)
        self.assertEqual(res.board_name, "Skincare")
        self.assertIsNone(res.board_id)

    def test_case_3_general_fallback(self):
        # Product: Misterius -> Category: General -> Board exists
        res = self.resolver.resolve("Produk Misterius")
        self.assertTrue(res.exists)
        self.assertEqual(res.board_name, "General")
        self.assertEqual(res.board_id, "333")

if __name__ == '__main__':
    unittest.main()
