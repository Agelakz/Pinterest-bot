import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class TiktokVideoCandidate:
    id: str
    title: str
    author: str
    duration: int
    thumbnail: str
    video_url: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "duration": self.duration,
            "thumbnail": self.thumbnail,
            "video_url": self.video_url
        }

class SearchProvider(ABC):
    """Abstract base class for TikTok search providers."""

    @abstractmethod
    def search_videos(self, keyword: str) -> List[TiktokVideoCandidate]:
        """Search for videos based on a keyword.
        
        Args:
            keyword: The search term.
            
        Returns:
            List of TiktokVideoCandidate objects.
        """
        pass
