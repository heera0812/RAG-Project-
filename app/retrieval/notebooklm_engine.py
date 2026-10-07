import asyncio
import logging
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path

from app.config import settings
from app.db.models import SearchResultItem, ChatResponse, SourceCitation

logger = logging.getLogger(__name__)


class NotebookLMEngine:
    """Agentic integration layer with Google Gemini Notebook (NotebookLM).
    
    Acts as both a grounded retrieval enhancer and an optional high-quality
    generation engine while maintaining strict Shantikunj AI rules and
    Gurudev -> Arth -> Aaj ka Abhyas reflection formulas.
    """

    def __init__(self):
        self._client_cls = None
        self._paths_mod = None
        self._initialized = False
        self._notebook_id: Optional[str] = settings.NOTEBOOKLM_NOTEBOOK_ID

    def _ensure_imports(self):
        if not self._initialized:
            try:
                from notebooklm import NotebookLMClient
                import notebooklm.paths as paths
                self._client_cls = NotebookLMClient
                self._paths_mod = paths
                self._initialized = True
            except ImportError:
                logger.warning("notebooklm-py package not found.")
                self._initialized = False

    def is_authenticated(self) -> bool:
        """Check if NotebookLM credentials exist in storage."""
        self._ensure_imports()
        if not self._initialized or not self._paths_mod:
            return False
        try:
            storage_path = self._paths_mod.get_storage_path()
            return storage_path.exists() and storage_path.stat().st_size > 50
        except Exception as e:
            logger.debug(f"Error checking NotebookLM auth: {e}")
            return False

    async def _get_or_select_notebook(self, client) -> Optional[str]:
        """Resolve active notebook ID or select the most relevant existing notebook."""
        if self._notebook_id:
            return self._notebook_id

        try:
            notebooks = await client.notebooks.list()
            if not notebooks:
                logger.info("No existing notebook found. Creating 'Shantikunj AI Knowledge Base'...")
                new_nb = await client.notebooks.create("Shantikunj AI Knowledge Base")
                self._notebook_id = new_nb.id
                return self._notebook_id

            # Prefer notebooks with relevant names
            for nb in notebooks:
                name = getattr(nb, "title", getattr(nb, "name", "")).lower()
                if "shantikunj" in name or "gayatri" in name or "mahavigyan" in name:
                    self._notebook_id = nb.id
                    return self._notebook_id

            # Otherwise select the most recently updated notebook
            self._notebook_id = notebooks[0].id
            return self._notebook_id
        except Exception as e:
            logger.warning(f"Failed to list or select notebook: {e}")
            return None

    async def ask_async(
        self,
        question: str,
        notebook_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Query NotebookLM for grounded answers and source references."""
        if not self.is_authenticated():
            return None

        try:
            async with self._client_cls.from_storage() as client:
                nb_id = notebook_id or await self._get_or_select_notebook(client)
                if not nb_id:
                    logger.warning("No notebook available in NotebookLM.")
                    return None

                # Ask with strict grounding
                prompt = (
                    f"{question}\n\n"
                    f"[Please provide a concise, factual answer strictly grounded in Gurudev Pandit Shriram Sharma Acharya's "
                    f"authorized literature with citations.]"
                )
                result = await client.chat.ask(nb_id, prompt)
                return {
                    "answer": result.answer,
                    "references": getattr(result, "references", []),
                    "conversation_id": getattr(result, "conversation_id", None),
                    "turn_number": getattr(result, "turn_number", 1),
                    "notebook_id": nb_id,
                }
        except Exception as e:
            logger.warning(f"NotebookLM query failed: {e}")
            return None

    def ask_sync(
        self,
        question: str,
        notebook_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Synchronous wrapper for ask_async."""
        try:
            # Handle existing event loop if called in async environments
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(asyncio.run, self.ask_async(question, notebook_id))
                    return future.result(timeout=45.0)
            else:
                return asyncio.run(self.ask_async(question, notebook_id))
        except Exception as e:
            logger.warning(f"NotebookLM sync call failed: {e}")
            return None

    def retrieve_chunks(
        self,
        query: str,
        top_k: int = 3,
    ) -> List[SearchResultItem]:
        """Extract grounded passages from NotebookLM and return as SearchResultItems."""
        if not self.is_authenticated():
            return []

        res = self.ask_sync(query)
        if not res or not res.get("answer"):
            return []

        items: List[SearchResultItem] = []
        answer_text = res["answer"].strip()
        nb_id = res.get("notebook_id", "notebooklm")

        # Create a high-quality grounded chunk from NotebookLM's synthesis
        item = SearchResultItem(
            chunk_id=f"nlm_{nb_id[:8]}",
            document_id="doc_notebooklm_grounded",
            content=f"Gemini Notebook Grounded Synthesis:\n{answer_text}",
            score=0.88,
            metadata={
                "book": "Gayatri Mahavigyan (Gemini Notebook Grounded)",
                "chapter": "NotebookLM Synthesis",
                "page_start": 1,
                "page_end": 1,
                "source_type": "notebooklm",
                "quality_status": "approved",
                "copyright_status": "approved",
            },
        )
        items.append(item)

        # Process any granular source references if provided by NotebookLM
        for idx, ref in enumerate(res.get("references", []), start=1):
            ref_snippet = getattr(ref, "snippet", getattr(ref, "text", str(ref)))
            if ref_snippet and len(ref_snippet) > 20:
                items.append(
                    SearchResultItem(
                        chunk_id=f"nlm_ref_{idx}",
                        document_id="doc_notebooklm_grounded",
                        content=ref_snippet,
                        score=0.85,
                        metadata={
                            "book": "Gayatri Mahavigyan (Grounded Reference)",
                            "chapter": "NotebookLM Reference",
                            "page_start": idx,
                            "page_end": idx,
                            "source_type": "notebooklm",
                            "quality_status": "approved",
                            "copyright_status": "approved",
                        },
                    )
                )

        return items[:top_k]


notebooklm_engine = NotebookLMEngine()
