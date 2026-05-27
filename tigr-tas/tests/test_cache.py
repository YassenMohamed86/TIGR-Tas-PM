import pytest
import asyncio
from unittest.mock import patch
from app.cache.cache_manager import CacheManager
from freezegun import freeze_time

pytestmark = pytest.mark.asyncio

@pytest.fixture
def cache_manager(fake_redis):
    # We patch get_redis_client to return fake_redis
    with patch("app.cache.cache_manager.get_redis_client", return_value=fake_redis):
        cm = CacheManager()
        cm.client = fake_redis # Ensure it uses the fake redis directly
        yield cm

async def test_cache_set_and_get(cache_manager):
    await cache_manager.set("key1", {"data": "value"}, ttl=60)
    result = await cache_manager.get("key1")
    assert result == {"data": "value"}

async def test_cache_get_missing_key_returns_none(cache_manager):
    result = await cache_manager.get("nonexistent_key")
    assert result is None

async def test_cache_delete(cache_manager):
    await cache_manager.set("key2", "value")
    await cache_manager.delete("key2")
    assert await cache_manager.get("key2") is None

async def test_cache_ttl_expiry(cache_manager):
    # fake_redis might not support TTL advancement accurately with freezegun,
    # but we can try to test logic if it supports. Or we can just sleep if small.
    # To avoid slow tests, we can just check if ttl is set in fake_redis
    await cache_manager.set("key3", "value", ttl=1)
    # fake_redis supports real sleep
    await asyncio.sleep(1.1)
    assert await cache_manager.get("key3") is None

async def test_cache_set_overwrites_existing(cache_manager):
    await cache_manager.set("key4", "original")
    await cache_manager.set("key4", "updated")
    assert await cache_manager.get("key4") == "updated"
