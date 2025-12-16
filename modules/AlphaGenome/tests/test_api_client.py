"""
Tests for AlphaGenome API Client

Tests variant effect prediction, caching, and batch operations.
"""

import pytest
from pathlib import Path
import sys
import json
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from alphagenome.api.client import AlphaGenomeClient, VariantEffect
from alphagenome.api.cache import PredictionCache


class TestVariantEffect:
    """Test VariantEffect dataclass."""

    def test_variant_effect_creation(self):
        """Should create VariantEffect with all fields."""
        effect = VariantEffect(
            variant_id="chr1:12345:A>G",
            gene="BRCA1",
            effect_size=0.75,
            p_value=0.001,
            tissue="brain",
            effect_type="eQTL",
            confidence=0.95,
        )

        assert effect.variant_id == "chr1:12345:A>G"
        assert effect.gene == "BRCA1"
        assert effect.effect_size == 0.75
        assert effect.p_value == 0.001
        assert effect.tissue == "brain"

    def test_is_significant_below_threshold(self):
        """Effects with low p-value should be significant."""
        effect = VariantEffect(
            variant_id="chr1:12345:A>G",
            gene="BRCA1",
            effect_size=0.5,
            p_value=0.01,
            tissue="brain",
            effect_type="eQTL",
            confidence=0.9,
        )

        assert effect.is_significant is True

    def test_is_not_significant_above_threshold(self):
        """Effects with high p-value should not be significant."""
        effect = VariantEffect(
            variant_id="chr1:12345:A>G",
            gene="BRCA1",
            effect_size=0.1,
            p_value=0.1,
            tissue="brain",
            effect_type="eQTL",
            confidence=0.5,
        )

        assert effect.is_significant is False

    def test_to_dict(self):
        """Should convert to dictionary correctly."""
        effect = VariantEffect(
            variant_id="chr1:12345:A>G",
            gene="BRCA1",
            effect_size=0.5,
            p_value=0.01,
            tissue="brain",
            effect_type="eQTL",
            confidence=0.9,
        )

        d = effect.to_dict()

        assert d["variant_id"] == "chr1:12345:A>G"
        assert d["gene"] == "BRCA1"
        assert "is_significant" in d


class TestAlphaGenomeClient:
    """Test AlphaGenomeClient functionality."""

    @pytest.fixture
    def client(self, tmp_path):
        """Create client with temporary cache directory."""
        return AlphaGenomeClient(cache_dir=tmp_path)

    @pytest.fixture
    def client_no_cache(self, tmp_path):
        """Create client without caching."""
        return AlphaGenomeClient(cache_dir=tmp_path, use_cache=False)

    def test_client_initialization(self, client):
        """Client should initialize with default settings."""
        assert client.cache is not None
        assert client.use_cache is True

    def test_client_no_cache_initialization(self, client_no_cache):
        """Client should work without cache."""
        assert client_no_cache.use_cache is False

    def test_predict_variant_returns_effect(self, client):
        """Should return VariantEffect for variant prediction."""
        result = client.predict_variant(
            chrom="chr1",
            pos=12345,
            ref="A",
            alt="G",
            gene="BRCA1",
            tissue="brain",
        )

        assert isinstance(result, VariantEffect)
        assert result.variant_id == "chr1:12345:A>G"
        assert result.gene == "BRCA1"

    def test_predict_variant_caches_result(self, client, tmp_path):
        """Should cache prediction results."""
        # First call
        result1 = client.predict_variant(
            chrom="chr1",
            pos=12345,
            ref="A",
            alt="G",
            gene="TEST",
        )

        # Check cache
        cache_key = "chr1:12345:A>G:TEST:None"
        cached = client.cache.get(cache_key)

        assert cached is not None

    def test_predict_eqtl_single_tissue(self, client):
        """Should predict eQTL for single tissue."""
        results = client.predict_eqtl(
            chrom="chr1",
            pos=12345,
            ref="A",
            alt="G",
            gene="BRCA1",
            tissues=["brain"],
        )

        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0].tissue == "brain"

    def test_predict_eqtl_multiple_tissues(self, client):
        """Should predict eQTL for multiple tissues."""
        tissues = ["brain", "liver", "heart"]

        results = client.predict_eqtl(
            chrom="chr1",
            pos=12345,
            ref="A",
            alt="G",
            gene="BRCA1",
            tissues=tissues,
        )

        assert isinstance(results, list)
        assert len(results) == len(tissues)

    def test_batch_predict(self, client):
        """Should predict effects for multiple variants."""
        variants = [
            {"chrom": "chr1", "pos": 100, "ref": "A", "alt": "G"},
            {"chrom": "chr1", "pos": 200, "ref": "C", "alt": "T"},
            {"chrom": "chr2", "pos": 300, "ref": "G", "alt": "A"},
        ]

        results = client.batch_predict(variants, gene="TEST")

        assert isinstance(results, list)
        assert len(results) == len(variants)
        assert all(isinstance(r, VariantEffect) for r in results)

    def test_batch_predict_empty_list(self, client):
        """Should handle empty variant list."""
        results = client.batch_predict([], gene="TEST")

        assert results == []


