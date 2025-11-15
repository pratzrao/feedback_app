"""
Cache Helper Utilities
Implements safe caching strategies as outlined in CACHING_STRATEGY.md
"""

import streamlit as st
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from services.db_helper import get_connection


class SafeCache:
    """
    Ultra-safe caching utility that prioritizes data freshness over performance.
    Implements the approved caching strategy from CACHING_STRATEGY.md.
    """
    
    @staticmethod
    def get_page_cache_key(base_key: str) -> str:
        """Generate a page-specific cache key that auto-clears between page loads."""
        page_id = st.session_state.get('page_load_id', 'unknown')
        return f"page_cache_{page_id}_{base_key}"
    
    @staticmethod
    def init_page_cache():
        """Initialize page-level cache that auto-clears on new page loads."""
        # Generate unique page ID for this session/page load
        current_time = int(time.time() * 1000)  # Millisecond precision
        if 'page_load_id' not in st.session_state:
            st.session_state['page_load_id'] = current_time
        
        # Clean up old page caches (keep only current page cache)
        keys_to_remove = []
        current_page_id = str(st.session_state['page_load_id'])
        
        for key in st.session_state.keys():
            if key.startswith('page_cache_') and current_page_id not in key:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del st.session_state[key]
    
    @staticmethod
    def get_page_cached_data(key: str, fetch_function: Callable, *args, **kwargs) -> Any:
        """
        Get data from page-level cache or fetch fresh if not available.
        Cache automatically clears when user navigates to new page.
        
        Args:
            key: Unique identifier for this cached data
            fetch_function: Function to call if cache miss
            *args, **kwargs: Arguments to pass to fetch_function
            
        Returns:
            Cached data or fresh data from fetch_function
        """
        SafeCache.init_page_cache()
        cache_key = SafeCache.get_page_cache_key(key)
        
        if cache_key not in st.session_state:
            # Cache miss - fetch fresh data
            fresh_data = fetch_function(*args, **kwargs)
            st.session_state[cache_key] = fresh_data
            return fresh_data
        
        # Cache hit - return cached data
        return st.session_state[cache_key]
    
    @staticmethod
    def get_timed_cache(key: str, fetch_function: Callable, ttl_seconds: int = 3600, *args, **kwargs) -> Any:
        """
        Get data from time-based cache with TTL (Time To Live).
        Use only for static/reference data that changes infrequently.
        
        Args:
            key: Unique identifier for this cached data
            fetch_function: Function to call if cache miss or expired
            ttl_seconds: Cache duration in seconds (default: 1 hour)
            *args, **kwargs: Arguments to pass to fetch_function
            
        Returns:
            Cached data or fresh data from fetch_function
        """
        cache_key = f"timed_cache_{key}"
        cache_time_key = f"timed_cache_time_{key}"
        
        # Check if cache exists and is fresh
        if cache_key in st.session_state and cache_time_key in st.session_state:
            cache_age = time.time() - st.session_state[cache_time_key]
            if cache_age < ttl_seconds:
                return st.session_state[cache_key]
        
        # Cache expired or doesn't exist - refresh
        fresh_data = fetch_function(*args, **kwargs)
        st.session_state[cache_key] = fresh_data
        st.session_state[cache_time_key] = time.time()
        return fresh_data
    
    @staticmethod
    def invalidate_cache(pattern: str = None):
        """
        Invalidate caches matching a pattern.
        Use this after database writes that might affect cached data.
        
        Args:
            pattern: Cache key pattern to match (None = invalidate all caches)
        """
        keys_to_remove = []
        
        for key in st.session_state.keys():
            if pattern is None:
                # Remove all cache keys
                if key.startswith(('page_cache_', 'timed_cache_')):
                    keys_to_remove.append(key)
            else:
                # Remove keys matching pattern
                if key.startswith(('page_cache_', 'timed_cache_')) and pattern in key:
                    keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del st.session_state[key]
    
    @staticmethod
    def invalidate_user_related_caches():
        """Invalidate caches that might be affected by user data changes."""
        SafeCache.invalidate_cache('users')
        SafeCache.invalidate_cache('departments')
        SafeCache.invalidate_cache('verticals')
    
    @staticmethod
    def invalidate_cycle_related_caches():
        """Invalidate caches that might be affected by cycle data changes."""
        SafeCache.invalidate_cache('cycle')
        SafeCache.invalidate_cache('active_cycle')


