"""
Advanced Search System with Filters and Sorting
Developer: Molla Samser
Design & Testing: Rima Khatun
Company: RSK World
Year: 2026
Website: https://rskworld.in
"""

import re
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import sqlite3

class AdvancedSearch:
    def __init__(self, db_path='search_index.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize search index database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Search index table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT,
                source TEXT,
                author TEXT,
                published_at TIMESTAMP,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                keywords TEXT,
                sentiment TEXT,
                reliability_score INTEGER,
                word_count INTEGER,
                language TEXT,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Full-text search virtual table
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
                title, content, keywords, category, source, author,
                content='search_index', content_rowid='id'
            )
        ''')
        
        # Search history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                query TEXT,
                filters TEXT,
                results_count INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Popular searches
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS popular_searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                search_count INTEGER DEFAULT 1,
                last_searched TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def index_article(self, article_data: Dict) -> bool:
        """Index an article for search."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Extract keywords from content
            keywords = self._extract_keywords(article_data.get('content', ''))
            
            # Insert into main index
            cursor.execute('''
                INSERT OR REPLACE INTO search_index 
                (article_id, title, content, category, source, author, published_at,
                 keywords, sentiment, reliability_score, word_count, language)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                article_data.get('article_id'),
                article_data.get('title'),
                article_data.get('content'),
                article_data.get('category'),
                article_data.get('source'),
                article_data.get('author'),
                article_data.get('published_at'),
                json.dumps(keywords),
                article_data.get('sentiment'),
                article_data.get('reliability_score'),
                article_data.get('word_count'),
                article_data.get('language')
            ))
            
            # Insert into full-text search
            cursor.execute('''
                INSERT OR REPLACE INTO articles_fts 
                (title, content, keywords, category, source, author)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                article_data.get('title'),
                article_data.get('content'),
                json.dumps(keywords),
                article_data.get('category'),
                article_data.get('source'),
                article_data.get('author')
            ))
            
            conn.commit()
            conn.close()
            return True
        
        except Exception as e:
            print(f"Error indexing article: {e}")
            return False
    
    def _extract_keywords(self, text: str, max_keywords: int = 20) -> List[str]:
        """Extract keywords from text."""
        # Clean and tokenize
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter stop words
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had',
            'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his',
            'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'way', 'who',
            'boy', 'did', 'use', 'her', 'make', 'than', 'them', 'way', 'many',
            'after', 'also', 'back', 'call', 'come', 'even', 'from', 'give',
            'hand', 'help', 'keep', 'last', 'leave', 'most', 'move', 'much',
            'need', 'only', 'over', 'said', 'same', 'take', 'tell', 'that',
            'their', 'there', 'well', 'were', 'what', 'when', 'will', 'with',
            'your', 'been', 'called', 'could', 'find', 'into', 'look', 'more',
            'must', 'other', 'should', 'still', 'such', 'time', 'very', 'want'
        }
        
        filtered_words = [word for word in words if word not in stop_words]
        
        # Count frequency and return top keywords
        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        return [word for word, count in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:max_keywords]]
    
    def search(self, query: str, filters: Optional[Dict] = None, sort_by: str = 'relevance', 
               limit: int = 20, offset: int = 0) -> Dict:
        """Perform advanced search with filters and sorting."""
        
        # Build search query
        base_query = """
            SELECT si.article_id, si.title, si.content, si.category, si.source,
                   si.author, si.published_at, si.sentiment, si.reliability_score,
                   si.word_count, si.language,
                   articles_fts.rank as search_rank
            FROM search_index si
            JOIN articles_fts ON si.id = articles_fts.rowid
            WHERE si.is_active = 1
        """
        
        params = []
        conditions = []
        
        # Add text search condition
        if query:
            conditions.append("articles_fts MATCH ?")
            params.append(query)
        
        # Apply filters
        if filters:
            if filters.get('category'):
                conditions.append("si.category = ?")
                params.append(filters['category'])
            
            if filters.get('source'):
                conditions.append("si.source = ?")
                params.append(filters['source'])
            
            if filters.get('sentiment'):
                conditions.append("si.sentiment = ?")
                params.append(filters['sentiment'])
            
            if filters.get('language'):
                conditions.append("si.language = ?")
                params.append(filters['language'])
            
            if filters.get('min_reliability'):
                conditions.append("si.reliability_score >= ?")
                params.append(filters['min_reliability'])
            
            if filters.get('date_from'):
                conditions.append("si.published_at >= ?")
                params.append(filters['date_from'])
            
            if filters.get('date_to'):
                conditions.append("si.published_at <= ?")
                params.append(filters['date_to'])
        
        # Combine conditions
        if conditions:
            base_query += " AND " + " AND ".join(conditions)
        
        # Add sorting
        if sort_by == 'relevance':
            base_query += " ORDER BY search_rank DESC"
        elif sort_by == 'date':
            base_query += " ORDER BY si.published_at DESC"
        elif sort_by == 'reliability':
            base_query += " ORDER BY si.reliability_score DESC"
        elif sort_by == 'popularity':
            base_query += " ORDER BY si.word_count DESC"
        
        # Add pagination
        base_query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        # Execute search
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(base_query, params)
            results = cursor.fetchall()
            
            # Get total count for pagination
            count_query = base_query.replace(
                "SELECT si.article_id, si.title, si.content, si.category, si.source, si.author, si.published_at, si.sentiment, si.reliability_score, si.word_count, si.language, articles_fts.rank as search_rank",
                "SELECT COUNT(*)"
            ).replace("ORDER BY.*LIMIT.*OFFSET.*", "")
            
            cursor.execute(count_query, params[:-2])  # Remove limit and offset params
            total_count = cursor.fetchone()[0]
            
            # Format results
            articles = []
            for row in results:
                articles.append({
                    'article_id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'category': row[3],
                    'source': row[4],
                    'author': row[5],
                    'published_at': row[6],
                    'sentiment': row[7],
                    'reliability_score': row[8],
                    'word_count': row[9],
                    'language': row[10],
                    'search_rank': row[11]
                })
            
            return {
                'articles': articles,
                'total_count': total_count,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total_count
            }
        
        except Exception as e:
            return {
                'articles': [],
                'total_count': 0,
                'error': str(e)
            }
        finally:
            if conn:
                conn.close()
    
    def get_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """Get search suggestions based on partial query."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get suggestions from titles and keywords
            cursor.execute('''
                SELECT DISTINCT title, keywords FROM search_index 
                WHERE title LIKE ? OR keywords LIKE ?
                LIMIT ?
            ''', (f'%{query}%', f'%{query}%', limit * 2))
            
            results = cursor.fetchall()
            conn.close()
            
            suggestions = []
            for title, keywords in results:
                # Add title suggestion
                if query.lower() in title.lower():
                    suggestions.append(title)
                
                # Add keyword suggestions
                if keywords:
                    keyword_list = json.loads(keywords)
                    for keyword in keyword_list:
                        if query.lower() in keyword.lower() and keyword not in suggestions:
                            suggestions.append(keyword)
            
            return suggestions[:limit]
        
        except Exception as e:
            conn.close()
            return []
    
    def get_popular_searches(self, limit: int = 10) -> List[Dict]:
        """Get popular search queries."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT query, search_count, last_searched 
            FROM popular_searches 
            ORDER BY search_count DESC, last_searched DESC 
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'query': row[0],
                'count': row[1],
                'last_searched': row[2]
            }
            for row in results
        ]
    
    def track_search(self, user_id: Optional[str], query: str, filters: Dict, results_count: int):
        """Track search query for analytics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Add to search history
        cursor.execute('''
            INSERT INTO search_history (user_id, query, filters, results_count)
            VALUES (?, ?, ?, ?)
        ''', (user_id, query, json.dumps(filters), results_count))
        
        # Update popular searches
        cursor.execute('''
            INSERT OR REPLACE INTO popular_searches (query, search_count, last_searched)
            VALUES (?, 
                    COALESCE((SELECT search_count FROM popular_searches WHERE query = ?), 0) + 1,
                    ?)
        ''', (query, query, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def get_search_analytics(self, days: int = 30) -> Dict:
        """Get search analytics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Total searches
        cursor.execute('''
            SELECT COUNT(*) FROM search_history 
            WHERE timestamp >= ?
        ''', (cutoff_date,))
        total_searches = cursor.fetchone()[0]
        
        # Top queries
        cursor.execute('''
            SELECT query, COUNT(*) as count 
            FROM search_history 
            WHERE timestamp >= ?
            GROUP BY query 
            ORDER BY count DESC 
            LIMIT 10
        ''', (cutoff_date,))
        top_queries = [{'query': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Search trends over time
        cursor.execute('''
            SELECT DATE(timestamp) as date, COUNT(*) as count
            FROM search_history 
            WHERE timestamp >= ?
            GROUP BY DATE(timestamp)
            ORDER BY date
        ''', (cutoff_date,))
        search_trends = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_searches': total_searches,
            'top_queries': top_queries,
            'search_trends': search_trends
        }

class SearchFilters:
    """Search filter definitions and validation."""
    
    CATEGORIES = ['general', 'business', 'technology', 'entertainment', 'health', 'science', 'sports']
    SENTIMENTS = ['Positive', 'Negative', 'Neutral']
    LANGUAGES = ['English', 'Hindi', 'Spanish', 'French', 'German']
    SORT_OPTIONS = ['relevance', 'date', 'reliability', 'popularity']
    
    @staticmethod
    def validate_filters(filters: Dict) -> Dict:
        """Validate and normalize search filters."""
        validated = {}
        
        if filters.get('category') in SearchFilters.CATEGORIES:
            validated['category'] = filters['category']
        
        if filters.get('sentiment') in SearchFilters.SENTIMENTS:
            validated['sentiment'] = filters['sentiment']
        
        if filters.get('language') in SearchFilters.LANGUAGES:
            validated['language'] = filters['language']
        
        if filters.get('sort_by') in SearchFilters.SORT_OPTIONS:
            validated['sort_by'] = filters['sort_by']
        
        # Validate numeric filters
        try:
            if filters.get('min_reliability'):
                reliability = int(filters['min_reliability'])
                if 0 <= reliability <= 100:
                    validated['min_reliability'] = reliability
        except (ValueError, TypeError):
            pass
        
        # Validate date filters
        for date_field in ['date_from', 'date_to']:
            if filters.get(date_field):
                try:
                    # Basic date validation - could be enhanced
                    datetime.strptime(filters[date_field], '%Y-%m-%d')
                    validated[date_field] = filters[date_field]
                except ValueError:
                    pass
        
        return validated

# Initialize global search instance
advanced_search = AdvancedSearch()

# Developer Details
# Created by Molla Samser (RSK World)
# 2026
