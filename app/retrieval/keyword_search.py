import re
from typing import List
from app.db.models import SearchResultItem
from app.db.repositories import metadata_repo


class KeywordSearchEngine:
    """Exact lexical matching for mantras, book names, Sanskrit terms, and titles."""

    def __init__(self):
        self.repo = metadata_repo

    def search(self, query: str, top_k: int = 5) -> List[SearchResultItem]:
        query_words = [w for w in re.findall(r"[\w\u0900-\u097F]+", query) if len(w) > 2]
        if not query_words:
            return []

        all_docs = self.repo.list_documents()
        items: List[SearchResultItem] = []

        for doc in all_docs:
            chunks = self.repo.list_chunks_for_document(doc.document_id)
            for chk in chunks:
                if chk.quality_status != "approved":
                    continue

                text = chk.content
                # Count matches
                matches = sum(1 for w in query_words if w in text)
                if matches > 0:
                    score = min(1.0, matches / len(query_words))
                    items.append(
                        SearchResultItem(
                            chunk_id=chk.chunk_id,
                            document_id=chk.document_id,
                            content=chk.content,
                            score=round(score, 4),
                            metadata=chk.to_metadata(),
                        )
                    )

        items.sort(key=lambda x: x.score, reverse=True)
        return items[:top_k]


keyword_search_engine = KeywordSearchEngine()
