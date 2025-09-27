from functools import lru_cache
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, TypeVar, Generic, Callable, Awaitable
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

class DataCache(Generic[T]):
    """Generic data cache with TTL support"""
    
    def __init__(self, ttl_minutes: int = 30):
        self.data: Optional[T] = None
        self.last_fetch: Optional[datetime] = None
        self.ttl = timedelta(minutes=ttl_minutes)
        self._lock = asyncio.Lock()
    
    async def get_data(self, fetch_func: Callable[[], Awaitable[T]]) -> T:
        """Get cached data or fetch fresh data if cache is expired"""
        async with self._lock:
            if self._is_cache_valid():
                logger.debug("Returning cached data")
                return self.data
            
            logger.info("Cache expired or empty, fetching fresh data")
            try:
                self.data = await fetch_func()
                self.last_fetch = datetime.now()
                logger.info("Successfully updated cache")
                return self.data
            except Exception as e:
                logger.error(f"Failed to fetch fresh data: {e}")
                # Return stale data if available, otherwise re-raise
                if self.data is not None:
                    logger.warning("Returning stale cached data due to fetch failure")
                    return self.data
                raise
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        if self.data is None or self.last_fetch is None:
            return False
        
        age = datetime.now() - self.last_fetch
        return age <= self.ttl
    
    def invalidate(self) -> None:
        """Manually invalidate the cache"""
        logger.info("Cache manually invalidated")
        self.data = None
        self.last_fetch = None
    
    def get_cache_age(self) -> Optional[timedelta]:
        """Get the age of the current cache"""
        if self.last_fetch is None:
            return None
        return datetime.now() - self.last_fetch
    
    @property
    def is_cached(self) -> bool:
        """Check if data is currently cached"""
        return self.data is not None


class PolyHavenDataCache:
    """Specialized cache for PolyHaven data with multiple cache buckets"""
    
    def __init__(self, ttl_minutes: int = 30):
        self.assets_cache: Dict[str, DataCache[Dict[str, Any]]] = {}
        self.types_cache = DataCache[list](ttl_minutes)
        self.categories_cache: Dict[str, DataCache[Dict[str, int]]] = {}
        self.ttl_minutes = ttl_minutes
    
    def get_assets_cache(self, cache_key: str) -> DataCache[Dict[str, Any]]:
        """Get or create assets cache for a specific filter combination"""
        if cache_key not in self.assets_cache:
            self.assets_cache[cache_key] = DataCache[Dict[str, Any]](self.ttl_minutes)
        return self.assets_cache[cache_key]
    
    def get_categories_cache(self, asset_type: str) -> DataCache[Dict[str, int]]:
        """Get or create categories cache for a specific asset type"""
        if asset_type not in self.categories_cache:
            self.categories_cache[asset_type] = DataCache[Dict[str, int]](self.ttl_minutes)
        return self.categories_cache[asset_type]
    
    def invalidate_all(self) -> None:
        """Invalidate all caches"""
        logger.info("Invalidating all PolyHaven caches")
        self.types_cache.invalidate()
        
        for cache in self.assets_cache.values():
            cache.invalidate()
        
        for cache in self.categories_cache.values():
            cache.invalidate()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about cache usage"""
        stats = {
            "types_cached": self.types_cache.is_cached,
            "types_age": self.types_cache.get_cache_age(),
            "assets_caches": len(self.assets_cache),
            "categories_caches": len(self.categories_cache),
            "cache_details": {}
        }
        
        for key, cache in self.assets_cache.items():
            stats["cache_details"][f"assets_{key}"] = {
                "cached": cache.is_cached,
                "age": cache.get_cache_age()
            }
        
        for key, cache in self.categories_cache.items():
            stats["cache_details"][f"categories_{key}"] = {
                "cached": cache.is_cached,
                "age": cache.get_cache_age()
            }
        
        return stats
