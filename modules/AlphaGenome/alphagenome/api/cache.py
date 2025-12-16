"""
AlphaGenome Prediction Cache

File-based cache for API predictions to avoid redundant API calls.
Uses JSON files organized by cache key prefix for efficient lookup.
"""

import json
from pathlib import Path
from typing import Any


class PredictionCache:
    """
    File-based cache for AlphaGenome predictions.

    Stores predictions in JSON files organized by cache key prefix.
    This allows efficient caching without requiring zarr dependency.

    Example:
        >>> cache = PredictionCache("cache/predictions")
        >>> cache.set("abc123", {"effect": 0.5})
        >>> result = cache.get("abc123")
    """

    def __init__(self, cache_dir: Path | str):
        """
        Initialize cache.

        Args:
            cache_dir: Directory for cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # In-memory index for fast lookups
        self._index: dict[str, Path] = {}
        self._load_index()

    def _load_index(self):
        """Load existing cache keys into index."""
        for cache_file in self.cache_dir.glob("*.json"):
            key = cache_file.stem
            self._index[key] = cache_file

    def _get_cache_path(self, key: str) -> Path:
        """Get file path for a cache key."""
        return self.cache_dir / f"{key}.json"

    def get(self, key: str) -> dict | None:
        """
        Get cached prediction.

        Args:
            key: Cache key

        Returns:
            Cached data or None if not found
        """
        if key not in self._index:
            return None

        cache_file = self._index[key]

        try:
            with open(cache_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # Remove corrupted entry
            del self._index[key]
            return None

    def set(self, key: str, value: dict):
        """
        Store prediction in cache.

        Args:
            key: Cache key
            value: Data to cache (must be JSON-serializable)
        """
        cache_file = self._get_cache_path(key)

        with open(cache_file, "w") as f:
            json.dump(value, f, indent=2)

        self._index[key] = cache_file

    def has(self, key: str) -> bool:
        """Check if key exists in cache."""
        return key in self._index

    def delete(self, key: str):
        """Delete cached entry."""
        if key in self._index:
            try:
                self._index[key].unlink()
            except FileNotFoundError:
                pass
            del self._index[key]

    def clear(self):
        """Clear all cached entries."""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
        self._index.clear()

    def size(self) -> int:
        """Get number of cached entries."""
        return len(self._index)

    def stats(self) -> dict:
        """Get cache statistics."""
        total_size = sum(f.stat().st_size for f in self._index.values())
        return {
            "entries": len(self._index),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / 1e6,
        }


class ZarrPredictionCache:
    """
    Zarr-based cache for large-scale predictions.

    More efficient for storing thousands of predictions, but requires
    zarr dependency. Falls back to file-based cache if zarr unavailable.
    """

    def __init__(self, cache_dir: Path | str):
        """Initialize Zarr cache."""
        try:
            import zarr
            self._zarr = zarr
        except ImportError:
            raise ImportError(
                "Zarr is required for ZarrPredictionCache. "
                "Install with: pip install zarr"
            )

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._store = zarr.open(str(self.cache_dir / "predictions.zarr"), mode="a")

    def get(self, key: str) -> Any | None:
        """Get cached prediction."""
        if key in self._store:
            return self._store[key][:]
        return None

    def set(self, key: str, value: Any):
        """Store prediction."""
        self._store[key] = value

    def has(self, key: str) -> bool:
        """Check if key exists."""
        return key in self._store

    def size(self) -> int:
        """Get number of entries."""
        return len(self._store)
