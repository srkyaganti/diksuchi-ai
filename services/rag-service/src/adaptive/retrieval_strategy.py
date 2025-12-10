"""
Adaptive retrieval strategy selection and execution.

Selects and applies appropriate retrieval strategies based on:
- Query characteristics (complexity, type)
- Initial retrieval results (confidence, coverage)
- Collection quality metrics
"""

import logging
from typing import List, Dict, Any, Optional

from .query_analyzer import QueryAnalyzer
from .query_expander import QueryExpander
from .query_decomposer import QueryDecomposer

logger = logging.getLogger(__name__)


class AdaptiveRetrievalStrategy:
    """Selects and applies adaptive retrieval strategies."""

    # Strategy definitions
    STRATEGIES = {
        "STANDARD": {
            "description": "Direct hybrid search",
            "confidence_threshold": 0.65,
            "max_retries": 1,
        },
        "EXPANDED": {
            "description": "Add synonyms and related terms",
            "confidence_threshold": 0.50,
            "max_retries": 2,
        },
        "DECOMPOSED": {
            "description": "Break into sub-queries",
            "confidence_threshold": 0.50,
            "max_retries": 2,
        },
        "FALLBACK": {
            "description": "Aggressive expansion + lowered threshold",
            "confidence_threshold": 0.40,
            "max_retries": 3,
        },
    }

    def __init__(self):
        """Initialize adaptive strategy components."""
        self.analyzer = QueryAnalyzer()
        self.expander = QueryExpander()
        self.decomposer = QueryDecomposer()

    def select_strategy(
        self,
        query: str,
        initial_results: Optional[List[Dict]] = None,
        collection_metrics: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Select retrieval strategy based on query and results.

        Args:
            query: Original query
            initial_results: Initial retrieval results (optional)
            collection_metrics: Collection quality metrics (optional)

        Returns:
            {
                'strategy': str (STANDARD/EXPANDED/DECOMPOSED/FALLBACK),
                'queries': List[str] (queries to execute),
                'parameters': Dict (strategy parameters),
                'rationale': str
            }
        """
        # Analyze query
        analysis = self.analyzer.analyze(query)

        # Evaluate initial results if provided
        result_quality = None
        if initial_results:
            result_quality = self._evaluate_results(initial_results)

        # Determine strategy
        strategy, rationale = self._choose_strategy(
            analysis, result_quality, collection_metrics
        )

        # Generate queries for strategy
        queries = self._generate_queries(strategy, query)

        result = {
            "strategy": strategy,
            "queries": queries,
            "parameters": self.STRATEGIES[strategy],
            "rationale": rationale,
        }

        logger.info(f"Selected strategy: {strategy} - {rationale}")
        return result

    def _evaluate_results(self, results: List[Dict]) -> Dict[str, Any]:
        """
        Evaluate quality of retrieval results.

        Args:
            results: Retrieval results

        Returns:
            {
                'avg_confidence': float,
                'coverage': float,
                'quality_assessment': str
            }
        """
        if not results:
            return {"avg_confidence": 0.0, "coverage": 0.0, "quality_assessment": "empty"}

        confidences = [r.get("confidence", 0.5) for r in results]
        avg_confidence = sum(confidences) / len(confidences)

        # Count high-confidence results
        high_confidence_count = sum(1 for c in confidences if c >= 0.75)
        coverage = high_confidence_count / len(results)

        # Assess quality
        if avg_confidence >= 0.80:
            assessment = "excellent"
        elif avg_confidence >= 0.65:
            assessment = "good"
        elif avg_confidence >= 0.50:
            assessment = "marginal"
        else:
            assessment = "poor"

        return {
            "avg_confidence": avg_confidence,
            "coverage": coverage,
            "quality_assessment": assessment,
        }

    def _choose_strategy(
        self,
        analysis: Dict[str, Any],
        result_quality: Optional[Dict[str, Any]],
        collection_metrics: Optional[Dict[str, float]],
    ) -> tuple:
        """
        Choose strategy based on analysis.

        Args:
            analysis: Query analysis result
            result_quality: Result quality evaluation
            collection_metrics: Collection metrics

        Returns:
            (strategy, rationale) tuple
        """
        complexity = analysis.get("complexity", "MODERATE")
        query_type = analysis.get("query_type", "general")
        is_multi_part = analysis.get("is_multi_part", False)
        recommended = analysis.get("recommended_retrieval_strategy", "STANDARD")

        # If results are poor, escalate strategy
        if result_quality:
            assessment = result_quality.get("quality_assessment", "good")
            if assessment == "poor":
                return "FALLBACK", "Initial results poor, using aggressive fallback"
            elif assessment == "marginal":
                if recommended in ["DECOMPOSED", "EXPANDED"]:
                    return recommended, f"Initial results marginal, using {recommended}"
                else:
                    return "EXPANDED", "Initial results marginal, expanding query"

        # Based on query analysis
        if complexity == "COMPLEX" and is_multi_part:
            return "DECOMPOSED", "Complex multi-part query, decomposing into sub-queries"

        if complexity == "COMPLEX" and not is_multi_part:
            return "EXPANDED", "Complex single-part query, expanding with synonyms"

        if query_type in ["specification", "troubleshooting"]:
            return "EXPANDED", f"Query type {query_type} benefits from expansion"

        # Default
        return "STANDARD", "Using standard hybrid retrieval"

    def _generate_queries(self, strategy: str, query: str) -> List[str]:
        """
        Generate query variants based on strategy.

        Args:
            strategy: Selected strategy
            query: Original query

        Returns:
            List of queries to execute
        """
        if strategy == "STANDARD":
            return [query]

        elif strategy == "EXPANDED":
            # Generate synonym variants
            expanded = self.expander.expand_query(query, num_variants=2)
            return expanded

        elif strategy == "DECOMPOSED":
            # Decompose into sub-queries
            decomposition = self.decomposer.decompose(query)
            if decomposition.get("is_decomposed"):
                return decomposition.get("sub_queries", [query])
            else:
                # If can't decompose, fall back to expansion
                return self.expander.expand_query(query, num_variants=2)

        elif strategy == "FALLBACK":
            # Aggressive: both expansion and decomposition
            expanded = self.expander.expand_query(query, num_variants=2)
            decomposition = self.decomposer.decompose(query)
            if decomposition.get("is_decomposed"):
                all_queries = expanded + decomposition.get("sub_queries", [])
            else:
                all_queries = expanded

            # Return unique queries
            return list(dict.fromkeys(all_queries))

        return [query]

    def adapt_strategy(
        self, initial_strategy: str, retry_count: int, result_quality: Dict
    ) -> Optional[str]:
        """
        Adapt strategy if initial attempt didn't succeed.

        Args:
            initial_strategy: Initially selected strategy
            retry_count: Number of retries so far
            result_quality: Quality of last attempt

        Returns:
            New strategy or None if should give up
        """
        assessment = result_quality.get("quality_assessment", "poor")

        # Already at FALLBACK, no further escalation
        if initial_strategy == "FALLBACK":
            if retry_count >= self.STRATEGIES["FALLBACK"]["max_retries"]:
                return None

            return "FALLBACK"

        # Escalation path
        escalation_path = {
            "STANDARD": "EXPANDED",
            "EXPANDED": "DECOMPOSED",
            "DECOMPOSED": "FALLBACK",
        }

        if assessment in ["poor", "marginal"]:
            max_retries = self.STRATEGIES[initial_strategy]["max_retries"]
            if retry_count < max_retries:
                return escalation_path.get(initial_strategy)

        return None

    def log_strategy_selection(self, selection: Dict[str, Any]) -> None:
        """
        Log strategy selection details.

        Args:
            selection: Strategy selection result
        """
        logger.info("=" * 70)
        logger.info("ADAPTIVE RETRIEVAL STRATEGY")
        logger.info("=" * 70)
        logger.info(f"Strategy: {selection.get('strategy')}")
        logger.info(f"Rationale: {selection.get('rationale')}")
        logger.info(f"Queries ({len(selection.get('queries', []))}):")
        for i, q in enumerate(selection.get("queries", []), 1):
            logger.info(f"  [{i}] {q}")
        logger.info("=" * 70)
