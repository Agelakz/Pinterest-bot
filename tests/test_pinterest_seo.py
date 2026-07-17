import unittest
from services.pinterest_seo import PinterestSEOEngine

class TestSEO(unittest.TestCase):
    def test_board_generator(self):
        engine = PinterestSEOEngine()
        prod = {"nama": "SKINTIFIC Cushion", "link_affiliate": "https://shp.ee/abc"}
        res = engine.generate_metadata(prod)
        self.assertEqual(res["data"]["board"], "Makeup")

if __name__ == "__main__":
    unittest.main()