class TestPredictionCache:
    """Test PredictionCache functionality."""

    @pytest.fixture
    def cache(self, tmp_path):
        """Create cache in temporary directory."""
        return PredictionCache(cache_dir=tmp_path)

    def test_cache_initialization(self, tmp_path):
        """Cache should create directory if needed."""
        cache_dir = tmp_path / "new_cache"
        cache = PredictionCache(cache_dir=cache_dir)

        assert cache_dir.exists()

    def test_cache_set_and_get(self, cache):
        """Should store and retrieve values."""
        key = "test_key"
        value = {"effect_size": 0.5, "p_value": 0.01}

        cache.set(key, value)
        result = cache.get(key)

        assert result == value

    def test_cache_miss_returns_none(self, cache):
        """Should return None for missing keys."""
        result = cache.get("nonexistent_key")

        assert result is None

    def test_cache_overwrites_existing(self, cache):
        """Should overwrite existing values."""
        key = "test_key"
        value1 = {"value": 1}
        value2 = {"value": 2}

        cache.set(key, value1)
        cache.set(key, value2)
        result = cache.get(key)

        assert result == value2

    def test_cache_persists_to_disk(self, tmp_path):
        """Cache should persist values to disk."""
        key = "persistent_key"
        value = {"data": "test"}

        # Create first cache, set value
        cache1 = PredictionCache(cache_dir=tmp_path)
        cache1.set(key, value)

        # Create second cache, should find value
        cache2 = PredictionCache(cache_dir=tmp_path)
        result = cache2.get(key)

        assert result == value

    def test_cache_stats(self, cache):
        """Should track cache statistics."""
        # Set some values
        cache.set("key1", {"a": 1})
        cache.set("key2", {"b": 2})

        # Get some values (hits and misses)
        cache.get("key1")  # hit
        cache.get("key3")  # miss

        stats = cache.stats()

        assert "entries" in stats
        assert "hits" in stats
        assert "misses" in stats
        assert stats["entries"] == 2
        assert stats["hits"] == 1
        assert stats["misses"] == 1

    def test_cache_clear(self, cache):
        """Should clear all cached values."""
        cache.set("key1", {"a": 1})
        cache.set("key2", {"b": 2})

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.stats()["entries"] == 0


class TestCacheKeyGeneration:
    """Test cache key generation."""

    @pytest.fixture
    def client(self, tmp_path):
        """Create client with temporary cache directory."""
        return AlphaGenomeClient(cache_dir=tmp_path)

    def test_variant_key_format(self, client):
        """Variant keys should be consistent."""
        # Call predict to generate cache entry
        client.predict_variant(
            chrom="chr1",
            pos=12345,
            ref="A",
            alt="G",
            gene="BRCA1",
            tissue="brain",
        )

        # Check expected key format
        expected_key = "chr1:12345:A>G:BRCA1:brain"
        assert client.cache.get(expected_key) is not None

    def test_different_variants_different_keys(self, client):
        """Different variants should have different cache keys."""
        client.predict_variant("chr1", 100, "A", "G", gene="TEST")
        client.predict_variant("chr1", 200, "C", "T", gene="TEST")

        stats = client.cache.stats()
        assert stats["entries"] == 2


class TestErrorHandling:
    """Test error handling in API client."""

    @pytest.fixture
    def client(self, tmp_path):
        """Create client with temporary cache directory."""
        return AlphaGenomeClient(cache_dir=tmp_path)

    def test_invalid_chromosome(self, client):
        """Should handle invalid chromosome gracefully."""
        # The mock implementation should still return a result
        result = client.predict_variant(
            chrom="chrInvalid",
            pos=100,
            ref="A",
            alt="G",
        )

        # Should return a valid VariantEffect (mock always succeeds)
        assert isinstance(result, VariantEffect)

    def test_empty_gene(self, client):
        """Should handle missing gene parameter."""
        result = client.predict_variant(
            chrom="chr1",
            pos=100,
            ref="A",
            alt="G",
            gene=None,
        )

        assert isinstance(result, VariantEffect)

    def test_empty_tissue(self, client):
        """Should handle missing tissue parameter."""
        result = client.predict_variant(
            chrom="chr1",
            pos=100,
            ref="A",
            alt="G",
            tissue=None,
        )

        assert isinstance(result, VariantEffect)


class TestClientConfiguration:
    """Test client configuration options."""

    def test_custom_cache_dir(self, tmp_path):
        """Should use custom cache directory."""
        custom_dir = tmp_path / "custom_cache"
        client = AlphaGenomeClient(cache_dir=custom_dir)

        assert client.cache.cache_dir == custom_dir
        assert custom_dir.exists()

    def test_disable_cache(self, tmp_path):
        """Should work with caching disabled."""
        client = AlphaGenomeClient(cache_dir=tmp_path, use_cache=False)

        # First call
        result1 = client.predict_variant("chr1", 100, "A", "G")

        # Should not cache
        stats = client.cache.stats()
        assert stats["entries"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
