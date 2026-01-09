"""
Caching System for News Summary Bot
Developer: Molla Samser
Design & Testing: Rima Khatun
Company: RSK World
Year: 2026
Website: https://rskworld.in
"""

import time
import json
import hashlib
import sqlite3
from datetime import datetime, timedelta
from threading import Lock
import os

class CacheManager:
    def __init__(self, db_path='cache.db', default_ttl=300):
        self.db_path = db_path
        self.default_ttl = default_ttl
        self.lock = Lock()
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for caching."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache_entries (
                key TEXT PRIMARY KEY,
                value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache_stats (
                id INTEGER PRIMARY KEY,
                total_hits INTEGER DEFAULT 0,
                total_misses INTEGER DEFAULT 0,
                total_entries INTEGER DEFAULT 0,
                last_cleanup TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Initialize stats if not exists
        cursor.execute('SELECT COUNT(*) FROM cache_stats')
        if cursor.fetchone()[0] == 0:
            cursor.execute('INSERT INTO cache_stats (id) VALUES (1)')
        
        conn.commit()
        conn.close()
    
    def _generate_key(self, prefix, *args, **kwargs):
        """Generate a unique cache key."""
        key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key):
        """Get value from cache."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT value, expires_at FROM cache_entries 
                WHERE key = ? AND (expires_at IS NULL OR expires_at > ?)
            ''', (key, datetime.now()))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                # Update access statistics
                self._update_access_stats(key, hit=True)
                return json.loads(result[0])
            else:
                self._update_access_stats(key, hit=False)
                return None
    
    def set(self, key, value, ttl=None):
        """Set value in cache with optional TTL."""
        if ttl is None:
            ttl = self.default_ttl
        
        expires_at = datetime.now() + timedelta(seconds=ttl) if ttl > 0 else None
        
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO cache_entries 
                (key, value, expires_at, created_at, last_accessed)
                VALUES (?, ?, ?, ?, ?)
            ''', (key, json.dumps(value), expires_at, datetime.now(), datetime.now()))
            
            conn.commit()
            conn.close()
    
    def delete(self, key):
        """Delete specific key from cache."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM cache_entries WHERE key = ?', (key,))
            
            conn.commit()
            conn.close()
    
    def clear(self):
        """Clear all cache entries."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM cache_entries')
            
            conn.commit()
            conn.close()
    
    def cleanup_expired(self):
        """Remove expired entries from cache."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM cache_entries 
                WHERE expires_at IS NOT NULL AND expires_at <= ?
            ''', (datetime.now(),))
            
            # Update cleanup timestamp
            cursor.execute('''
                UPDATE cache_stats SET last_cleanup = ?
                WHERE id = 1
            ''', (datetime.now(),))
            
            conn.commit()
            conn.close()
    
    def get_stats(self):
        """Get cache statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get overall stats
        cursor.execute('''
            SELECT total_hits, total_misses, total_entries, last_cleanup
            FROM cache_stats WHERE id = 1
        ''')
        stats = cursor.fetchone()
        
        # Get current entry count
        cursor.execute('SELECT COUNT(*) FROM cache_entries')
        current_entries = cursor.fetchone()[0]
        
        # Get cache size
        cursor.execute('''
            SELECT SUM(LENGTH(value)) FROM cache_entries
        ''')
        cache_size = cursor.fetchone()[0] or 0
        
        conn.close()
        
        if stats:
            hit_rate = (stats[0] / (stats[0] + stats[1]) * 100) if (stats[0] + stats[1]) > 0 else 0
            
            return {
                'total_hits': stats[0],
                'total_misses': stats[1],
                'total_entries': stats[2],
                'current_entries': current_entries,
                'cache_size_bytes': cache_size,
                'cache_size_mb': round(cache_size / (1024 * 1024), 2),
                'hit_rate': round(hit_rate, 2),
                'last_cleanup': stats[3]
            }
        
        return None
    
    def _update_access_stats(self, key, hit=True):
        """Update access statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if hit:
            # Update hit count and last accessed for the entry
            cursor.execute('''
                UPDATE cache_entries 
                SET access_count = access_count + 1, last_accessed = ?
                WHERE key = ?
            ''', (datetime.now(), key))
            
            # Update global hit count
            cursor.execute('''
                UPDATE cache_stats 
                SET total_hits = total_hits + 1
                WHERE id = 1
            ''')
        else:
            # Update global miss count
            cursor.execute('''
                UPDATE cache_stats 
                SET total_misses = total_misses + 1
                WHERE id = 1
            ''')
        
        # Update total entries count
        cursor.execute('SELECT COUNT(*) FROM cache_entries')
        current_count = cursor.fetchone()[0]
        cursor.execute('''
            UPDATE cache_stats 
            SET total_entries = ?
            WHERE id = 1
        ''', (current_count,))
        
        conn.commit()
        conn.close()

class NewsCache:
    """Specialized cache for news data."""
    
    def __init__(self, cache_manager):
        self.cache = cache_manager
    
    def get_news(self, category='general', query=None, country='us'):
        """Get cached news data."""
        key = self.cache._generate_key('news', category, query, country)
        return self.cache.get(key)
    
    def set_news(self, category='general', query=None, country='us', data=None, ttl=300):
        """Cache news data."""
        if data is None:
            return
        
        key = self.cache._generate_key('news', category, query, country)
        self.cache.set(key, data, ttl)
    
    def get_summary(self, content_hash, language='English'):
        """Get cached summary."""
        key = self.cache._generate_key('summary', content_hash, language)
        return self.cache.get(key)
    
    def set_summary(self, content_hash, language='English', summary=None, ttl=3600):
        """Cache summary."""
        if summary is None:
            return
        
        key = self.cache._generate_key('summary', content_hash, language)
        self.cache.set(key, summary, ttl)
    
    def get_sentiment(self, content_hash):
        """Get cached sentiment analysis."""
        key = self.cache._generate_key('sentiment', content_hash)
        return self.cache.get(key)
    
    def set_sentiment(self, content_hash, sentiment=None, ttl=3600):
        """Cache sentiment analysis."""
        if sentiment is None:
            return
        
        key = self.cache._generate_key('sentiment', content_hash)
        self.cache.set(key, sentiment, ttl)
    
    def get_trending_topics(self, days=7):
        """Get cached trending topics."""
        key = self.cache._generate_key('trending', days)
        return self.cache.get(key)
    
    def set_trending_topics(self, days=7, topics=None, ttl=1800):
        """Cache trending topics."""
        if topics is None:
            return
        
        key = self.cache._generate_key('trending', days)
        self.cache.set(key, topics, ttl)
    
    def invalidate_category(self, category):
        """Invalidate all cache entries for a specific category."""
        # This is a simplified approach - in production, you might want
        # more sophisticated invalidation strategies
        patterns = [
            f"news:{category}:",
            f"trending:",
        ]
        
        conn = sqlite3.connect(self.cache.db_path)
        cursor = conn.cursor()
        
        for pattern in patterns:
            cursor.execute('DELETE FROM cache_entries WHERE key LIKE ?', (f'%{pattern}%',))
        
        conn.commit()
        conn.close()

# Cache decorator for functions
def cached(ttl=300, key_prefix=None):
    """Decorator to cache function results."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache_manager = getattr(wrapper, '_cache_manager', None)
            if not cache_manager:
                return func(*args, **kwargs)
            
            # Generate cache key
            prefix = key_prefix or func.__name__
            key = cache_manager._generate_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            result = cache_manager.get(key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(key, result, ttl)
            
            return result
        
        return wrapper
    return decorator

# Initialize global cache manager
cache_manager = CacheManager()
news_cache = NewsCache(cache_manager)

# Developer Details
# Created by Molla Samser (RSK World)
# 2026
