"""
Standard Information Retrieval metrics for RAG evaluation.

Implements industry-standard metrics:
- Precision@k: Percentage of retrieved items that are relevant
- Recall@k: Percentage of relevant items that are retrieved
- Mean Reciprocal Rank (MRR): Average rank of first relevant item
- Normalized Discounted Cumulative Gain (nDCG): Ranking quality metric
"""

import logging
import math
from typing import List, Dict, Set, Optional, Tuple

logger = logging.getLogger(__name__)


class RetrievalMetrics:
    """Computes standard IR metrics for retrieval evaluation."""

    @staticmethod
    def precision_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
        """
        Compute Precision@k: (# relevant in top-k) / k

        Measures: Of the top-k results, how many are relevant?
        Range: 0.0-1.0 (higher is better)

        Args:
            retrieved_ids: List of retrieved document IDs (ordered by relevance)
            relevant_ids: Set of truly relevant document IDs
            k: Cutoff rank (evaluate top-k results)

        Returns:
            Precision@k score
        """
        if k <= 0:
            return 0.0

        # Count relevant items in top-k
        top_k = set(retrieved_ids[:k])
        num_relevant_in_top_k = len(top_k & relevant_ids)

        # Precision = relevant / k
        precision = num_relevant_in_top_k / k

        return precision

    @staticmethod
    def recall_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
        """
        Compute Recall@k: (# relevant in top-k) / (# total relevant)

        Measures: Of all relevant items, how many did we retrieve?
        Range: 0.0-1.0 (higher is better)

        Args:
            retrieved_ids: List of retrieved document IDs (ordered)
            relevant_ids: Set of truly relevant document IDs
            k: Cutoff rank

        Returns:
            Recall@k score
        """
        if not relevant_ids:
            return 1.0  # No relevant items means perfect recall

        # Count relevant items in top-k
        top_k = set(retrieved_ids[:k])
        num_relevant_in_top_k = len(top_k & relevant_ids)

        # Recall = relevant / total_relevant
        recall = num_relevant_in_top_k / len(relevant_ids)

        return recall

    @staticmethod
    def mean_reciprocal_rank(
        retrieved_ids: List[str], relevant_ids: Set[str]
    ) -> float:
        """
        Compute Mean Reciprocal Rank (MRR): 1 / (rank of first relevant item)

        Measures: How quickly does the first relevant item appear?
        Range: 0.0-1.0 (higher is better, 1.0 = first result is relevant)

        Args:
            retrieved_ids: List of retrieved document IDs (ordered)
            relevant_ids: Set of truly relevant document IDs

        Returns:
            MRR score
        """
        # Find rank of first relevant item (1-indexed)
        for rank, doc_id in enumerate(retrieved_ids, 1):
            if doc_id in relevant_ids:
                return 1.0 / rank

        # No relevant item found
        return 0.0

    @staticmethod
    def ndcg_at_k(
        retrieved_ids: List[str],
        relevance_scores: Dict[str, int],
        k: int,
        ideal_ranking: Optional[List[str]] = None,
    ) -> float:
        """
        Compute Normalized Discounted Cumulative Gain (nDCG@k)

        Measures: Quality of ranking, accounting for relevance grades
        Range: 0.0-1.0 (higher is better)

        Formula:
        DCG@k = sum(relevance_i / log2(i+1)) for i in top-k
        nDCG@k = DCG@k / IDCG@k (normalized by ideal ranking)

        Args:
            retrieved_ids: List of retrieved document IDs (ordered)
            relevance_scores: Dict mapping doc_id to relevance score (0-3)
            k: Cutoff rank
            ideal_ranking: Optional ideal ranking (defaults to sorted by relevance)

        Returns:
            nDCG@k score
        """
        if k <= 0 or not retrieved_ids:
            return 0.0

        # Compute actual DCG@k
        dcg = 0.0
        for i, doc_id in enumerate(retrieved_ids[:k], 1):
            rel = relevance_scores.get(doc_id, 0)
            dcg += rel / math.log2(i + 1)

        # Compute ideal DCG@k (IDCG)
        # Ideal ranking: docs sorted by relevance score descending
        if ideal_ranking is None:
            ideal_ranking = sorted(
                relevance_scores.keys(),
                key=lambda x: relevance_scores[x],
                reverse=True,
            )

        idcg = 0.0
        for i, doc_id in enumerate(ideal_ranking[:k], 1):
            rel = relevance_scores.get(doc_id, 0)
            idcg += rel / math.log2(i + 1)

        # Normalize
        if idcg == 0:
            return 0.0

        ndcg = dcg / idcg
        return min(1.0, ndcg)  # Ensure <= 1.0

    @staticmethod
    def compute_all_metrics(
        retrieved_ids: List[str],
        relevant_ids: Set[str],
        relevance_scores: Optional[Dict[str, int]] = None,
        k_values: List[int] = None,
    ) -> Dict[str, Dict[str, float]]:
        """
        Compute all metrics for multiple k values.

        Args:
            retrieved_ids: List of retrieved document IDs
            relevant_ids: Set of relevant document IDs
            relevance_scores: Optional dict for graded relevance (for nDCG)
            k_values: List of k values to evaluate (default: [3, 5, 10])

        Returns:
            Dictionary with metrics for each k value:
            {
                'k3': {'precision': 0.67, 'recall': 0.5, 'mrr': 1.0, 'ndcg': 0.72},
                'k5': {...},
                'k10': {...}
            }
        """
        if k_values is None:
            k_values = [3, 5, 10]

        # Ensure relevance_scores is provided (use binary relevance if not)
        if relevance_scores is None:
            relevance_scores = {doc_id: (1 if doc_id in relevant_ids else 0)
                                for doc_id in retrieved_ids}

        metrics_by_k = {}

        for k in k_values:
            key = f"k{k}"

            metrics_by_k[key] = {
                "precision": RetrievalMetrics.precision_at_k(retrieved_ids, relevant_ids, k),
                "recall": RetrievalMetrics.recall_at_k(retrieved_ids, relevant_ids, k),
                "mrr": RetrievalMetrics.mean_reciprocal_rank(retrieved_ids, relevant_ids),
                "ndcg": RetrievalMetrics.ndcg_at_k(retrieved_ids, relevance_scores, k),
            }

        return metrics_by_k

    @staticmethod
    def log_metrics(metrics: Dict[str, Dict[str, float]], query_id: str = None) -> None:
        """
        Log metrics in human-readable format.

        Args:
            metrics: Metrics dict from compute_all_metrics()
            query_id: Optional query ID for context
        """
        logger.info("=" * 70)
        if query_id:
            logger.info(f"METRICS FOR QUERY: {query_id}")
        else:
            logger.info("RETRIEVAL METRICS")
        logger.info("=" * 70)

        for k_key, k_metrics in sorted(metrics.items()):
            logger.info(f"\n{k_key.upper()}:")
            for metric_name, metric_value in k_metrics.items():
                logger.info(f"  {metric_name:10s}: {metric_value:.4f}")

        logger.info("=" * 70)

    @staticmethod
    def aggregate_metrics(
        all_metrics: List[Dict[str, Dict[str, float]]]
    ) -> Dict[str, Dict[str, float]]:
        """
        Aggregate metrics across multiple queries.

        Computes mean, min, max for each metric at each k.

        Args:
            all_metrics: List of metrics dicts (one per query)

        Returns:
            Aggregated metrics with mean, min, max for each k and metric
        """
        if not all_metrics:
            return {}

        # Get all k values from first query
        k_values = list(all_metrics[0].keys())

        aggregated = {}

        for k_key in k_values:
            aggregated[k_key] = {}

            # Get all metric names from first query
            metric_names = list(all_metrics[0][k_key].keys())

            for metric_name in metric_names:
                # Collect values for this metric across all queries
                values = [q[k_key][metric_name] for q in all_metrics if k_key in q]

                # Compute statistics
                aggregated[k_key][metric_name] = {
                    "mean": sum(values) / len(values) if values else 0.0,
                    "min": min(values) if values else 0.0,
                    "max": max(values) if values else 0.0,
                    "count": len(values),
                }

        return aggregated

    @staticmethod
    def log_aggregated_metrics(
        aggregated: Dict[str, Dict[str, Dict[str, float]]], name: str = "Results"
    ) -> None:
        """
        Log aggregated metrics with statistics.

        Args:
            aggregated: Aggregated metrics dict
            name: Name of the evaluation set
        """
        logger.info("=" * 70)
        logger.info(f"AGGREGATED METRICS: {name}")
        logger.info("=" * 70)

        for k_key in sorted(aggregated.keys()):
            logger.info(f"\n{k_key.upper()}:")
            for metric_name, stats in aggregated[k_key].items():
                mean = stats.get("mean", 0.0)
                min_val = stats.get("min", 0.0)
                max_val = stats.get("max", 0.0)
                count = stats.get("count", 0)
                logger.info(
                    f"  {metric_name:10s}: {mean:.4f} (min: {min_val:.4f}, "
                    f"max: {max_val:.4f}, n={count})"
                )

        logger.info("=" * 70)
