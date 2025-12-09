import chromadb
import bm25s
import logging
import os
from typing import List, Dict, Any
from src.storage.graph_manager import LocalGraph
from src.embeddings.sentence_transformer_embeddings import SentenceTransformerEmbeddingFunction

logger = logging.getLogger(__name__)

class HybridRetriever:
    """
    Combines Vector Search, Keyword Search (BM25), and Graph Expansion.
    Now supports collection-specific retrieval for data isolation.
    """

    def __init__(self, embedding_model_path: str = "models/bge-m3"):
        # 1. Vector Store Client (collections accessed per-query)
        self.chroma_client = chromadb.PersistentClient(path="data/chroma_db")

        if not os.path.exists(embedding_model_path):
             raise FileNotFoundError(f"Embedding model not found at {embedding_model_path}")

        self.embedding_fn = SentenceTransformerEmbeddingFunction(
            model_name_or_path=embedding_model_path
        )

        # Don't create a default collection - collections are accessed per query
        # This ensures data isolation between organizations

        # 2. Graph Store
        self.graph = LocalGraph()

        # 3. Keyword Search (BM25S) - now collection-specific
        # BM25 indices are loaded per collection
        self.bm25_indices = {}  # collection_id -> BM25 retriever

    def _get_collection(self, collection_id: str):
        """
        Get a ChromaDB collection specific to the given collectionId.

        Args:
            collection_id: The collection ID from the web application

        Returns:
            ChromaDB collection instance
        """
        collection_name = f"collection_{collection_id}"
        logger.info(f"Retrieving from ChromaDB collection: {collection_name}")

        try:
            return self.chroma_client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_fn
            )
        except Exception as e:
            logger.error(f"Collection {collection_name} not found: {e}")
            raise ValueError(f"Collection {collection_id} not found or not yet indexed")

    def _load_bm25(self, collection_id: str):
        """Load BM25 index for a specific collection."""
        if collection_id in self.bm25_indices:
            return  # Already loaded

        index_path = f"data/bm25_index/collection_{collection_id}"
        try:
            self.bm25_indices[collection_id] = bm25s.BM25.load(index_path, load_corpus=True)
            logger.info(f"Loaded BM25 index for collection {collection_id}")
        except FileNotFoundError:
            logger.warning(f"BM25 index not found for collection {collection_id}. Keyword search will be disabled.")

    def search(self, query: str, collection_id: str, k: int = 10) -> List[Dict]:
        """
        Performs hybrid search: Vector + Keyword + Graph Expansion.
        Now collection-specific for data isolation.

        Args:
            query: Search query
            collection_id: Collection ID to search within
            k: Number of results to return

        Returns:
            List of search results with scores
        """
        results_map = {} # id -> result_dict

        # Get collection-specific ChromaDB collection
        collection = self._get_collection(collection_id)

        # Load BM25 index for this collection
        self._load_bm25(collection_id)

        # 1. Vector Search (collection-specific)
        try:
            vector_res = collection.query(query_texts=[query], n_results=k)
            if vector_res['ids']:
                for i, doc_id in enumerate(vector_res['ids'][0]):
                    results_map[doc_id] = {
                        "id": doc_id,
                        "content": vector_res['documents'][0][i],
                        "metadata": vector_res['metadatas'][0][i],
                        "score": 1.0 / (i + 1), # Simple rank-based score
                        "source": "vector"
                    }
        except Exception as e:
            logger.error(f"Vector search failed: {e}")

        # 2. Keyword Search (BM25) - collection-specific
        if collection_id in self.bm25_indices:
            try:
                retriever_bm25 = self.bm25_indices[collection_id]
                tokenized_query = bm25s.tokenize(query)
                bm25_res = retriever_bm25.retrieve(tokenized_query, k=k)
                for i, doc in enumerate(bm25_res.documents[0]):
                    doc_id = doc['id'] # Assuming corpus has IDs
                    if doc_id not in results_map:
                        results_map[doc_id] = {
                            "id": doc_id,
                            "content": doc['text'],
                            "metadata": doc['metadata'],
                            "score": 0,
                            "source": "keyword"
                        }
                    results_map[doc_id]["score"] += 1.0 / (i + 1) # RRF-like addition
            except Exception as e:
                logger.error(f"BM25 search failed for collection {collection_id}: {e}")

        # 3. Graph Expansion (Safety & Context)
        # For the top 3 results, fetch related "Safety" or "Tool" nodes
        top_ids = sorted(results_map.keys(), key=lambda x: results_map[x]['score'], reverse=True)[:3]
        
        for doc_id in top_ids:
            # Example: Fetch warnings linked to this section
            warnings = self.graph.get_neighbors(doc_id, relation="HAS_WARNING")
            for w in warnings:
                if w['id'] not in results_map:
                    results_map[w['id']] = {
                        "id": w['id'],
                        "content": f"WARNING: {w['content']}", # Emphasize warning
                        "metadata": w['metadata'],
                        "score": 2.0, # High priority for safety
                        "source": "graph_expansion"
                    }
                    
            # Example: Fetch required tools
            tools = self.graph.get_neighbors(doc_id, relation="REQUIRES_TOOL")
            for t in tools:
                 if t['id'] not in results_map:
                    results_map[t['id']] = {
                        "id": t['id'],
                        "content": f"REQUIRED TOOL: {t['content']}",
                        "metadata": t['metadata'],
                        "score": 1.5,
                        "source": "graph_expansion"
                    }

        # Convert to list and sort
        final_results = list(results_map.values())
        final_results.sort(key=lambda x: x['score'], reverse=True)
        
        return final_results[:k*2] # Return expanded pool for reranking
