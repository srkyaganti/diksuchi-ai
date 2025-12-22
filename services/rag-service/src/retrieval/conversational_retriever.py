"""
Conversational Retriever with chat history awareness.
Handles multi-turn conversations, query rewriting, and context building.
"""
import logging
from typing import List, Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.retrieval.hybrid_retriever import HybridRetriever
    from src.retrieval.reranker import Reranker

logger = logging.getLogger(__name__)


class ConversationalRetriever:
    """
    Enhanced retriever that considers conversation history.

    Implements:
    1. Query rewriting with chat context
    2. Coreference resolution
    3. Multi-query generation
    4. Conversation-aware reranking
    """

    def __init__(
        self,
        hybrid_retriever: "HybridRetriever" = None,
        reranker: "Reranker" = None,
        ollama_model: str = "bge-m3",
        ollama_url: str = "http://localhost:11434",
        use_query_agent: bool = False  # Disabled by default to save memory
    ):
        """
        Initialize conversational retriever.
        
        Args:
            hybrid_retriever: Shared HybridRetriever instance (avoids duplicate model loading)
            reranker: Shared Reranker instance (avoids duplicate model loading)
            ollama_model: Ollama embedding model name (used if hybrid_retriever not provided)
            ollama_url: Ollama server URL
            use_query_agent: Whether to use query refinement agent (disabled by default)
        """
        # Use shared instances if provided, otherwise create new
        if hybrid_retriever is not None:
            self.hybrid_retriever = hybrid_retriever
            logger.info("Using shared HybridRetriever instance")
        else:
            from src.retrieval.hybrid_retriever import HybridRetriever
            self.hybrid_retriever = HybridRetriever(ollama_model, ollama_url)
            logger.info("Created new HybridRetriever instance")
        
        if reranker is not None:
            self.reranker = reranker
            logger.info("Using shared Reranker instance")
        else:
            from src.retrieval.reranker import Reranker
            self.reranker = Reranker(use_fp16=True)
            logger.info("Created new Reranker instance")

        # Query agent is disabled by default to save memory
        self.query_agent = None
        if use_query_agent:
            logger.info("Query agent is disabled in memory-optimized mode")

    def retrieve_with_history(
        self,
        current_query: str,
        collection_id: str,
        chat_history: List[Dict[str, str]],
        k: int = 10,
        rerank: bool = True,
        conversation_depth: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve documents considering conversation history.
        Now collection-specific for data isolation.

        Args:
            current_query: Current user query
            collection_id: Collection ID to search within
            chat_history: List of {"role": "user/assistant", "content": "..."}
            k: Number of results to return
            rerank: Whether to apply reranking
            conversation_depth: How many previous turns to consider

        Returns:
            List of retrieval results with scores and metadata
        """
        import time
        conv_start = time.time()

        # Step 1: Build contextualized query
        context_start = time.time()
        contextualized_query = self._build_contextualized_query(
            current_query,
            chat_history,
            conversation_depth
        )
        context_time = time.time() - context_start
        logger.info(f"    ├─ Contextualize query: {context_time:.3f}s")
        logger.info(f"      Original: '{current_query}'")
        logger.info(f"      Contextualized: '{contextualized_query}'")

        # Step 2: Optional query refinement (expand acronyms, add synonyms)
        refined_query = contextualized_query
        refine_time = 0
        if self.query_agent:
            refine_start = time.time()
            refined_query = self.query_agent.refine_query(contextualized_query)
            refine_time = time.time() - refine_start
            logger.info(f"    ├─ Refine query: {refine_time:.3f}s")
            logger.info(f"      Refined: '{refined_query}'")
        else:
            logger.info(f"    ├─ Refine query: skipped (no query agent)")

        # Step 3: Hybrid retrieval with expanded results pool (collection-specific)
        search_start = time.time()
        results = self.hybrid_retriever.search(
            query=refined_query,
            collection_id=collection_id,
            k=k
        )
        search_time = time.time() - search_start
        logger.info(f"    ├─ Hybrid search: {search_time:.3f}s ({len(results)} results)")

        # Step 4: Conversation-aware reranking
        rerank_time = 0
        if rerank and results:
            rerank_start = time.time()
            # Build context-aware query for reranking
            rerank_query = self._build_reranking_query(
                current_query,
                chat_history,
                conversation_depth
            )

            results = self.reranker.rerank(
                query=rerank_query,
                results=results,
                top_k=k
            )
            rerank_time = time.time() - rerank_start
            logger.info(f"    └─ Conversation-aware reranking: {rerank_time:.3f}s ({len(results)} final results)")
        else:
            logger.info(f"    └─ Reranking: skipped")

        total_time = time.time() - conv_start
        logger.info(f"  [ConversationalRetriever] Complete in {total_time:.3f}s")

        return results[:k]

    def _build_contextualized_query(
        self,
        current_query: str,
        chat_history: List[Dict[str, str]],
        conversation_depth: int = 3
    ) -> str:
        """
        Build a standalone query by incorporating recent conversation context.

        Handles coreferences like:
        - "What about its torque?" -> "What about the compressor bolt torque?"
        - "Tell me more" -> "Tell me more about hydraulic system maintenance"
        """
        if not chat_history or len(chat_history) == 0:
            return current_query

        # Get recent conversation turns (user + assistant pairs)
        recent_history = chat_history[-conversation_depth * 2:]  # Get last N turns

        # Check if current query has coreference indicators
        coreference_indicators = [
            "it", "its", "that", "this", "these", "those",
            "he", "she", "they", "the system", "the part",
            "tell me more", "what about", "how about", "and"
        ]

        has_coreference = any(
            indicator in current_query.lower()
            for indicator in coreference_indicators
        )

        if not has_coreference:
            # Query is already standalone
            return current_query

        # Build context from recent messages
        context_pieces = []
        for msg in recent_history:
            if msg["role"] == "user":
                # Extract key entities/topics from user messages
                content = msg["content"].strip()
                if len(content) > 10:  # Ignore very short messages
                    # Simple approach: take first substantive message
                    context_pieces.append(content)

        if not context_pieces:
            return current_query

        # Combine context with current query
        # Strategy: Prepend the most recent relevant context
        base_context = context_pieces[-1]  # Most recent substantive query

        # Simple heuristic: if current query starts with question words,
        # replace coreferences with base context subject
        if current_query.lower().startswith(("what", "how", "when", "where", "why")):
            # Extract subject from base context (very naive approach)
            subject_keywords = self._extract_keywords(base_context)
            if subject_keywords:
                contextualized = f"{current_query} (regarding: {' '.join(subject_keywords)})"
                return contextualized

        # Fallback: concatenate with context
        return f"{base_context} - {current_query}"

    def _extract_keywords(self, text: str, max_keywords: int = 3) -> List[str]:
        """
        Extract key technical terms from text.
        Very naive approach - in production use NER or keyword extraction model.
        """
        # Stop words to filter out
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "should",
            "could", "may", "might", "can", "i", "you", "we", "they", "it", "this",
            "that", "what", "how", "when", "where", "why", "about", "tell", "me"
        }

        # Tokenize and filter
        words = text.lower().split()
        keywords = [
            word.strip(".,?!;:()[]{}")
            for word in words
            if len(word) > 3 and word.lower() not in stop_words
        ]

        # Return first few unique keywords
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen and len(unique_keywords) < max_keywords:
                unique_keywords.append(kw)
                seen.add(kw)

        return unique_keywords

    def _build_reranking_query(
        self,
        current_query: str,
        chat_history: List[Dict[str, str]],
        conversation_depth: int = 3
    ) -> str:
        """
        Build query for reranking that includes conversation context.

        This helps the cross-encoder understand what information is relevant
        given the conversation flow.
        """
        if not chat_history or len(chat_history) == 0:
            return current_query

        # Get recent turns
        recent_history = chat_history[-conversation_depth * 2:]

        # Build context summary
        context_lines = []
        for msg in recent_history[-4:]:  # Last 2 turns (4 messages)
            role_label = "Question" if msg["role"] == "user" else "Answer"
            content = msg["content"][:100]  # Truncate for brevity
            context_lines.append(f"{role_label}: {content}")

        # Combine with current query
        context_str = " | ".join(context_lines)
        rerank_query = f"[Context: {context_str}] | Current question: {current_query}"

        return rerank_query

    def retrieve_multi_query(
        self,
        current_query: str,
        chat_history: List[Dict[str, str]],
        k: int = 10,
        num_query_variants: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple query variants and fuse results (RAG-Fusion approach).

        Args:
            current_query: Current user query
            chat_history: Conversation history
            k: Final number of results
            num_query_variants: How many variants to generate

        Returns:
            Fused and reranked results
        """
        # Base query
        queries = [current_query]

        # Generate variants if query agent is available
        if self.query_agent and num_query_variants > 1:
            # Generate paraphrases or focused versions
            # For now, use basic approach:
            contextualized = self._build_contextualized_query(
                current_query, chat_history, conversation_depth=3
            )
            queries.append(contextualized)

            # Could add more variants here (different phrasings)

        # Retrieve for each query
        all_results = {}  # doc_id -> result dict
        query_counts = {}  # doc_id -> how many queries retrieved it

        for query in queries:
            results = self.hybrid_retriever.search(query=query, k=k * 2)
            for i, result in enumerate(results):
                doc_id = result['id']
                if doc_id not in all_results:
                    all_results[doc_id] = result
                    query_counts[doc_id] = 0

                # Reciprocal Rank Fusion score
                query_counts[doc_id] += 1.0 / (i + 1)

        # Re-score based on fusion
        for doc_id, count_score in query_counts.items():
            all_results[doc_id]['score'] = count_score

        # Sort by fused score
        fused_results = list(all_results.values())
        fused_results.sort(key=lambda x: x['score'], reverse=True)

        # Final reranking with context
        if len(fused_results) > k:
            rerank_query = self._build_reranking_query(
                current_query, chat_history, conversation_depth=3
            )
            fused_results = self.reranker.rerank(
                query=rerank_query,
                results=fused_results[:k * 2],
                top_k=k
            )

        return fused_results[:k]