# Safe caching functions for commonly used data
def get_cached_departments() -> List[Dict]:
    """Get department list with 1-hour cache (safe - rarely changes)."""
    def fetch_departments():
        conn = get_connection()
        return conn.execute(
            "SELECT DISTINCT vertical FROM users WHERE is_active = 1 AND vertical IS NOT NULL ORDER BY vertical"
        ).fetchall()
    
    return SafeCache.get_timed_cache('departments', fetch_departments, ttl_seconds=3600)

def get_cached_active_users() -> List[Dict]:
    """Get active users list with 5-minute cache (moderate risk)."""
    def fetch_active_users():
        conn = get_connection()
        return conn.execute(
            "SELECT user_type_id, first_name, last_name, email, vertical FROM users WHERE is_active = 1 ORDER BY first_name, last_name"
        ).fetchall()
    
    return SafeCache.get_timed_cache('active_users', fetch_active_users, ttl_seconds=300)  # 5 minutes

def get_cached_active_cycle() -> Optional[Dict]:
    """Get active cycle info with 1-hour cache (safe - changes infrequently)."""
    def fetch_active_cycle():
        from services.db_helper import get_active_review_cycle
        return get_active_review_cycle()
    
    return SafeCache.get_timed_cache('active_cycle', fetch_active_cycle, ttl_seconds=3600)

def get_cached_user_roles() -> List[Dict]:
    """Get role definitions with 24-hour cache (very safe - system config)."""
    def fetch_roles():
        conn = get_connection()
        return conn.execute(
            "SELECT role_id, role_name, description FROM roles ORDER BY role_name"
        ).fetchall()
    
    return SafeCache.get_timed_cache('roles', fetch_roles, ttl_seconds=86400)  # 24 hours

def get_page_cached_user_data(cache_key: str, query: str, params: tuple = ()) -> List[Dict]:
    """
    Get user data with page-level cache (ultra-safe - auto-clears on page change).
    Use this for data that might be used multiple times in a single page load.
    """
    def fetch_user_data():
        conn = get_connection()
        return conn.execute(query, params).fetchall()
    
    return SafeCache.get_page_cached_data(cache_key, fetch_user_data)


# Cache invalidation helpers (call these after database writes)
def invalidate_on_user_action(action_type: str, user_id: Optional[int] = None):
    """
    Invalidate appropriate caches when user takes an action.
    This preserves real-time functionality by clearing relevant caches.
    """
    if action_type == 'user_added' or action_type == 'user_modified':
        SafeCache.invalidate_user_related_caches()
        
    elif action_type == 'cycle_created' or action_type == 'cycle_modified':
        SafeCache.invalidate_cycle_related_caches()
        
    elif action_type in ['nomination_submitted', 'review_completed', 'approval_given']:
        # Don't invalidate anything - we don't cache these real-time status items
        pass  
    
    # For debugging - log cache invalidation
    # print(f"Cache invalidated for action: {action_type}")


# Manual cache management for admin use
def clear_all_caches():
    """Clear all caches. Use this for troubleshooting or after major data changes."""
    SafeCache.invalidate_cache()

def get_cache_stats() -> Dict[str, int]:
    """Get cache statistics for monitoring."""
    page_cache_count = len([k for k in st.session_state.keys() if k.startswith('page_cache_')])
    timed_cache_count = len([k for k in st.session_state.keys() if k.startswith('timed_cache_')])
    
    return {
        'page_cache_entries': page_cache_count,
        'timed_cache_entries': timed_cache_count,
        'total_session_keys': len(st.session_state.keys())
    }