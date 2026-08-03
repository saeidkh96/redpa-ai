from app.runtime_cache.service import DistributedCacheService

def test_cache_key_is_deterministic():
    assert DistributedCacheService.build_key(
        "x", {"b": 2, "a": 1}
    ) == DistributedCacheService.build_key(
        "x", {"a": 1, "b": 2}
    )
