from typing import List, Dict, Any, Optional, Tuple
import logging
from dataclasses import dataclass

from .database import VectorDatabase
from .embeddings import EmbeddingService, CachedEmbeddingService
from ..utils import setup_logging, Timer


@dataclass
class SearchResult:
    """Represents a search result"""
    id: str
    document: str
    metadata: Dict[str, Any]
    score: float
    rank: int


class VectorSearchEngine:
    """High-level search engine combining vector database and embeddings"""

    def __init__(
        self,
        database: Optional[VectorDatabase] = None,
        embedding_service: Optional[EmbeddingService] = None,
        use_cache: bool = True,
    ):
        self.logger = setup_logging("VectorSearchEngine")
        
        # Initialize database
        self.database = database or VectorDatabase()
        
        # Initialize embedding service
        if embedding_service:
            self.embedding_service = embedding_service
        elif use_cache:
            self.embedding_service = CachedEmbeddingService()
        else:
            self.embedding_service = EmbeddingService()

    def index_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        batch_size: int = 100,
    ) -> List[str]:
        """Index documents into the vector database"""
        if not documents:
            return []
        
        self.logger.info(f"Indexing {len(documents)} documents")
        
        # Process in batches for large document sets
        all_ids = []
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i+batch_size]
            batch_meta = metadatas[i:i+batch_size] if metadatas else None
            batch_ids = ids[i:i+batch_size] if ids else None
            
            with Timer(f"Indexing batch {i//batch_size + 1}", self.logger):
                batch_result_ids = self.database.add_documents(
                    documents=batch_docs,
                    metadatas=batch_meta,
                    ids=batch_ids,
                )
                all_ids.extend(batch_result_ids)
        
        self.logger.info(f"Successfully indexed {len(all_ids)} documents")
        return all_ids

    def search(
        self,
        query: str,
        n_results: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
        rerank: bool = False,
    ) -> List[SearchResult]:
        """Search for similar documents"""
        with Timer(f"Searching for '{query[:50]}...'", self.logger):
            # Query the database
            results = self.database.query(
                query_texts=[query],
                n_results=n_results,
                where=filter_metadata,
            )
            
            # Parse results
            search_results = self._parse_results(results, query, rerank)
        
        self.logger.info(f"Found {len(search_results)} results for query")
        return search_results

    def multi_search(
        self,
        queries: List[str],
        n_results: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
        aggregate: str = "none",
    ) -> Dict[str, List[SearchResult]]:
        """Search with multiple queries"""
        if not queries:
            return {}
        
        with Timer(f"Multi-search with {len(queries)} queries", self.logger):
            # Query the database
            results = self.database.query(
                query_texts=queries,
                n_results=n_results,
                where=filter_metadata,
            )
            
            # Parse results for each query
            all_results = {}
            for i, query in enumerate(queries):
                query_results = {
                    "ids": results["ids"][i] if results["ids"] else [],
                    "documents": results["documents"][i] if results["documents"] else [],
                    "metadatas": results["metadatas"][i] if results["metadatas"] else [],
                    "distances": results["distances"][i] if results["distances"] else [],
                }
                all_results[query] = self._parse_results(query_results, query, False)
            
            # Aggregate results if requested
            if aggregate != "none":
                all_results = self._aggregate_results(all_results, aggregate)
        
        return all_results

    def semantic_search(
        self,
        query: str,
        documents: List[str],
        n_results: int = 10,
    ) -> List[Tuple[int, float, str]]:
        """Perform semantic search on a list of documents without database"""
        if not documents:
            return []
        
        # Generate embeddings
        query_embedding = self.embedding_service.encode_queries(query)
        doc_embeddings = self.embedding_service.encode_documents(documents)
        
        # Compute similarities
        similarities = self.embedding_service.compute_similarity(
            query_embedding,
            doc_embeddings,
        )[0]
        
        # Sort by similarity
        indices_scores = [(i, score, documents[i]) 
                         for i, score in enumerate(similarities)]
        indices_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top results
        return indices_scores[:n_results]

    def find_duplicates(
        self,
        threshold: float = 0.95,
        batch_size: int = 100,
    ) -> List[Tuple[str, str, float]]:
        """Find duplicate or near-duplicate documents in the database"""
        # Get all documents
        all_docs = self.database.get_documents()
        
        if not all_docs["ids"]:
            return []
        
        duplicates = []
        doc_ids = all_docs["ids"]
        doc_texts = all_docs["documents"]
        
        # Generate embeddings for all documents
        embeddings = self.embedding_service.encode_documents(doc_texts)
        
        # Compute pairwise similarities
        similarities = self.embedding_service.compute_similarity(embeddings, embeddings)
        
        # Find duplicates
        for i in range(len(doc_ids)):
            for j in range(i + 1, len(doc_ids)):
                if similarities[i][j] >= threshold:
                    duplicates.append((
                        doc_ids[i],
                        doc_ids[j],
                        float(similarities[i][j])
                    ))
        
        self.logger.info(f"Found {len(duplicates)} duplicate pairs")
        return duplicates

    def _parse_results(
        self,
        results: Dict[str, Any],
        query: str,
        rerank: bool,
    ) -> List[SearchResult]:
        """Parse query results into SearchResult objects"""
        search_results = []
        
        # Handle empty results
        if not results.get("ids") or not results["ids"]:
            return []
        
        # For single query, results are nested
        ids = results["ids"][0] if isinstance(results["ids"][0], list) else results["ids"]
        documents = results["documents"][0] if isinstance(results["documents"][0], list) else results["documents"]
        metadatas = results["metadatas"][0] if isinstance(results["metadatas"][0], list) else results["metadatas"]
        distances = results["distances"][0] if isinstance(results["distances"][0], list) else results["distances"]
        
        for i, (doc_id, doc, meta, dist) in enumerate(zip(ids, documents, metadatas, distances)):
            # Convert distance to similarity score (1 - normalized_distance)
            score = 1.0 / (1.0 + dist) if dist else 1.0
            
            search_results.append(SearchResult(
                id=doc_id,
                document=doc,
                metadata=meta or {},
                score=score,
                rank=i + 1,
            ))
        
        # Rerank if requested
        if rerank:
            search_results = self._rerank_results(search_results, query)
        
        return search_results

    def _rerank_results(
        self,
        results: List[SearchResult],
        query: str,
    ) -> List[SearchResult]:
        """Rerank search results using cross-encoder or other methods"""
        # This is a placeholder for more sophisticated reranking
        # Could use cross-encoder models or other reranking strategies
        
        # For now, just return as-is
        return results

    def _aggregate_results(
        self,
        results: Dict[str, List[SearchResult]],
        method: str,
    ) -> Dict[str, List[SearchResult]]:
        """Aggregate results from multiple queries"""
        if method == "union":
            # Combine all unique results
            seen_ids = set()
            aggregated = []
            
            for query_results in results.values():
                for result in query_results:
                    if result.id not in seen_ids:
                        seen_ids.add(result.id)
                        aggregated.append(result)
            
            # Re-rank by average score
            aggregated.sort(key=lambda x: x.score, reverse=True)
            for i, result in enumerate(aggregated):
                result.rank = i + 1
            
            return {"aggregated": aggregated}
        
        elif method == "intersection":
            # Only keep results that appear in all queries
            if not results:
                return {}
            
            # Get IDs from first query
            common_ids = set(r.id for r in next(iter(results.values())))
            
            # Intersect with other queries
            for query_results in results.values():
                query_ids = set(r.id for r in query_results)
                common_ids &= query_ids
            
            # Filter results
            aggregated = []
            for result_list in results.values():
                for result in result_list:
                    if result.id in common_ids:
                        aggregated.append(result)
                        common_ids.remove(result.id)  # Only add once
            
            return {"aggregated": aggregated}
        
        else:
            return results

    def get_statistics(self) -> Dict[str, Any]:
        """Get search engine statistics"""
        stats = {
            "total_documents": self.database.count(),
            "collections": self.database.list_collections(),
            "embedding_model": self.embedding_service.get_model_info(),
        }
        
        # Add cache stats if using cached service
        if isinstance(self.embedding_service, CachedEmbeddingService):
            stats["cache"] = {
                "size": len(self.embedding_service.cache),
                "hits": self.embedding_service.cache_hits,
                "misses": self.embedding_service.cache_misses,
                "hit_rate": (
                    self.embedding_service.cache_hits /
                    max(1, self.embedding_service.cache_hits + self.embedding_service.cache_misses)
                ) * 100,
            }
        
        return stats