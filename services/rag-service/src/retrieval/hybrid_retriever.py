import chromadb
import bm25s
import logging
import os
from typing import List, Dict, Any
from src.storage.graph_manager import LocalGraph
from src.embeddings.sentence_transformer_embeddings import SentenceTransformerEmbeddingFunction
from src.quality.safety_preserver import SafetyPreserver
from src.quality.confidence_scorer import ConfidenceScorer
from src.quality.conflict_detector import ConflictDetector
from src.quality.citation_tracker import CitationTracker
from src.adaptive.hallucination_detector import HallucinationDetector
from src.adaptive.retrieval_strategy import AdaptiveRetrievalStrategy

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

        # 4. Quality gates for Phase 1 accuracy improvements
        self.safety_preserver = SafetyPreserver()
        self.confidence_scorer = ConfidenceScorer()
        self.conflict_detector = ConflictDetector(embedding_model=self.embedding_fn.model)

        # 5. Citation tracking for Phase 2
        self.citation_tracker = CitationTracker()

        # 6. Phase 4: Hallucination detection and adaptive retrieval
        self.hallucination_detector = HallucinationDetector(embedding_model=self.embedding_fn.model)
        self.adaptive_strategy = AdaptiveRetrievalStrategy()

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
        import time
        search_start = time.time()
        results_map = {} # id -> result_dict

        logger.info(f"  [HybridRetriever] Starting hybrid search for collection={collection_id}")

        # Get collection-specific ChromaDB collection
        get_collection_start = time.time()
        collection = self._get_collection(collection_id)
        get_collection_time = time.time() - get_collection_start
        logger.info(f"    ├─ Get collection: {get_collection_time:.3f}s")

        # Load BM25 index for this collection
        load_bm25_start = time.time()
        self._load_bm25(collection_id)
        load_bm25_time = time.time() - load_bm25_start
        logger.info(f"    ├─ Load BM25 index: {load_bm25_time:.3f}s")

        # 1. Vector Search (collection-specific)
        vector_search_start = time.time()
        vector_results_count = 0
        try:
            vector_res = collection.query(query_texts=[query], n_results=k)
            if vector_res['ids']:
                vector_results_count = len(vector_res['ids'][0])
                for i, doc_id in enumerate(vector_res['ids'][0]):
                    results_map[doc_id] = {
                        "id": doc_id,
                        "content": vector_res['documents'][0][i],
                        "metadata": vector_res['metadatas'][0][i],
                        "score": 1.0 / (i + 1), # Simple rank-based score
                        "source": "vector"
                    }
        except Exception as e:
            logger.error(f"    ├─ Vector search failed: {e}")
        vector_search_time = time.time() - vector_search_start
        logger.info(f"    ├─ Vector search: {vector_search_time:.3f}s ({vector_results_count} results)")

        # 2. Keyword Search (BM25) - collection-specific
        bm25_results_count = 0
        bm25_search_start = time.time()
        if collection_id in self.bm25_indices:
            try:
                retriever_bm25 = self.bm25_indices[collection_id]
                tokenized_query = bm25s.tokenize(query)
                bm25_res = retriever_bm25.retrieve(tokenized_query, k=k)
                for i, doc in enumerate(bm25_res.documents[0]):
                    doc_id = doc['id'] # Assuming corpus has IDs
                    bm25_results_count += 1
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
                logger.error(f"    ├─ BM25 search failed for collection {collection_id}: {e}")
        else:
            logger.info(f"    ├─ BM25 index not available for collection {collection_id}")
        bm25_search_time = time.time() - bm25_search_start
        logger.info(f"    ├─ BM25 search: {bm25_search_time:.3f}s ({bm25_results_count} results)")

        # 3. Graph Expansion (Safety & Context)
        graph_start = time.time()
        graph_results_count = 0
        # For the top 3 results, fetch related "Safety" or "Tool" nodes
        top_ids = sorted(results_map.keys(), key=lambda x: results_map[x]['score'], reverse=True)[:3]

        for doc_id in top_ids:
            # Example: Fetch warnings linked to this section
            warnings = self.graph.get_neighbors(doc_id, relation="HAS_WARNING")
            for w in warnings:
                if w['id'] not in results_map:
                    graph_results_count += 1
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
                    graph_results_count += 1
                    results_map[t['id']] = {
                        "id": t['id'],
                        "content": f"REQUIRED TOOL: {t['content']}",
                        "metadata": t['metadata'],
                        "score": 1.5,
                        "source": "graph_expansion"
                    }
        graph_time = time.time() - graph_start
        logger.info(f"    ├─ Graph expansion: {graph_time:.3f}s ({graph_results_count} results)")

        # Convert to list and sort
        sort_start = time.time()
        final_results = list(results_map.values())
        final_results.sort(key=lambda x: x['score'], reverse=True)
        sort_time = time.time() - sort_start
        logger.info(f"    └─ Sort & merge: {sort_time:.3f}s")

        # PHASE 1: Apply Quality Gates
        quality_gates_start = time.time()

        # Step 1: Mark safety content
        final_results = self.safety_preserver.mark_safety_content(final_results)

        # Step 2: Protect safety ranking (force safety items to top positions)
        final_results = self.safety_preserver.protect_safety_ranking(final_results, k)

        # Step 3: Score confidence and filter low-quality results
        confident_results, uncertain_results = self.confidence_scorer.filter_by_confidence(
            final_results,
            min_confidence=0.65
        )

        if uncertain_results:
            logger.info(
                f"    ├─ Confidence filtering: Filtered out {len(uncertain_results)} "
                f"low-confidence results (< 0.65)"
            )

        # Step 4: Detect and resolve conflicts (only if >5 results)
        conflicts = []
        if len(confident_results) > 5:
            conflicts = self.conflict_detector.detect_conflicts(confident_results)
            if conflicts:
                confident_results = self.conflict_detector.resolve_conflicts(
                    confident_results,
                    conflicts
                )
                logger.info(f"    ├─ Conflict resolution: Resolved {len(conflicts)} conflicts")

        # Step 5: Validate safety preservation
        safety_validation = self.safety_preserver.ensure_safety_in_final_results(
            confident_results, min_safety_items=1
        )
        if not safety_validation["has_sufficient_safety"]:
            logger.warning(safety_validation.get("warning", "Insufficient safety items"))

        quality_gates_time = time.time() - quality_gates_start
        logger.info(f"    └─ Quality gates: {quality_gates_time:.3f}s")

        # Log detailed analysis
        self.safety_preserver.log_safety_analysis(confident_results)
        self.confidence_scorer.log_confidence_analysis(confident_results)
        if conflicts:
            self.conflict_detector.log_conflict_analysis(conflicts, final_results)

        # PHASE 2: Add citations to results
        citation_start = time.time()
        final_results_with_citations = self.citation_tracker.enrich_with_citations(
            confident_results[:k*2]
        )
        self.citation_tracker.log_citation_analysis(final_results_with_citations)
        citation_time = time.time() - citation_start
        logger.info(f"    └─ Citation enrichment: {citation_time:.3f}s")

        total_time = time.time() - search_start
        final_count = len(final_results_with_citations)
        logger.info(
            f"  [HybridRetriever] Complete in {total_time:.3f}s, "
            f"returning {final_count} results with citations ({len(confident_results)} after quality gates)"
        )

        return final_results_with_citations # Return with citation metadata

    def check_and_adapt_strategy(
        self, query: str, initial_results: List[Dict], collection_id: str, max_retries: int = 2
    ) -> List[Dict]:
        """
        Phase 4: Evaluate initial results and adapt retrieval strategy if needed.

        If initial results have low average confidence, escalates to more aggressive
        retrieval strategies (expanded query, decomposed query, fallback).

        Args:
            query: Original query
            initial_results: Initial retrieval results
            collection_id: Collection ID for context
            max_retries: Maximum adaptive retry attempts

        Returns:
            Final results after adaptive strategy if needed, or initial results
        """
        # Evaluate initial results quality
        result_quality = self.adaptive_strategy._evaluate_results(initial_results)
        assessment = result_quality.get("quality_assessment", "good")

        logger.info(f"  [Phase 4 Adaptive] Result quality: {assessment} (avg_confidence: {result_quality['avg_confidence']:.2f})")

        # If results are good or excellent, return as-is
        if assessment in ["good", "excellent"]:
            self.adaptive_strategy.log_strategy_selection({
                "strategy": "STANDARD",
                "rationale": f"Initial results {assessment}",
                "queries": [query]
            })
            return initial_results

        # Results are poor or marginal, attempt adaptive retrieval
        current_strategy = "STANDARD"
        retry_count = 0
        current_results = initial_results

        while retry_count < max_retries:
            # Select adapted strategy
            new_strategy = self.adaptive_strategy.adapt_strategy(
                current_strategy, retry_count, result_quality
            )

            if not new_strategy:
                logger.info(f"  [Phase 4 Adaptive] Max retries reached, returning current results")
                break

            # Generate adapted queries
            adapted_queries = self.adaptive_strategy._generate_queries(new_strategy, query)

            logger.info(f"  [Phase 4 Adaptive] Retry {retry_count + 1}: Escalating to {new_strategy} strategy with {len(adapted_queries)} query variants")

            # Execute adapted queries (simplified - just try first adapted query)
            if len(adapted_queries) > 1:
                adapted_query = adapted_queries[1]  # Use first adapted variant
                try:
                    adapted_results = self.search(adapted_query, collection_id, k=10)
                    adapted_quality = self.adaptive_strategy._evaluate_results(adapted_results)

                    logger.info(f"  [Phase 4 Adaptive] Adapted results: {adapted_quality['quality_assessment']} (avg_confidence: {adapted_quality['avg_confidence']:.2f})")

                    # If adapted results are better, use them
                    if adapted_quality["avg_confidence"] > result_quality["avg_confidence"]:
                        current_results = adapted_results
                        result_quality = adapted_quality
                        logger.info(f"  [Phase 4 Adaptive] Accepting improved results")

                        if adapted_quality["quality_assessment"] in ["good", "excellent"]:
                            break

                except Exception as e:
                    logger.warning(f"  [Phase 4 Adaptive] Error executing adapted query: {e}")

            current_strategy = new_strategy
            retry_count += 1

        return current_results

    def validate_response_faithfulness(
        self, llm_response: str, retrieved_context: List[Dict]
    ) -> Dict[str, Any]:
        """
        Phase 4: Validate that LLM response is faithful to retrieved context.

        Checks if claims in the response are supported by the provided context.
        Detects hallucinations where LLM invents unsupported information.

        Args:
            llm_response: The LLM-generated response
            retrieved_context: List of retrieved context documents

        Returns:
            {
                'is_faithful': bool,
                'faithfulness_score': float (0-1),
                'total_claims': int,
                'supported_claims': int,
                'unsupported_claims': List[str],
                'confidence': str (HIGH/MEDIUM/LOW),
                'recommendation': str
            }
        """
        # Extract context text from retrieval results
        context_chunks = [r.get("content", "") for r in retrieved_context if r.get("content")]

        # Check faithfulness
        faithfulness_result = self.hallucination_detector.check_faithfulness(
            llm_response, context_chunks
        )

        # Add recommendation
        if faithfulness_result["is_faithful"]:
            recommendation = "Response is faithful to retrieved context. Safe to present to user."
        elif faithfulness_result["faithfulness_score"] >= 0.60:
            recommendation = "Response has some unsupported claims. Review before presenting to user."
        else:
            recommendation = "Response has significant unsupported claims. Do not present to user without verification."

        faithfulness_result["recommendation"] = recommendation

        # Log analysis
        self.hallucination_detector.log_hallucination_analysis(
            faithfulness_result,
            response_preview=llm_response[:100]
        )

        return faithfulness_result
