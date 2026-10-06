from typing import List, Tuple, Literal
from app.config import settings
from app.db.models import SearchResultItem
from app.db.repositories import vector_repo
from app.retrieval.query_normalizer import query_normalizer


class VectorSearchEngine:
    """Baseline vector retrieval with confidence evaluation adhering to Section 8."""

    def __init__(self):
        self.vector_repo = vector_repo
        self.normalizer = query_normalizer

    def search(
        self,
        query: str,
        n_candidates: int = settings.RETRIEVAL_CANDIDATES,
        top_k: int = settings.RETRIEVAL_TOP_K,
    ) -> Tuple[List[SearchResultItem], Literal["high", "medium", "low", "insufficient_evidence"]]:
        """Perform vector retrieval, deduplicate near-identical chunks, and assess confidence."""
        expanded_query, _, _ = self.normalizer.normalize_query(query)

        # 1. Retrieve candidates
        candidates = self.vector_repo.search(
            query=expanded_query,
            n_results=n_candidates,
            filter_approved_only=True,
        )

        if not candidates:
            return [], "insufficient_evidence"

        # 2. Assess retrieval confidence based on top similarity score
        top_score = candidates[0].score
        if top_score >= settings.SIMILARITY_HIGH_CONFIDENCE:
            confidence = "high"
        elif top_score >= settings.SIMILARITY_MEDIUM_CONFIDENCE:
            confidence = "medium"
        elif top_score >= settings.SIMILARITY_MIN_THRESHOLD:
            confidence = "low"
        else:
            confidence = "insufficient_evidence"

        # If evidence is insufficient, do not supply low-confidence matches as factual context
        if confidence == "insufficient_evidence":
            return [], "insufficient_evidence"

        # 3. Deduplicate near-identical chunks (e.g. same content hash or exact prefix)
        unique_results: List[SearchResultItem] = []
        seen_hashes = set()
        seen_pages = set()

        for item in candidates:
            content_hash = item.metadata.get("content_hash")
            page_range = (item.metadata.get("page_start"), item.metadata.get("page_end"))

            # Deduplicate exact hash
            if content_hash and content_hash in seen_hashes:
                continue
            if content_hash:
                seen_hashes.add(content_hash)

            unique_results.append(item)
            if len(unique_results) >= top_k:
                break

        return unique_results, confidence


vector_search_engine = VectorSearchEngine()
