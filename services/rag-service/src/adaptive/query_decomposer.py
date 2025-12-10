"""
Query decomposition module for breaking complex queries into sub-queries.

Splits multi-part queries into simpler sub-queries for better retrieval.
"""

import logging
import re
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class QueryDecomposer:
    """Decomposes complex queries into sub-queries."""

    def __init__(self):
        """Initialize query decomposer."""
        pass

    def decompose(self, query: str) -> Dict[str, Any]:
        """
        Decompose query into sub-queries.

        Identifies conjunctions and splits into separate sub-queries.

        Args:
            query: Original query

        Returns:
            {
                'original_query': str,
                'is_decomposed': bool,
                'sub_queries': List[str],
                'conjunction_type': str (AND/OR/SEQUENTIAL),
                'strategy': str (SEQUENTIAL/PARALLEL)
            }
        """
        # Check if query needs decomposition
        if not self._needs_decomposition(query):
            return {
                "original_query": query,
                "is_decomposed": False,
                "sub_queries": [query],
                "conjunction_type": None,
                "strategy": "STANDARD",
            }

        # Identify conjunction type
        conjunction_type = self._identify_conjunction(query)

        # Split by conjunction
        sub_queries = self._split_by_conjunction(query)

        # Clean sub-queries
        sub_queries = [q.strip() for q in sub_queries if q.strip()]

        # Determine strategy (how to combine results)
        strategy = self._determine_strategy(conjunction_type)

        result = {
            "original_query": query,
            "is_decomposed": len(sub_queries) > 1,
            "sub_queries": sub_queries,
            "conjunction_type": conjunction_type,
            "strategy": strategy,
        }

        logger.debug(f"Decomposed query into {len(sub_queries)} sub-queries")
        return result

    def _needs_decomposition(self, query: str) -> bool:
        """
        Check if query should be decomposed.

        Returns True for multi-part queries.

        Args:
            query: Query text

        Returns:
            True if decomposition recommended
        """
        query_lower = query.lower()

        # Multiple questions
        if query.count("?") > 1:
            return True

        # "and" or "or" with different question words
        if re.search(
            r'\b(how|what|why|when|where|who)\b.*\b(and|or)\b.*\b(how|what|why|when|where|who)\b',
            query_lower,
        ):
            return True

        # Sequential indicators
        if re.search(r'\b(then|after|before|followed by)\b', query_lower):
            return True

        return False

    def _identify_conjunction(self, query: str) -> str:
        """
        Identify type of conjunction between query parts.

        Args:
            query: Query text

        Returns:
            SEQUENTIAL, AND, OR, or None
        """
        query_lower = query.lower()

        # Sequential
        if re.search(r'\b(then|after|before|followed by|subsequently)\b', query_lower):
            return "SEQUENTIAL"

        # OR (alternative)
        if re.search(r'\b(or|either|alternatively)\b', query_lower):
            return "OR"

        # AND (both required)
        if re.search(r'\b(and|both|also)\b', query_lower):
            return "AND"

        return None

    def _split_by_conjunction(self, query: str) -> List[str]:
        """
        Split query by conjunctions.

        Args:
            query: Query text

        Returns:
            List of sub-queries
        """
        # Split by "and"
        if " and " in query.lower():
            parts = re.split(r'\s+and\s+', query, flags=re.IGNORECASE)
            if len(parts) > 1:
                return parts

        # Split by "or"
        if " or " in query.lower():
            parts = re.split(r'\s+or\s+', query, flags=re.IGNORECASE)
            if len(parts) > 1:
                return parts

        # Split by sequential markers
        sequential_markers = [
            r'then',
            r'after\s+that',
            r'followed\s+by',
            r'\?[^?]*\?',  # Multiple questions
        ]

        for marker in sequential_markers:
            parts = re.split(marker, query, flags=re.IGNORECASE)
            if len(parts) > 1:
                return parts

        # Default: return original
        return [query]

    def _determine_strategy(self, conjunction_type: str) -> str:
        """
        Determine how to combine results from sub-queries.

        PARALLEL: All sub-queries independent, combine results
        SEQUENTIAL: Run sub-queries in order, use previous results

        Args:
            conjunction_type: Type of conjunction

        Returns:
            Strategy string
        """
        if conjunction_type == "SEQUENTIAL":
            return "SEQUENTIAL"
        else:
            return "PARALLEL"

    def recompose_results(
        self,
        sub_query_results: List[Dict[str, Any]],
        strategy: str,
        conjunction_type: str,
    ) -> List[Dict[str, Any]]:
        """
        Recompose results from sub-queries based on strategy.

        For AND: Return documents in all result sets
        For OR: Return union of all documents
        For SEQUENTIAL: Combine results in order

        Args:
            sub_query_results: List of result dicts from each sub-query
            strategy: Combination strategy
            conjunction_type: Type of conjunction

        Returns:
            Combined results
        """
        if not sub_query_results:
            return []

        if strategy == "SEQUENTIAL":
            # For sequential, just concatenate
            # (earlier queries inform later ones)
            all_results = []
            for results in sub_query_results:
                all_results.extend(results)
            return all_results

        # PARALLEL strategy
        if conjunction_type == "AND":
            # Return only documents in all result sets
            return self._intersection_results(sub_query_results)
        elif conjunction_type == "OR":
            # Return union of all documents
            return self._union_results(sub_query_results)
        else:
            # Default: union
            return self._union_results(sub_query_results)

    def _intersection_results(self, result_sets: List[List[Dict]]) -> List[Dict]:
        """
        Get intersection of results (documents in all sets).

        Args:
            result_sets: List of result lists

        Returns:
            Intersection of all results
        """
        if not result_sets:
            return []

        # Get doc IDs in all result sets
        id_sets = [set(r.get("id") for r in rs) for rs in result_sets]
        common_ids = set.intersection(*id_sets) if id_sets else set()

        # Return docs with IDs in intersection
        result_map = {}
        for rs in result_sets:
            for r in rs:
                if r.get("id") in common_ids:
                    result_map[r.get("id")] = r

        return list(result_map.values())

    def _union_results(self, result_sets: List[List[Dict]]) -> List[Dict]:
        """
        Get union of results (all unique documents).

        Args:
            result_sets: List of result lists

        Returns:
            Union of all results
        """
        result_map = {}
        for rs in result_sets:
            for r in rs:
                doc_id = r.get("id")
                if doc_id not in result_map:
                    result_map[doc_id] = r

        return list(result_map.values())

    def log_decomposition(self, decomposition: Dict[str, Any]) -> None:
        """
        Log query decomposition results.

        Args:
            decomposition: Decomposition result dict
        """
        logger.debug("=" * 60)
        logger.debug("QUERY DECOMPOSITION:")
        logger.debug(f"  Original: {decomposition.get('original_query')}")
        logger.debug(f"  Decomposed: {decomposition.get('is_decomposed')}")
        if decomposition.get("is_decomposed"):
            logger.debug(f"  Conjunction: {decomposition.get('conjunction_type')}")
            logger.debug(f"  Strategy: {decomposition.get('strategy')}")
            logger.debug(f"  Sub-queries ({len(decomposition.get('sub_queries', []))}):")
            for i, sq in enumerate(decomposition.get("sub_queries", []), 1):
                logger.debug(f"    [{i}] {sq}")
        logger.debug("=" * 60)
