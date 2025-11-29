import chromadb
import bm25s
import logging
import os
from typing import List, Dict, Any
from src.storage.graph_manager import LocalGraph
from src.embeddings.llama_embeddings import LlamaCppEmbeddingFunction

logger = logging.getLogger(__name__)

class HybridRetriever:
    """
    Combines Vector Search, Keyword Search (BM25), and Graph Expansion.
    """
    
    def __init__(self, embedding_model_path: str = "models/bge-m3.gguf"):
        # 1. Vector Store
        self.chroma_client = chromadb.PersistentClient(path="data/chroma_db")
        
        if not os.path.exists(embedding_model_path):
             raise FileNotFoundError(f"Embedding model not found at {embedding_model_path}")
             
        self.embedding_fn = LlamaCppEmbeddingFunction(model_path=embedding_model_path)
        
        self.collection = self.chroma_client.get_collection(
            name="manuals",
            embedding_function=self.embedding_fn
        )
        
        # 2. Graph Store
        self.graph = LocalGraph()
        
        # 3. Keyword Search (BM25S)
        # Note: In a real app, you'd load a pre-built index. 
        # For this demo, we'll assume the index is built/loaded on startup or on-the-fly.
        self.retriever_bm25 = None 
        self._load_bm25()

    def _load_bm25(self):
        """Load BM25 index from disk or build it (placeholder)."""
        try:
            self.retriever_bm25 = bm25s.BM25.load("data/bm25_index", load_corpus=True)
        except FileNotFoundError:
            logger.warning("BM25 index not found. Keyword search will be disabled until indexed.")

    def search(self, query: str, k: int = 10) -> List[Dict]:
        """
        Performs hybrid search: Vector + Keyword + Graph Expansion.
        """
        results_map = {} # id -> result_dict
        
        # 1. Vector Search
        try:
            vector_res = self.collection.query(query_texts=[query], n_results=k)
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

        # 2. Keyword Search (BM25)
        if self.retriever_bm25:
            try:
                tokenized_query = bm25s.tokenize(query)
                bm25_res = self.retriever_bm25.retrieve(tokenized_query, k=k)
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
                logger.error(f"BM25 search failed: {e}")

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
