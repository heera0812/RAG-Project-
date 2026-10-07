from typing import List, Tuple, Literal
from app.config import settings
from app.db.models import SearchResultItem
from app.retrieval.vector_search import vector_search_engine
from app.retrieval.keyword_search import keyword_search_engine
from app.retrieval.notebooklm_engine import notebooklm_engine


from app.retrieval.query_normalizer import query_normalizer


class HybridSearchEngine:
    """Combines vector retrieval, lexical keyword boosts, and Gemini Notebook (NotebookLM)."""

    def __init__(self):
        self.vector_engine = vector_search_engine
        self.keyword_engine = keyword_search_engine
        self.notebooklm_engine = notebooklm_engine
        self.normalizer = query_normalizer

    def search(
        self,
        query: str,
        top_k: int = settings.RETRIEVAL_TOP_K,
        use_hybrid: bool = False,
        use_notebooklm: bool = True,
    ) -> Tuple[List[SearchResultItem], Literal["high", "medium", "low", "insufficient_evidence"]]:
        # Always run baseline vector search with expanded candidate pool
        vector_results, confidence = self.vector_engine.search(query=query, top_k=max(top_k * 2, 10))

        # Normalize/expand query for cross-lingual keyword matching
        expanded_query, _, _ = self.normalizer.normalize_query(query)

        # If NotebookLM is enabled and authenticated, retrieve additional grounded passages
        nlm_results = []
        if use_notebooklm and getattr(settings, "NOTEBOOKLM_ENABLED", False) and self.notebooklm_engine.is_authenticated():
            try:
                nlm_results = self.notebooklm_engine.retrieve_chunks(query=query, top_k=2)
                if nlm_results and confidence == "insufficient_evidence":
                    confidence = "medium"
            except Exception:
                pass

        if not use_hybrid and not nlm_results:
            return vector_results[:top_k], confidence

        # In hybrid mode, combine vector and keyword scores using expanded query
        keyword_results = self.keyword_engine.search(query=expanded_query, top_k=max(top_k * 2, 10))
        if not keyword_results:
            return vector_results[:top_k], confidence

        # If both vector and keyword find relevant chunks, boost cross-lingual confidence
        if confidence == "low" and keyword_results and vector_results:
            confidence = "medium"


        score_map = {}
        item_map = {}

        for r in vector_results:
            score_map[r.chunk_id] = 0.60 * r.score
            item_map[r.chunk_id] = r

        for kr in keyword_results:
            if kr.chunk_id in score_map:
                score_map[kr.chunk_id] += 0.35 * kr.score
            else:
                score_map[kr.chunk_id] = 0.65 * kr.score
                item_map[kr.chunk_id] = kr

        for nr in nlm_results:
            if nr.chunk_id in score_map:
                score_map[nr.chunk_id] += 0.30 * nr.score
            else:
                score_map[nr.chunk_id] = 0.85 * nr.score
                item_map[nr.chunk_id] = nr

        sorted_ids = sorted(score_map.keys(), key=lambda cid: score_map[cid], reverse=True)
        combined: List[SearchResultItem] = []
        for cid in sorted_ids[:top_k]:
            item = item_map[cid]
            item.score = round(score_map[cid], 4)
            combined.append(item)

        return combined, confidence


hybrid_search_engine = HybridSearchEngine()
