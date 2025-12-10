"""
Phase 3 Test Suite: Metrics and Monitoring

Tests the metrics evaluation and monitoring implementation:
1. Retrieval metrics (Precision, Recall, MRR, nDCG)
2. Metrics storage and retrieval
3. Degradation detection
4. Metrics aggregation
"""

import unittest
import json
from unittest.mock import Mock, MagicMock
from src.metrics.retrieval_metrics import RetrievalMetrics
from src.metrics.metrics_store import MetricsStore


class TestRetrievalMetrics(unittest.TestCase):
    """Test RetrievalMetrics functionality."""

    def test_precision_at_k_perfect(self):
        """Test precision with all relevant results."""
        retrieved = ["doc1", "doc2", "doc3"]
        relevant = {"doc1", "doc2", "doc3"}

        precision = RetrievalMetrics.precision_at_k(retrieved, relevant, k=3)

        self.assertEqual(precision, 1.0)

    def test_precision_at_k_partial(self):
        """Test precision with partial relevant results."""
        retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        relevant = {"doc1", "doc3", "doc5"}

        precision = RetrievalMetrics.precision_at_k(retrieved, relevant, k=5)

        self.assertEqual(precision, 0.6)  # 3/5

    def test_precision_at_k_none(self):
        """Test precision with no relevant results."""
        retrieved = ["doc1", "doc2", "doc3"]
        relevant = {"doc4", "doc5"}

        precision = RetrievalMetrics.precision_at_k(retrieved, relevant, k=3)

        self.assertEqual(precision, 0.0)

    def test_recall_at_k_perfect(self):
        """Test recall with all relevant items retrieved."""
        retrieved = ["doc1", "doc2", "doc3"]
        relevant = {"doc1", "doc2", "doc3"}

        recall = RetrievalMetrics.recall_at_k(retrieved, relevant, k=3)

        self.assertEqual(recall, 1.0)

    def test_recall_at_k_partial(self):
        """Test recall with partial retrieval."""
        retrieved = ["doc1", "doc2", "doc3"]
        relevant = {"doc1", "doc2", "doc3", "doc4", "doc5"}

        recall = RetrievalMetrics.recall_at_k(retrieved, relevant, k=3)

        self.assertEqual(recall, 0.6)  # 3/5

    def test_recall_at_k_none(self):
        """Test recall with no relevant items retrieved."""
        retrieved = ["doc4", "doc5"]
        relevant = {"doc1", "doc2", "doc3"}

        recall = RetrievalMetrics.recall_at_k(retrieved, relevant, k=2)

        self.assertEqual(recall, 0.0)

    def test_mrr_first_relevant(self):
        """Test MRR with first item relevant."""
        retrieved = ["doc1", "doc2", "doc3"]
        relevant = {"doc1"}

        mrr = RetrievalMetrics.mean_reciprocal_rank(retrieved, relevant)

        self.assertEqual(mrr, 1.0)

    def test_mrr_second_relevant(self):
        """Test MRR with second item relevant."""
        retrieved = ["docA", "doc1", "doc2"]
        relevant = {"doc1"}

        mrr = RetrievalMetrics.mean_reciprocal_rank(retrieved, relevant)

        self.assertAlmostEqual(mrr, 0.5)

    def test_mrr_none_relevant(self):
        """Test MRR with no relevant items."""
        retrieved = ["doc1", "doc2", "doc3"]
        relevant = {"doc4", "doc5"}

        mrr = RetrievalMetrics.mean_reciprocal_rank(retrieved, relevant)

        self.assertEqual(mrr, 0.0)

    def test_ndcg_perfect_ranking(self):
        """Test nDCG with perfect ranking (all relevant at top)."""
        retrieved = ["doc1", "doc2", "doc3"]
        relevance = {"doc1": 3, "doc2": 2, "doc3": 1}

        ndcg = RetrievalMetrics.ndcg_at_k(retrieved, relevance, k=3)

        # Perfect ranking has nDCG = 1.0
        self.assertAlmostEqual(ndcg, 1.0, places=2)

    def test_ndcg_degraded_ranking(self):
        """Test nDCG with degraded ranking."""
        retrieved = ["doc3", "doc1", "doc2"]  # Less relevant items first
        relevance = {"doc1": 3, "doc2": 2, "doc3": 1}

        ndcg = RetrievalMetrics.ndcg_at_k(retrieved, relevance, k=3)

        # Degraded ranking has lower nDCG
        self.assertLess(ndcg, 1.0)
        self.assertGreater(ndcg, 0.0)

    def test_compute_all_metrics(self):
        """Test computing all metrics at once."""
        retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        relevant = {"doc1", "doc2", "doc4"}
        relevance = {
            "doc1": 3,
            "doc2": 2,
            "doc3": 1,
            "doc4": 2,
            "doc5": 0,
        }

        metrics = RetrievalMetrics.compute_all_metrics(
            retrieved, relevant, relevance, k_values=[3, 5]
        )

        # Check structure
        self.assertIn("k3", metrics)
        self.assertIn("k5", metrics)
        self.assertIn("precision", metrics["k3"])
        self.assertIn("recall", metrics["k3"])
        self.assertIn("mrr", metrics["k3"])
        self.assertIn("ndcg", metrics["k3"])

        # Check values are in valid range
        for k_key in ["k3", "k5"]:
            for metric_value in metrics[k_key].values():
                self.assertGreaterEqual(metric_value, 0.0)
                self.assertLessEqual(metric_value, 1.0)

    def test_aggregate_metrics(self):
        """Test aggregating metrics across multiple queries."""
        all_metrics = [
            {
                "k5": {"precision": 0.8, "recall": 0.7, "mrr": 1.0, "ndcg": 0.75}
            },
            {
                "k5": {"precision": 0.6, "recall": 0.5, "mrr": 0.5, "ndcg": 0.65}
            },
            {
                "k5": {"precision": 0.4, "recall": 0.3, "mrr": 0.2, "ndcg": 0.55}
            },
        ]

        aggregated = RetrievalMetrics.aggregate_metrics(all_metrics)

        # Check structure
        self.assertIn("k5", aggregated)
        self.assertIn("precision", aggregated["k5"])

        # Check mean calculation
        precision_stats = aggregated["k5"]["precision"]
        expected_mean = (0.8 + 0.6 + 0.4) / 3
        self.assertAlmostEqual(precision_stats["mean"], expected_mean, places=2)
        self.assertEqual(precision_stats["count"], 3)


