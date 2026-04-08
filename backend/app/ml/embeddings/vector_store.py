import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import logging

class SemanticVectorStore:
    """
    Local embedding generator using sentence-transformers (all-MiniLM-L6-v2 by default for speed).
    Caches vectors to disk if needed, simulating pgvector behavior.
    """
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model_name = model_name
        self.encoder = None

    def _get_encoder(self) -> SentenceTransformer:
        if self.encoder is None:
            logging.info(f"Loading SemanticVectorStore model: {self.model_name}")
            # Lazy-load embeddings so the API can boot within tight memory limits.
            try:
                self.encoder = SentenceTransformer(self.model_name, local_files_only=True)
            except Exception:
                self.encoder = SentenceTransformer(self.model_name)
        return self.encoder
    
    def generate_embeddings(self, texts: list[str]) -> np.ndarray:
        """Generates dense embeddings for a list of strings."""
        if not texts: return np.array([])
        return self._get_encoder().encode(texts, show_progress_bar=False, normalize_embeddings=True)
        
    def query_similarity(self, query_text: str, document_embeddings: np.ndarray) -> np.ndarray:
        """Computes cosine similarity of a query string against the pre-computed document index."""
        if document_embeddings.size == 0: return np.array([])
        query_vec = self._get_encoder().encode([query_text], normalize_embeddings=True)
        sims = cosine_similarity(query_vec, document_embeddings)
        return sims[0]
