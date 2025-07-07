from __future__ import annotations
"""Simple in-memory cache manager with TTL support."""

import hashlib
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class _CacheItem:
    data: Any
    timestamp: float


class CacheManager:
    """Manage feature and prediction caches with TTL."""

    def __init__(self, feature_ttl: int = 60, prediction_ttl: int = 300, max_size: int = 1000) -> None:
        self.feature_ttl = feature_ttl
        self.prediction_ttl = prediction_ttl
        self.max_size = max_size
        self.feature_cache: Dict[str, _CacheItem] = {}
        self.prediction_cache: Dict[str, _CacheItem] = {}
        self.feature_hits = 0
        self.feature_misses = 0
        self.prediction_hits = 0
        self.prediction_misses = 0

    def get_feature_key(self, symbol: str, ts: float) -> str:
        minute_ts = int(ts // 60) * 60
        return f"features_{symbol}_{minute_ts}"

    def get_prediction_key(self, symbol: str, strategy: str, features: Any) -> str:
        feature_hash = hashlib.md5(str(features).encode()).hexdigest()[:8]
        return f"pred_{symbol}_{strategy}_{feature_hash}"

    def get_feature(self, key: str) -> Optional[Any]:
        item = self.feature_cache.get(key)
        if item and time.time() - item.timestamp < self.feature_ttl:
            self.feature_hits += 1
            return item.data
        if item:
            del self.feature_cache[key]
        self.feature_misses += 1
        return None

    def set_feature(self, key: str, data: Any) -> None:
        self.feature_cache[key] = _CacheItem(data, time.time())
        self._evict(self.feature_cache)

    def get_prediction(self, key: str) -> Optional[Any]:
        item = self.prediction_cache.get(key)
        if item and time.time() - item.timestamp < self.prediction_ttl:
            self.prediction_hits += 1
            return item.data
        if item:
            del self.prediction_cache[key]
        self.prediction_misses += 1
        return None

    def set_prediction(self, key: str, data: Any) -> None:
        self.prediction_cache[key] = _CacheItem(data, time.time())
        self._evict(self.prediction_cache)

    def _evict(self, cache: Dict[str, _CacheItem]) -> None:
        if len(cache) <= self.max_size:
            return
        # remove oldest 10% items
        sorted_keys = sorted(cache, key=lambda k: cache[k].timestamp)
        for k in sorted_keys[: max(len(cache) // 10, 1)]:
            del cache[k]

    def stats(self) -> Dict[str, int]:
        return {
            "feature_hits": self.feature_hits,
            "feature_misses": self.feature_misses,
            "prediction_hits": self.prediction_hits,
            "prediction_misses": self.prediction_misses,
        }
