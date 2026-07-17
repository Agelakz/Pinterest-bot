import logging
from typing import List
from providers.base_provider import SearchProvider, TiktokVideoCandidate

class MockProvider(SearchProvider):
    """A mock provider for testing and fallback purposes."""
    
    def search_videos(self, keyword: str) -> List[TiktokVideoCandidate]:
        return [
            TiktokVideoCandidate(
                id=f"mock_{keyword}_123",
                title=f"Sample video for {keyword}",
                author="mock_author",
                duration=30,
                thumbnail="https://example.com/thumb.jpg",
                video_url="https://example.com/video.mp4"
            )
        ]