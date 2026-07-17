import unittest
import os
from unittest.mock import patch

from services.tiktok_search_service import TiktokSearchService
from providers.base_provider import SearchProvider, TiktokVideoCandidate

class DummyProvider(SearchProvider):
    def search_videos(self, keyword: str):
        return [
            TiktokVideoCandidate(
                id="dummy_1",
                title=f"Dummy {keyword}",
                author="tester",
                duration=15,
                thumbnail="thumb.jpg",
                video_url="vid.mp4"
            )
        ]

class TestTiktokSearchServiceConfig(unittest.TestCase):
    
    @patch.dict(os.environ, {"SEARCH_PROVIDER": "mock"})
    def test_env_provider_loading(self):
        service = TiktokSearchService()
        self.assertEqual(service.provider.__class__.__name__, "MockProvider")
        
        result = service.search("test")
        self.assertTrue(result["success"])
        self.assertEqual(len(result["videos"]), 1)
        
    def test_explicit_provider_loading(self):
        service = TiktokSearchService(provider=DummyProvider())
        self.assertEqual(service.provider.__class__.__name__, "DummyProvider")
        
        result = service.search("test")
        self.assertTrue(result["success"])
        self.assertEqual(result["videos"][0]["id"], "dummy_1")

if __name__ == '__main__':
    unittest.main()