class TestMetricsStore(unittest.TestCase):
    """Test MetricsStore functionality."""

    def setUp(self):
        """Create mock Redis client."""
        self.mock_redis = MagicMock()
        self.store = MetricsStore(redis_client=self.mock_redis)

    def test_initialization(self):
        """Test MetricsStore initialization."""
        self.assertIsNotNone(self.store)
        self.assertEqual(self.store.RETENTION_DAYS, 30)
        self.assertEqual(len(self.store.DEFAULT_THRESHOLDS), 4)

    def test_record_retrieval_metrics(self):
        """Test recording metrics."""
        metrics = {
            "k5": {"precision": 0.8, "recall": 0.7, "mrr": 1.0, "ndcg": 0.75}
        }

        result = self.store.record_retrieval_metrics(
            query_id="Q001",
            collection_id="col1",
            metrics=metrics,
        )

        # Should succeed if Redis is configured
        # Mock will record the call
        if self.mock_redis:
            self.assertTrue(result or result is None)  # May be True or None

    def test_set_alert_threshold(self):
        """Test setting alert thresholds."""
        self.store.set_alert_threshold("precision_k5", 0.90)

        self.assertEqual(self.store.thresholds["precision_k5"], 0.90)

    def test_check_degradation_no_data(self):
        """Test degradation check with no data."""
        # Mock returns no stats
        self.mock_redis.zrange.return_value = []

        result = self.store.check_degradation("col1", "precision")

        self.assertFalse(result["degraded"])
        self.assertEqual(result["status"], "insufficient_data")

    def test_get_collection_baseline(self):
        """Test getting collection baseline."""
        # This would need Redis to be properly configured
        result = self.store.get_collection_baseline("col1")

        self.assertIsInstance(result, dict)


