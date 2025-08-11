import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from ..config import settings
from ..utils import setup_logging, generate_id, get_timestamp


class VectorDatabase:
    """ChromaDB vector database integration"""

    def __init__(
        self,
        persist_directory: Optional[Path] = None,
        collection_name: Optional[str] = None,
    ):
        self.persist_directory = persist_directory or settings.chroma_persist_directory
        self.collection_name = collection_name or settings.chroma_collection_name
        self.logger = setup_logging("VectorDatabase")
        
        # Ensure persist directory exists
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            )
        )
        
        # Initialize collection
        self.collection = None
        self._init_collection()

    def _init_collection(self):
        """Initialize or get the collection"""
        try:
            # Try to get existing collection
            self.collection = self.client.get_collection(
                name=self.collection_name,
            )
            self.logger.info(f"Loaded existing collection: {self.collection_name}")
        except Exception:
            # Create new collection if it doesn't exist
            from .embeddings import EmbeddingService
            embedding_service = EmbeddingService()
            
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=embedding_service.get_embedding_function(),
                metadata={"created": get_timestamp()},
            )
            self.logger.info(f"Created new collection: {self.collection_name}")

    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """Add documents to the vector database"""
        if not documents:
            return []
        
        # Generate IDs if not provided
        if ids is None:
            ids = [generate_id("doc") for _ in documents]
        
        # Ensure metadatas list matches documents
        if metadatas is None:
            metadatas = [{} for _ in documents]
        
        # Add timestamp to metadata
        for metadata in metadatas:
            metadata["timestamp"] = get_timestamp()
        
        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
            )
            self.logger.info(f"Added {len(documents)} documents to collection")
            return ids
        except Exception as e:
            self.logger.error(f"Error adding documents: {e}")
            raise

    def query(
        self,
        query_texts: List[str],
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        include: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Query the vector database for similar documents"""
        if not query_texts:
            return {"ids": [], "documents": [], "metadatas": [], "distances": []}
        
        # Default include fields
        if include is None:
            include = ["documents", "metadatas", "distances"]
        
        try:
            results = self.collection.query(
                query_texts=query_texts,
                n_results=n_results,
                where=where,
                include=include,
            )
            
            self.logger.info(
                f"Queried collection with {len(query_texts)} queries, "
                f"returned {len(results.get('ids', [[]])[0])} results"
            )
            return results
        except Exception as e:
            self.logger.error(f"Error querying collection: {e}")
            raise

    def get_documents(
        self,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get documents by IDs or metadata filter"""
        try:
            results = self.collection.get(
                ids=ids,
                where=where,
                limit=limit,
                include=["documents", "metadatas"],
            )
            
            self.logger.info(f"Retrieved {len(results.get('ids', []))} documents")
            return results
        except Exception as e:
            self.logger.error(f"Error getting documents: {e}")
            raise

    def update_documents(
        self,
        ids: List[str],
        documents: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """Update existing documents in the collection"""
        if not ids:
            return False
        
        try:
            # Add update timestamp
            if metadatas:
                for metadata in metadatas:
                    metadata["updated"] = get_timestamp()
            
            self.collection.update(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )
            
            self.logger.info(f"Updated {len(ids)} documents")
            return True
        except Exception as e:
            self.logger.error(f"Error updating documents: {e}")
            raise

    def delete_documents(
        self,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Delete documents from the collection"""
        if not ids and not where:
            self.logger.warning("No IDs or filter provided for deletion")
            return False
        
        try:
            self.collection.delete(
                ids=ids,
                where=where,
            )
            
            self.logger.info(f"Deleted documents from collection")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting documents: {e}")
            raise

    def count(self) -> int:
        """Get the total number of documents in the collection"""
        try:
            return self.collection.count()
        except Exception as e:
            self.logger.error(f"Error counting documents: {e}")
            return 0

    def reset_collection(self) -> bool:
        """Reset the entire collection (delete all documents)"""
        try:
            # Delete the collection
            self.client.delete_collection(name=self.collection_name)
            self.logger.info(f"Deleted collection: {self.collection_name}")
            
            # Reinitialize
            self._init_collection()
            return True
        except Exception as e:
            self.logger.error(f"Error resetting collection: {e}")
            return False

    def list_collections(self) -> List[str]:
        """List all collections in the database"""
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            self.logger.error(f"Error listing collections: {e}")
            return []

    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the current collection"""
        try:
            return {
                "name": self.collection_name,
                "count": self.count(),
                "metadata": self.collection.metadata,
                "persist_directory": str(self.persist_directory),
            }
        except Exception as e:
            self.logger.error(f"Error getting collection info: {e}")
            return {}