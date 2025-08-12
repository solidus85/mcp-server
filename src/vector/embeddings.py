from typing import List, Optional, Union, TYPE_CHECKING
import numpy as np
import logging
from chromadb.api.types import EmbeddingFunction

from ..config import settings
from ..utils import setup_logging, Timer

# Lazy import to avoid slow startup
if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """Service for generating text embeddings using sentence-transformers"""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.embedding_model
        self.logger = setup_logging("EmbeddingService")
        self.model = None
        # Don't load model immediately - wait until first use
        # self._load_model()

    def _load_model(self):
        """Load the sentence transformer model"""
        try:
            # Lazy import here to avoid slow startup
            from sentence_transformers import SentenceTransformer
            
            with Timer(f"Loading embedding model {self.model_name}", self.logger):
                self.model = SentenceTransformer(self.model_name)
            self.logger.info(f"Loaded embedding model: {self.model_name}")
        except Exception as e:
            self.logger.error(f"Error loading embedding model: {e}")
            raise

    def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        show_progress: bool = False,
        normalize: bool = True,
    ) -> np.ndarray:
        """Generate embeddings for text(s)"""
        # Ensure model is loaded (lazy loading)
        if self.model is None:
            self._load_model()
            
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            return np.array([])
        
        try:
            with Timer(f"Encoding {len(texts)} texts", self.logger):
                embeddings = self.model.encode(
                    texts,
                    batch_size=batch_size,
                    show_progress_bar=show_progress,
                    normalize_embeddings=normalize,
                )
            
            self.logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings
        except Exception as e:
            self.logger.error(f"Error generating embeddings: {e}")
            raise

    def encode_queries(
        self,
        queries: Union[str, List[str]],
        batch_size: int = 32,
        normalize: bool = True,
    ) -> np.ndarray:
        """Generate embeddings specifically for queries (may use different pooling)"""
        # Ensure model is loaded (lazy loading)
        if self.model is None:
            self._load_model()
            
        if isinstance(queries, str):
            queries = [queries]
        
        # Some models have specific query encoding
        if hasattr(self.model, 'encode_queries'):
            return self.model.encode_queries(
                queries,
                batch_size=batch_size,
                normalize_embeddings=normalize,
            )
        else:
            # Fallback to regular encoding
            return self.encode(queries, batch_size=batch_size, normalize=normalize)

    def encode_documents(
        self,
        documents: Union[str, List[str]],
        batch_size: int = 32,
        normalize: bool = True,
    ) -> np.ndarray:
        """Generate embeddings specifically for documents"""
        # Ensure model is loaded (lazy loading)
        if self.model is None:
            self._load_model()
            
        if isinstance(documents, str):
            documents = [documents]
        
        # Some models have specific document encoding
        if hasattr(self.model, 'encode_corpus'):
            return self.model.encode_corpus(
                documents,
                batch_size=batch_size,
                normalize_embeddings=normalize,
            )
        else:
            # Fallback to regular encoding
            return self.encode(documents, batch_size=batch_size, normalize=normalize)

    def compute_similarity(
        self,
        embeddings1: np.ndarray,
        embeddings2: np.ndarray,
        metric: str = "cosine",
    ) -> np.ndarray:
        """Compute similarity between two sets of embeddings"""
        if metric == "cosine":
            # Compute cosine similarity
            from sklearn.metrics.pairwise import cosine_similarity
            return cosine_similarity(embeddings1, embeddings2)
        elif metric == "euclidean":
            # Compute euclidean distance
            from sklearn.metrics.pairwise import euclidean_distances
            return -euclidean_distances(embeddings1, embeddings2)  # Negative for similarity
        elif metric == "dot":
            # Compute dot product
            return np.dot(embeddings1, embeddings2.T)
        else:
            raise ValueError(f"Unknown similarity metric: {metric}")

    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embeddings"""
        # Ensure model is loaded (lazy loading)
        if self.model is None:
            self._load_model()
        return self.model.get_sentence_embedding_dimension()

    def get_max_sequence_length(self) -> int:
        """Get the maximum sequence length the model can handle"""
        # Ensure model is loaded (lazy loading)
        if self.model is None:
            self._load_model()
        return self.model.max_seq_length

    def get_embedding_function(self) -> EmbeddingFunction:
        """Get a ChromaDB-compatible embedding function"""
        class ChromaEmbeddingFunction(EmbeddingFunction):
            def __init__(self, embedding_service):
                self.embedding_service = embedding_service
            
            def __call__(self, input: List[str]) -> List[List[float]]:
                embeddings = self.embedding_service.encode(input)
                return embeddings.tolist()
        
        return ChromaEmbeddingFunction(self)

    def get_model_info(self) -> dict:
        """Get information about the embedding model"""
        return {
            "model_name": self.model_name,
            "embedding_dimension": self.get_embedding_dimension(),
            "max_sequence_length": self.get_max_sequence_length(),
            "model_type": type(self.model).__name__,
        }


class CachedEmbeddingService(EmbeddingService):
    """Embedding service with caching support"""

    def __init__(self, model_name: Optional[str] = None, cache_size: int = 1000):
        super().__init__(model_name)
        self.cache_size = cache_size
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0

    def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        show_progress: bool = False,
        normalize: bool = True,
    ) -> np.ndarray:
        """Generate embeddings with caching"""
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = []
        texts_to_encode = []
        text_indices = []
        
        # Check cache
        for i, text in enumerate(texts):
            cache_key = f"{text}_{normalize}"
            if cache_key in self.cache:
                embeddings.append((i, self.cache[cache_key]))
                self.cache_hits += 1
            else:
                texts_to_encode.append(text)
                text_indices.append(i)
                self.cache_misses += 1
        
        # Encode uncached texts
        if texts_to_encode:
            new_embeddings = super().encode(
                texts_to_encode,
                batch_size=batch_size,
                show_progress=show_progress,
                normalize=normalize,
            )
            
            # Update cache
            for text, embedding, idx in zip(texts_to_encode, new_embeddings, text_indices):
                cache_key = f"{text}_{normalize}"
                
                # Implement simple LRU by removing oldest if cache is full
                if len(self.cache) >= self.cache_size:
                    # Remove first (oldest) item
                    self.cache.pop(next(iter(self.cache)))
                
                self.cache[cache_key] = embedding
                embeddings.append((idx, embedding))
        
        # Sort by original index and extract embeddings
        embeddings.sort(key=lambda x: x[0])
        result = np.array([emb for _, emb in embeddings])
        
        self.logger.debug(
            f"Cache stats - Hits: {self.cache_hits}, "
            f"Misses: {self.cache_misses}, "
            f"Hit rate: {self.cache_hits/(self.cache_hits+self.cache_misses)*100:.2f}%"
        )
        
        return result

    def clear_cache(self):
        """Clear the embedding cache"""
        self.cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0
        self.logger.info("Cleared embedding cache")