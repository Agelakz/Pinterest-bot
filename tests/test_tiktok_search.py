import unittest
import logging
from typing import List

from providers.base_provider import SearchProvider, TiktokVideoCandidate
from services.tiktok_search_service import TiktokSearchService

# Disable logging output during tests
logging.getLogger("services.tiktok_search_service").setLevel(logging.CRITICAL)

class FaultyProvider(SearchProvider):
    def search_videos(self, keyword: str) -> List[TiktokVideoCandidate]:
        raise ValueError("Provider API is down")

class SuccessfulProvider(SearchProvider):
    def search_videos(self, keyword: str) -> List[TiktokVideoCandidate]:
        return [
            TiktokVideoCandidate(
                id="1",
                title=f"Test {keyword}",
                author="tester",
                duration=15,
                thumbnail="thumb.jpg",
                video_url="vid.mp4"
            )
        ]

class TestTiktokSearchService(unittest.TestCase):

    def test_search_success(self):
        provider = SuccessfulProvider()
        service = TiktokSearchService(provider)
        
        result = service.search("cats")
        
        self.assertTrue(result["success"])
        self.assertEqual(len(result["videos"]), 1)
        self.assertEqual(result["videos"][0]["id"], "1")
        self.assertEqual(result["videos"][0]["title"], "Test cats")
        self.assertEqual(result["videos"][0]["author"], "tester")
        self.assertEqual(result["videos"][0]["duration"], 15)
        self.assertEqual(result["videos"][0]["thumbnail"], "thumb.jpg")
        self.assertEqual(result["videos"][0]["video_url"], "vid.mp4")

    def test_search_failure(self):
        provider = FaultyProvider()
        service = TiktokSearchService(provider)
        
        result = service.search("dogs")
        
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Provider API is down")
        self.assertEqual(result["videos"], [])

    def test_empty_keyword(self):
        provider = SuccessfulProvider()
        service = TiktokSearchService(provider)
        
        result = service.search("")
        
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Keyword cannot be empty.")
        self.assertEqual(result["videos"], [])

    def test_whitespace_keyword(self):
        provider = SuccessfulProvider()
        service = TiktokSearchService(provider)
        
        result = service.search("   ")
        
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Keyword cannot be empty.")
        self.assertEqual(result["videos"], [])

if __name__ == '__main__':
    unittest.main()