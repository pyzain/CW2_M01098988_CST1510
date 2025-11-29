# app/common/rag.py
"""
Lightweight RAG helper (lazy-imported heavy libs).
- Keeps import-time cheap; heavy libs loaded only when needed.
- Stores a persisted faiss index + metadata (if available).
"""

import os
import pickle
import logging
from typing import List, Tuple, Optional

_logger = logging.getLogger(__name__)

# lazy handles
_sentence_transformer = None
_faiss = None
_np = None

def _lazy_imports():
    global _sentence_transformer, _faiss, _np
    if _sentence_transformer is None:
        from sentence_transformers import SentenceTransformer
        _sentence_transformer = SentenceTransformer
    if _faiss is None:
        import faiss
        _faiss = faiss
    if _np is None:
        import numpy as np
        _np = np

# Config — store embeddings under project DATA/embeddings
MODEL_NAME = "all-MiniLM-L6-v2"
EMB_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "DATA", "embeddings")
INDEX_PATH = os.path.join(EMB_DIR, "faiss.index")
METADATA_PATH = os.path.join(EMB_DIR, "metadata.pkl")

os.makedirs(EMB_DIR, exist_ok=True)


class RAG:
    def __init__(self, model_name: str = MODEL_NAME):
        # Defer heavy imports until we actually need the model or index
        self.model_name = model_name
        self.model = None
        self.index = None
        self.metadata = []

        # try to lazy-load an existing index if present
        if os.path.exists(INDEX_PATH) and os.path.exists(METADATA_PATH):
            try:
                self._load_index()
            except Exception:
                self.index = None
                self.metadata = []

    def _ensure_model(self):
        _lazy_imports()
        if self.model is None:
            # instantiate model once
            self.model = _sentence_transformer(self.model_name)

    def _save_index(self):
        _lazy_imports()
        if self.index is not None:
            _faiss.write_index(self.index, INDEX_PATH)
        with open(METADATA_PATH, "wb") as f:
            pickle.dump(self.metadata, f)

    def _load_index(self):
        _lazy_imports()
        self.index = _faiss.read_index(INDEX_PATH)
        with open(METADATA_PATH, "rb") as f:
            self.metadata = pickle.load(f)

    def build_from_dataframe(self, df, text_column: str = "description", id_column: str = "incident_id"):
        """
        Build FAISS index from dataframe rows. Saves index+metadata to disk.
        - Texts are stringified; empty descriptions are synthesized from key columns.
        """
        if df is None or df.empty:
            self.index = None
            self.metadata = []
            return

        self._ensure_model()

        texts = []
        meta = []
        for _, row in df.iterrows():
            # robustly fetch text
            try:
                text = str(row.get(text_column, "")).strip()
            except Exception:
                text = ""
            if not text:
                # synthesize short description
                text = f"Type:{row.get('type','')}; Severity:{row.get('severity','')}; Asset:{row.get('asset','')}; Status:{row.get('status','')}"
            texts.append(text)
            meta.append({"id": row.get(id_column), "text": text})

        if len(texts) == 0:
            self.index = None
            self.metadata = []
            return

        # compute embeddings (convert to numpy)
        embeddings = self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        d = embeddings.shape[1]
        self.index = _faiss.IndexFlatL2(d)
        self.index.add(embeddings)
        self.metadata = meta
        # persist
        try:
            self._save_index()
        except Exception:
            _logger.exception("Failed to save RAG index/metadata; continuing without persistence.")

    def query(self, q: str, k: int = 5) -> List[Tuple[dict, float]]:
        """
        Query the index returning list of (metadata, distance) tuples.
        Returns empty list if index missing.
        """
        if self.index is None or not self.metadata:
            return []

        self._ensure_model()
        q_emb = self.model.encode([q], convert_to_numpy=True)
        D, I = self.index.search(q_emb, k)
        results = []
        for idx, dist in zip(I[0], D[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            results.append((self.metadata[idx], float(dist)))
        return results


# Module-level singleton (lazy)
_rag_singleton: Optional[RAG] = None


def get_rag_singleton() -> RAG:
    """
    Return the module-level RAG instance, creating it lazily when first requested.
    """
    global _rag_singleton
    if _rag_singleton is None:
        _rag_singleton = RAG()
    return _rag_singleton
