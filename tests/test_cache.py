import time

import pytest

from app.services.cache import CacheService


def test_cache_normalizes_query_keys():
	cache = CacheService()

	cache.set("  WiFi   is OFF ", {"contexts": []})

	assert cache.get("wifi is off") == {"contexts": []}


def test_cache_expires_values():
	cache = CacheService(ttl_seconds=0.01)
	cache.set("wifi", "result")

	time.sleep(0.02)

	assert cache.get("wifi") is None


def test_cache_evicts_expiring_entry_when_full():
	cache = CacheService(max_size=1)
	cache.set("first", 1)
	cache.set("second", 2)

	assert cache.get("first") is None
	assert cache.get("second") == 2


def test_cache_clear_removes_values():
	cache = CacheService()
	cache.set("wifi", "result")

	cache.clear()

	assert cache.get("wifi") is None


def test_cache_values_are_isolated_from_caller_mutations():
	cache = CacheService()
	value = {"contexts": [{"title": "Original"}]}

	cache.set("wifi", value)
	value["contexts"][0]["title"] = "Changed before read"
	result = cache.get("wifi")
	result["contexts"][0]["title"] = "Changed after read"

	assert cache.get("wifi") == {"contexts": [{"title": "Original"}]}


@pytest.mark.parametrize("kwargs", [{"ttl_seconds": 0}, {"max_size": 0}])
def test_cache_rejects_invalid_configuration(kwargs):
	with pytest.raises(ValueError):
		CacheService(**kwargs)
