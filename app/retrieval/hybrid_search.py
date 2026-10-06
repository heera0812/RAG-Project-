from typing import List, Tuple, Literal
from app.config import settings
from app.db.models import SearchResultItem
from app.retrieval.vector_search import vector_search_engine
from app.retrieval.keyword_search import keyword_search_engine


class HybridSearchEngine:
    """Combines vector retrieval with lexical keyword boosts."""

    def __init__(self):
        self.vector_engine = vector_search_engine
        self.keyword_engine = keyword_search_engine

    def search(
        self,
        query: str,
        top_k: int = settings.RETRIEVAL_TOP_K,
        use_hybrid: bool = False,
    ) -> Tuple[List[SearchResultItem], Literal["high", "medium", "low", "insufficient_evidence"]]:
        # Always run baseline vector search
        vector_results, confidence = self.vector_engine.search(query=query, top_k=top_k)

        if not use_hybrid or confidence == "insufficient_evidence":
            return vector_results, confidence

        # In hybrid mode, combine vector and keyword scores
        keyword_results = self.keyword_engine.search(query=query, top_k=top_k)
        if not keyword_results:
            return vector_results, confidence

        score_map = {}
        item_map = {}

        for r in vector_results:
            score_map[r.chunk_id] = 0.75 * r.score
            item_map[r.chunk_id] = r

        for kr in keyword_results:
            if kr.chunk_id in score_map:
                score_map[kr.chunk_id] += 0.25 * kr.score
            else:
                score_map[kr.chunk_id] = 0.25 * kr.score
                item_map[kr.chunk_id] = kr

        sorted_ids = sorted(score_map.keys(), key=lambda cid: score_map[cid], reverse=True)
        combined: List[SearchResultItem] = []
        for cid in sorted_ids[:top_k]:
            item = item_map[cid]
            item.score = round(score_map[cid], 4)
            combined.append(item)

        return combined, confidence


hybrid_search_engine = HybridSearchEngine()
