import unittest
from services.category_intelligence import ProductClassifier

class TestProductClassifier(unittest.TestCase):
    def setUp(self):
        self.classifier = ProductClassifier()

    def test_skintific_cushion(self):
        self.assertEqual(self.classifier.classify("Skintific Cushion Velvet"), "Makeup")
        
    def test_glad2glow_sunscreen(self):
        self.assertEqual(self.classifier.classify("Glad2Glow Sunscreen"), "Skincare")
        
    def test_erigo_hoodie(self):
        self.assertEqual(self.classifier.classify("Erigo Hoodie Oversize"), "Fashion Pria")
        
    def test_panci(self):
        self.assertEqual(self.classifier.classify("Panci Anti Lengket"), "Peralatan Dapur")
        
    def test_xiaomi_powerbank(self):
        self.assertEqual(self.classifier.classify("Powerbank Xiaomi"), "Gadget & Aksesoris")
        
    def test_general_fallback(self):
        self.assertEqual(self.classifier.classify("Produk Misterius"), "General")

    def test_first_match_rule(self):
        self.assertEqual(self.classifier.classify("Tas Sepatu Olahraga"), "Tas & Dompet")

if __name__ == '__main__':
    unittest.main()
