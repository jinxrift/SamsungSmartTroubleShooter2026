_cache = {}


def get(key):
    """Return cached value for key, or None if not found."""
    return _cache.get(key)


def set(key, value):
    """Store a value in the cache."""
    _cache[key] = value