import logging
from pathlib import Path
from typing import Dict, Any, List

from services.search_orchestrator import SearchOrchestrator

logger = logging.getLogger(__name__)

class CandidateSelector:
    """
    Rule-based Candidate Selector MVP.
    Evaluates candidates from SearchOrchestrator and picks the best ONE.
    Deterministic, no AI used.
    """

    def __init__(self, data_path: Path):
        self.data_path = data_path
        # Dependency Injection (Internalized for MVP)
        self.orchestrator = SearchOrchestrator(self.data_path)

    def _format_success(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {"success": True, **data}

    def _format_error(self, message: str) -> Dict[str, Any]:
        return {"success": False, "error": message, "data": None}

    def score_video(self, video: Dict[str, Any], product_name: str) -> int:
        """
        Calculates score based on deterministic rules.
        """
        score = 0
        
        # We assume validity (download_url and filename) is already checked before calling this, 
        # but we add the score bumps based on the rule specification anyway.
        if video.get("download_url"):
            score += 10
        if video.get("filename"):
            score += 5
            
        title = video.get("title", "")
        if title:
            score += 10
            # Relevance check: if any significant word from product name is in video title
            prod_words = [w.lower() for w in product_name.split() if len(w) > 3]
            title_lower = title.lower()
            relevance = any(pw in title_lower for pw in prod_words)
            if relevance:
                score += 40
            
            # Penalty check: Heavy hard-selling / likely burned-in watermark overlay videos
            negative_keywords = ["promo", "murah", "diskon", "flash sale", "flashsale", "gratis ongkir", "free ongkir", "klik keranjang"]
            has_negative = any(nk in title_lower for nk in negative_keywords)
            if has_negative:
                score -= 40
        else:
            score -= 5
            
        author = video.get("author", "")
        if author:
            score += 5
            
        thumbnail = video.get("thumbnail", "")
        if thumbnail:
            score += 10
            
        duration = int(video.get("duration", 0))
        if duration == 0:
            score -= 20
        elif 10 <= duration <= 60:
            score += 20
            
        return score

    def run(self) -> Dict[str, Any]:
        """Main flow to score and select the best candidate."""
        
        # 1. Gather candidates from Orchestrator
        orch_res = self.orchestrator.run()
        if not orch_res.get("success"):
            return self._format_error(f"Search Orchestrator failed: {orch_res.get('error')}")
            
        product = orch_res.get("product", {})
        videos = orch_res.get("videos", [])
        
        logger.info(f"Evaluating {len(videos)} candidates")
        
        valid_candidates = []
        product_name = product.get("nama", "")
        
        # 2. Score Candidates
        for vid in videos:
            # Skip invalid candidates
            if not vid.get("download_url") or not vid.get("filename"):
                continue
                
            score = self.score_video(vid, product_name)
            vid_with_score = dict(vid)
            vid_with_score["score"] = score
            
            logger.info(f"Candidate score: {score}")
            valid_candidates.append(vid_with_score)
            
        # 3. Handle Empty
        if not valid_candidates:
            return self._format_error("No valid candidate")
            
        # 4. Sort and Select (descending by score, fallback to original order on tie)
        valid_candidates.sort(key=lambda x: x["score"], reverse=True)
        
        selected_video = valid_candidates[0]
        logger.info(f"Selected score: {selected_video['score']}")
        
        return self._format_success({
            "product": product,
            "selected_video": selected_video,
            "candidate_count": len(valid_candidates)
        })
