#!/usr/bin/env python
"""
Example client for vector search functionality
"""

import asyncio
import aiohttp
import json
from typing import List, Dict, Any


class VectorSearchClient:
    """Client for vector search operations via MCP Server API"""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.api_prefix = "/api/v1"
        self.headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
    
    async def embed_text(self, session: aiohttp.ClientSession, text: str) -> List[float]:
        """Generate embedding for text"""
        url = f"{self.base_url}{self.api_prefix}/vectors/embed"
        payload = {"text": text}
        
        async with session.post(url, json=payload, headers=self.headers) as response:
            response.raise_for_status()
            result = await response.json()
            return result["embedding"]
    
    async def index_document(self, session: aiohttp.ClientSession, document: Dict) -> Dict:
        """Index a document for vector search"""
        url = f"{self.base_url}{self.api_prefix}/vectors/index"
        
        async with session.post(url, json=document, headers=self.headers) as response:
            response.raise_for_status()
            return await response.json()
    
    async def search(self, session: aiohttp.ClientSession, 
                     query: str, 
                     limit: int = 5,
                     threshold: float = 0.7) -> List[Dict]:
        """Search for similar documents"""
        url = f"{self.base_url}{self.api_prefix}/vectors/search"
        payload = {
            "query": query,
            "limit": limit,
            "threshold": threshold
        }
        
        async with session.post(url, json=payload, headers=self.headers) as response:
            response.raise_for_status()
            result = await response.json()
            return result["results"]
    
    async def search_with_filter(self, session: aiohttp.ClientSession,
                                 query: str,
                                 filters: Dict,
                                 limit: int = 5) -> List[Dict]:
        """Search with metadata filters"""
        url = f"{self.base_url}{self.api_prefix}/vectors/search"
        payload = {
            "query": query,
            "filters": filters,
            "limit": limit
        }
        
        async with session.post(url, json=payload, headers=self.headers) as response:
            response.raise_for_status()
            result = await response.json()
            return result["results"]


async def main():
    """Example usage of vector search client"""
    
    # Initialize client
    client = VectorSearchClient()
    
    async with aiohttp.ClientSession() as session:
        print("Vector Search Client Example")
        print("=" * 50)
        
        # Step 1: Index sample documents
        print("\n1. Indexing documents...")
        
        documents = [
            {
                "id": "doc001",
                "title": "Introduction to Machine Learning",
                "content": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It focuses on developing computer programs that can access data and use it to learn for themselves.",
                "metadata": {
                    "category": "AI/ML",
                    "author": "John Doe",
                    "year": 2024,
                    "tags": ["machine learning", "AI", "introduction"]
                }
            },
            {
                "id": "doc002",
                "title": "Deep Learning Fundamentals",
                "content": "Deep learning is a subset of machine learning that uses neural networks with multiple layers. These neural networks attempt to simulate the behavior of the human brain, allowing it to learn from large amounts of data.",
                "metadata": {
                    "category": "AI/ML",
                    "author": "Jane Smith",
                    "year": 2024,
                    "tags": ["deep learning", "neural networks", "AI"]
                }
            },
            {
                "id": "doc003",
                "title": "Natural Language Processing",
                "content": "Natural Language Processing (NLP) is a branch of AI that helps computers understand, interpret and manipulate human language. NLP draws from many disciplines including computational linguistics and machine learning.",
                "metadata": {
                    "category": "NLP",
                    "author": "Bob Johnson",
                    "year": 2023,
                    "tags": ["NLP", "linguistics", "text processing"]
                }
            },
            {
                "id": "doc004",
                "title": "Computer Vision Applications",
                "content": "Computer vision is a field of AI that trains computers to interpret and understand the visual world. Using digital images from cameras and deep learning models, machines can identify and classify objects.",
                "metadata": {
                    "category": "Computer Vision",
                    "author": "Alice Brown",
                    "year": 2024,
                    "tags": ["computer vision", "image processing", "AI"]
                }
            },
            {
                "id": "doc005",
                "title": "Reinforcement Learning in Robotics",
                "content": "Reinforcement learning is a type of machine learning where an agent learns to make decisions by performing actions and receiving rewards. It's widely used in robotics for teaching robots to perform complex tasks.",
                "metadata": {
                    "category": "Robotics",
                    "author": "Charlie Wilson",
                    "year": 2023,
                    "tags": ["reinforcement learning", "robotics", "decision making"]
                }
            }
        ]
        
        for doc in documents:
            try:
                result = await client.index_document(session, doc)
                print(f"  Indexed: {doc['title']} (ID: {result.get('id', doc['id'])})")
            except Exception as e:
                print(f"  Error indexing {doc['title']}: {e}")
        
        # Wait a moment for indexing to complete
        await asyncio.sleep(2)
        
        # Step 2: Perform semantic searches
        print("\n2. Performing semantic searches...")
        
        queries = [
            "How do neural networks work?",
            "What is artificial intelligence?",
            "Understanding human language with computers",
            "Teaching robots to learn",
            "Image recognition and classification"
        ]
        
        for query in queries:
            print(f"\n  Query: '{query}'")
            results = await client.search(session, query, limit=3)
            
            if results:
                print("  Results:")
                for i, result in enumerate(results, 1):
                    print(f"    {i}. {result.get('title', 'Unknown')} (Score: {result.get('score', 0):.3f})")
                    if result.get('metadata'):
                        print(f"       Category: {result['metadata'].get('category', 'N/A')}")
            else:
                print("  No results found")
        
        # Step 3: Search with filters
        print("\n3. Searching with metadata filters...")
        
        print("\n  Filter: category='AI/ML' AND year=2024")
        filtered_results = await client.search_with_filter(
            session,
            query="machine learning concepts",
            filters={
                "category": "AI/ML",
                "year": 2024
            },
            limit=5
        )
        
        if filtered_results:
            print("  Results:")
            for result in filtered_results:
                print(f"    - {result.get('title', 'Unknown')}")
                print(f"      Author: {result.get('metadata', {}).get('author', 'N/A')}")
                print(f"      Year: {result.get('metadata', {}).get('year', 'N/A')}")
        else:
            print("  No results found")
        
        # Step 4: Generate embeddings for comparison
        print("\n4. Generating embeddings for text comparison...")
        
        texts = [
            "Machine learning and artificial intelligence",
            "Deep neural networks",
            "Computer vision and image processing"
        ]
        
        embeddings = []
        for text in texts:
            embedding = await client.embed_text(session, text)
            embeddings.append(embedding)
            print(f"  Generated embedding for: '{text}' (dimension: {len(embedding)})")
        
        # Calculate similarity between first two embeddings
        if len(embeddings) >= 2:
            import numpy as np
            
            # Cosine similarity
            def cosine_similarity(a, b):
                return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
            
            similarity = cosine_similarity(
                np.array(embeddings[0]), 
                np.array(embeddings[1])
            )
            print(f"\n  Similarity between first two texts: {similarity:.3f}")


if __name__ == "__main__":
    asyncio.run(main())