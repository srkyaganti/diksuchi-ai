"""
Metrics storage and retrieval with Redis backend.

Provides persistent storage of retrieval metrics with:
- Individual query metrics (30-day retention)
- Hourly aggregations for trend analysis
- Degradation detection
- Alert thresholds
"""

import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class MetricsStore:
    """Redis-backed metrics storage and retrieval."""

    # Configuration
    RETENTION_DAYS = 30
    HOURLY_RETENTION_DAYS = 90
    ALERT_WINDOW_HOURS = 24  # Check last 24 hours for degradation

    # Default thresholds for alerting
    DEFAULT_THRESHOLDS = {
        "precision_k5": 0.75,  # Should maintain >75% precision
        "recall_k10": 0.85,    # Should maintain >85% recall
        "mrr": 0.70,           # Should maintain >70% MRR
        "ndcg_k5": 0.75,       # Should maintain >75% nDCG
    }

    def __init__(self, redis_client=None):
        """
        Initialize metrics store.

        Args:
            redis_client: Optional Redis client (for testing)
                         If None, will attempt to use default Redis
        """
        self.redis = redis_client
        self.thresholds = self.DEFAULT_THRESHOLDS.copy()

    def record_retrieval_metrics(
        self,
        query_id: str,
        collection_id: str,
        metrics: Dict[str, Dict[str, float]],
        timestamp: Optional[int] = None,
    ) -> bool:
        """
        Record metrics for a single query retrieval.

        Stores:
        1. Individual query metrics (with TTL)
        2. Hourly aggregates (for trending)

        Args:
            query_id: Unique query identifier
            collection_id: Collection being queried
            metrics: Metrics dict from RetrievalMetrics.compute_all_metrics()
            timestamp: Optional Unix timestamp (defaults to now)

        Returns:
            True if stored successfully
        """
        if not self.redis or timestamp is None:
            timestamp = int(time.time())

        try:
            # Key for individual query
            query_key = f"rag_metrics:query:{collection_id}:{query_id}"

            # Store metrics with TTL
            metrics_data = {
                "query_id": query_id,
                "collection_id": collection_id,
                "timestamp": timestamp,
                "metrics": metrics,
            }

            self.redis.setex(
                query_key,
                self.RETENTION_DAYS * 86400,  # Convert days to seconds
                json.dumps(metrics_data),
            )

            # Also store in hourly aggregate
            self._add_to_hourly_aggregate(collection_id, metrics, timestamp)

            logger.debug(f"Recorded metrics for query {query_id}")
            return True

        except Exception as e:
            logger.error(f"Error recording metrics: {e}")
            return False

    def _add_to_hourly_aggregate(
        self, collection_id: str, metrics: Dict[str, Dict[str, float]], timestamp: int
    ) -> None:
        """
        Add query metrics to hourly aggregate.

        Args:
            collection_id: Collection ID
            metrics: Query metrics
            timestamp: Unix timestamp
        """
        if not self.redis:
            return

        try:
            # Get hour from timestamp
            dt = datetime.fromtimestamp(timestamp)
            hour_key = dt.strftime("%Y-%m-%d-%H")

            # Key for hourly aggregate
            agg_key = f"rag_metrics:hourly:{collection_id}:{hour_key}"

            # Store individual metric values for percentile calculation
            for k_key, k_metrics in metrics.items():
                for metric_name, metric_value in k_metrics.items():
                    # Use sorted set for each metric (for percentiles)
                    zset_key = f"{agg_key}:{metric_name}"
                    self.redis.zadd(zset_key, {str(metric_value): time.time()})
                    self.redis.expire(zset_key, self.HOURLY_RETENTION_DAYS * 86400)

        except Exception as e:
            logger.error(f"Error adding to hourly aggregate: {e}")

    def get_hourly_stats(
        self, collection_id: str, metric_name: str, hours_back: int = 24
    ) -> Dict[str, float]:
        """
        Get hourly statistics for a metric over time window.

        Returns mean, p50, p95, p99, min, max for the metric.

        Args:
            collection_id: Collection ID
            metric_name: Metric name (e.g., "precision", "recall")
            hours_back: How many hours back to look (default: 24)

        Returns:
            Statistics dict with mean, p50, p95, p99, min, max, count
        """
        if not self.redis:
            return {}

        try:
            now = datetime.now()
            stats_list = []

            # Collect metrics from last N hours
            for i in range(hours_back):
                check_time = now - timedelta(hours=i)
                hour_key = check_time.strftime("%Y-%m-%d-%H")
                zset_key = f"rag_metrics:hourly:{collection_id}:{metric_name}"

                # Get values for this hour
                values = self.redis.zrange(zset_key, 0, -1)
                stats_list.extend([float(v) for v in values])

            if not stats_list:
                return {"count": 0, "mean": 0.0}

            # Compute statistics
            stats_list.sort()
            count = len(stats_list)
            mean = sum(stats_list) / count

            percentiles = {
                "p50": stats_list[int(count * 0.50)],
                "p95": stats_list[int(count * 0.95)],
                "p99": stats_list[int(count * 0.99)],
            }

            return {
                "mean": mean,
                "min": min(stats_list),
                "max": max(stats_list),
                "count": count,
                **percentiles,
            }

        except Exception as e:
            logger.error(f"Error getting hourly stats: {e}")
            return {}

    def check_degradation(
        self,
        collection_id: str,
        metric_name: str,
        threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Check if a metric has degraded below threshold.

        Compares last 24 hours against threshold.

        Args:
            collection_id: Collection ID
            metric_name: Metric name
            threshold: Threshold value (uses default if not specified)

        Returns:
            {
                'degraded': bool,
                'current_mean': float,
                'threshold': float,
                'change': float,
                'status': str
            }
        """
        if threshold is None:
            threshold = self.thresholds.get(metric_name, 0.70)

        # Get recent stats
        stats = self.get_hourly_stats(collection_id, metric_name, hours_back=24)

        if not stats or stats.get("count", 0) == 0:
            return {
                "degraded": False,
                "current_mean": 0.0,
                "threshold": threshold,
                "change": 0.0,
                "status": "insufficient_data",
            }

        current_mean = stats.get("mean", 0.0)
        degraded = current_mean < threshold

        return {
            "degraded": degraded,
            "current_mean": current_mean,
            "threshold": threshold,
            "change": current_mean - threshold,
            "status": "degraded" if degraded else "healthy",
        }

    def get_collection_baseline(
        self, collection_id: str, metric_names: List[str] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Get baseline statistics for a collection across all metrics.

        Args:
            collection_id: Collection ID
            metric_names: List of metrics to retrieve (default: all standard metrics)

        Returns:
            Dict with stats for each metric
        """
        if metric_names is None:
            metric_names = ["precision", "recall", "mrr", "ndcg"]

        baselines = {}

        for metric in metric_names:
            baselines[metric] = self.get_hourly_stats(
                collection_id, metric, hours_back=168  # 7 days
            )

        return baselines

    def set_alert_threshold(self, metric_name: str, threshold: float) -> None:
        """
        Set custom alert threshold for a metric.

        Args:
            metric_name: Metric name
            threshold: Threshold value
        """
        self.thresholds[metric_name] = threshold
        logger.info(f"Set alert threshold for {metric_name}: {threshold}")

    def clear_old_metrics(self) -> int:
        """
        Clear metrics older than retention period.

        Note: Redis TTL handles this automatically, but this
        can be called for explicit cleanup.

        Returns:
            Number of keys deleted
        """
        if not self.redis:
            return 0

        try:
            # Find all old query keys
            cutoff_time = int(time.time()) - (self.RETENTION_DAYS * 86400)
            deleted = 0

            # Scan for old keys
            cursor = 0
            while True:
                cursor, keys = self.redis.scan(
                    cursor, match="rag_metrics:query:*", count=100
                )

                for key in keys:
                    try:
                        # Check TTL
                        ttl = self.redis.ttl(key)
                        if ttl == -1:  # No TTL, delete it
                            self.redis.delete(key)
                            deleted += 1
                    except Exception:
                        pass

                if cursor == 0:
                    break

            logger.info(f"Cleared {deleted} old metric entries")
            return deleted

        except Exception as e:
            logger.error(f"Error clearing old metrics: {e}")
            return 0

    def log_metrics_status(self, collection_id: str) -> None:
        """
        Log current metrics status for a collection.

        Args:
            collection_id: Collection ID
        """
        logger.info("=" * 70)
        logger.info(f"METRICS STATUS FOR COLLECTION: {collection_id}")
        logger.info("=" * 70)

        baselines = self.get_collection_baseline(collection_id)

        for metric_name, stats in baselines.items():
            if stats.get("count", 0) == 0:
                logger.info(f"{metric_name}: No data")
                continue

            mean = stats.get("mean", 0.0)
            threshold = self.thresholds.get(metric_name, 0.70)
            status = "✅ HEALTHY" if mean >= threshold else "⚠️  DEGRADED"

            logger.info(
                f"{metric_name:12s}: {mean:.4f} (threshold: {threshold:.4f}) {status}"
            )

        logger.info("=" * 70)