class TestPhase3Integration(unittest.TestCase):
    """Integration tests for Phase 3 metrics."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_redis = MagicMock()
        self.store = MetricsStore(redis_client=self.mock_redis)

    def test_complete_evaluation_workflow(self):
        """Test complete evaluation workflow."""
        # Step 1: Compute metrics for a query
        retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        relevant = {"doc1", "doc2", "doc4"}
        relevance = {
            "doc1": 3,
            "doc2": 2,
            "doc3": 1,
            "doc4": 2,
            "doc5": 0,
        }

        metrics = RetrievalMetrics.compute_all_metrics(
            retrieved, relevant, relevance, k_values=[3, 5]
        )

        # Step 2: Store metrics
        success = self.store.record_retrieval_metrics(
            query_id="Q001",
            collection_id="test_col",
            metrics=metrics,
        )

        # Step 3: Verify metrics are computed correctly
        self.assertIsNotNone(metrics)
        self.assertIn("k3", metrics)
        self.assertIn("k5", metrics)

        # Step 4: Check precision values
        k3_precision = metrics["k3"]["precision"]
        k5_precision = metrics["k5"]["precision"]

        # k=3: 2 relevant in top 3 = 2/3 ≈ 0.667
        self.assertAlmostEqual(k3_precision, 2 / 3, places=2)

        # k=5: 3 relevant in top 5 = 3/5 = 0.6
        self.assertAlmostEqual(k5_precision, 0.6, places=2)

    def test_metrics_across_queries(self):
        """Test aggregating metrics across multiple queries."""
        query_results = [
            {
                "query_id": "Q001",
                "retrieved": ["doc1", "doc2", "doc3"],
                "relevant": {"doc1", "doc2"},
            },
            {
                "query_id": "Q002",
                "retrieved": ["doc4", "doc5", "doc6"],
                "relevant": {"doc4"},
            },
            {
                "query_id": "Q003",
                "retrieved": ["doc7", "doc8", "doc9"],
                "relevant": {"doc7", "doc8", "doc9"},
            },
        ]

        all_metrics = []
        for qr in query_results:
            metrics = RetrievalMetrics.compute_all_metrics(
                qr["retrieved"],
                qr["relevant"],
                k_values=[3],
            )
            all_metrics.append(metrics)

        # Aggregate metrics
        aggregated = RetrievalMetrics.aggregate_metrics(all_metrics)

        # Verify aggregation
        self.assertIn("k3", aggregated)
        self.assertIn("precision", aggregated["k3"])
        self.assertEqual(aggregated["k3"]["precision"]["count"], 3)

        # Mean precision should be (1.0 + 0.333 + 1.0) / 3 ≈ 0.777
        mean_precision = aggregated["k3"]["precision"]["mean"]
        self.assertGreater(mean_precision, 0.6)
        self.assertLess(mean_precision, 1.0)

    def test_golden_qa_pairs_loading(self):
        """Test loading golden QA pairs."""
        import os

        qa_file = (
            "/Users/srikaryaganti/workspaces/drdo/diksuchi-ai/"
            "services/rag-service/data/evaluation/golden_qa_pairs.json"
        )

        if os.path.exists(qa_file):
            with open(qa_file, "r") as f:
                qa_pairs = json.load(f)

            # Verify structure
            self.assertIsInstance(qa_pairs, list)
            self.assertGreater(len(qa_pairs), 0)

            # Check first pair
            first_pair = qa_pairs[0]
            self.assertIn("query_id", first_pair)
            self.assertIn("query", first_pair)
            self.assertIn("collection_id", first_pair)
            self.assertIn("relevant_doc_ids", first_pair)
            self.assertIn("relevance_scores", first_pair)

            # Verify all have required fields
            for pair in qa_pairs:
                self.assertIn("query_id", pair)
                self.assertIsInstance(pair["relevance_scores"], dict)


if __name__ == "__main__":
    unittest.main()
