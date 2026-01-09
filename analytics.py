"""
Advanced Analytics and NLP Processing Module
Developer: Molla Samser
Design & Testing: Rima Khatun
Company: RSK World
Year: 2026
Website: https://rskworld.in
"""

import re
import json
import sqlite3
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import statistics

class NewsAnalytics:
    def __init__(self, db_path='news_analytics.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for analytics storage."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tables for analytics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                category TEXT,
                sentiment TEXT,
                reliability_score INTEGER,
                word_count INTEGER,
                language TEXT,
                keywords TEXT,
                source TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT,
                action TEXT,
                category TEXT,
                search_query TEXT,
                article_id TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def extract_keywords(self, text, max_keywords=10):
        """Extract keywords from text using simple frequency analysis."""
        # Clean and tokenize text
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        
        # Filter out common stop words
        stop_words = {'that', 'this', 'with', 'from', 'they', 'have', 'been', 
                     'said', 'each', 'which', 'their', 'time', 'will', 'about', 
                     'would', 'there', 'could', 'other', 'more', 'after', 'first',
                     'also', 'most', 'over', 'such', 'only', 'many', 'some', 'these'}
        
        filtered_words = [word for word in words if word not in stop_words]
        
        # Count frequency and return top keywords
        word_freq = Counter(filtered_words)
        return [word for word, count in word_freq.most_common(max_keywords)]
    
    def analyze_trending_topics(self, days=7):
        """Analyze trending topics over the past N days."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cursor.execute('''
            SELECT keywords, category, COUNT(*) as frequency
            FROM news_analytics 
            WHERE timestamp >= ?
            GROUP BY keywords, category
            ORDER BY frequency DESC
            LIMIT 20
        ''', (cutoff_date,))
        
        results = cursor.fetchall()
        conn.close()
        
        trending = []
        for keywords, category, freq in results:
            if keywords:
                keyword_list = json.loads(keywords)
                trending.append({
                    'keywords': keyword_list,
                    'category': category,
                    'frequency': freq
                })
        
        return trending
    
    def get_sentiment_trends(self, days=30):
        """Get sentiment analysis trends over time."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cursor.execute('''
            SELECT DATE(timestamp) as date, sentiment, COUNT(*) as count
            FROM news_analytics 
            WHERE timestamp >= ?
            GROUP BY DATE(timestamp), sentiment
            ORDER BY date
        ''', (cutoff_date,))
        
        results = cursor.fetchall()
        conn.close()
        
        # Organize data by date
        trends = defaultdict(lambda: {'Positive': 0, 'Negative': 0, 'Neutral': 0})
        for date, sentiment, count in results:
            trends[date][sentiment] = count
        
        return dict(trends)
    
    def get_category_analytics(self):
        """Get analytics breakdown by category."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT category, 
                   AVG(reliability_score) as avg_reliability,
                   AVG(word_count) as avg_word_count,
                   COUNT(*) as article_count,
                   sentiment
            FROM news_analytics 
            GROUP BY category, sentiment
            ORDER BY category
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        analytics = {}
        for category, reliability, word_count, count, sentiment in results:
            if category not in analytics:
                analytics[category] = {
                    'total_articles': 0,
                    'avg_reliability': 0,
                    'avg_word_count': 0,
                    'sentiments': {'Positive': 0, 'Negative': 0, 'Neutral': 0}
                }
            
            analytics[category]['total_articles'] += count
            analytics[category]['sentiments'][sentiment] = count
            analytics[category]['avg_reliability'] = max(analytics[category]['avg_reliability'], reliability)
            analytics[category]['avg_word_count'] = max(analytics[category]['avg_word_count'], word_count)
        
        return analytics
    
    def track_user_interaction(self, user_id, action, category=None, search_query=None, article_id=None):
        """Track user interactions for analytics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_interactions 
            (user_id, action, category, search_query, article_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, action, category, search_query, article_id))
        
        conn.commit()
        conn.close()
    
    def get_user_activity_summary(self, user_id=None, days=30):
        """Get summary of user activity."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        if user_id:
            cursor.execute('''
                SELECT action, category, COUNT(*) as count
                FROM user_interactions 
                WHERE user_id = ? AND timestamp >= ?
                GROUP BY action, category
                ORDER BY count DESC
            ''', (user_id, cutoff_date))
        else:
            cursor.execute('''
                SELECT action, category, COUNT(*) as count
                FROM user_interactions 
                WHERE timestamp >= ?
                GROUP BY action, category
                ORDER BY count DESC
            ''', (cutoff_date,))
        
        results = cursor.fetchall()
        conn.close()
        
        summary = {}
        for action, category, count in results:
            key = f"{action}_{category}" if category else action
            summary[key] = count
        
        return summary
    
    def store_article_analysis(self, article_data):
        """Store analysis results for an article."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO news_analytics 
            (category, sentiment, reliability_score, word_count, language, keywords, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            article_data.get('category'),
            article_data.get('sentiment'),
            article_data.get('reliability_score'),
            article_data.get('word_count'),
            article_data.get('language'),
            json.dumps(article_data.get('keywords', [])),
            article_data.get('source')
        ))
        
        conn.commit()
        conn.close()

# Advanced NLP Features
class AdvancedNLP:
    def __init__(self):
        self.emotion_keywords = {
            'joy': ['happy', 'excited', 'delighted', 'pleased', 'satisfied', 'thrilled'],
            'anger': ['angry', 'furious', 'outraged', 'irritated', 'frustrated', 'annoyed'],
            'fear': ['afraid', 'scared', 'terrified', 'worried', 'anxious', 'concerned'],
            'sadness': ['sad', 'depressed', 'disappointed', 'upset', 'grief', 'sorrow'],
            'surprise': ['surprised', 'shocked', 'amazed', 'astonished', 'stunned']
        }
    
    def detect_emotions(self, text):
        """Detect emotions in text based on keyword analysis."""
        text_lower = text.lower()
        emotion_scores = {}
        
        for emotion, keywords in self.emotion_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            emotion_scores[emotion] = score
        
        # Return the dominant emotion
        if max(emotion_scores.values()) == 0:
            return 'neutral'
        
        return max(emotion_scores, key=emotion_scores.get)
    
    def calculate_readability_score(self, text):
        """Calculate simple readability score based on sentence length and word complexity."""
        sentences = text.split('.')
        words = text.split()
        
        if not sentences or not words:
            return 0
        
        avg_sentence_length = len(words) / len(sentences)
        complex_words = len([w for w in words if len(w) > 6])
        
        # Simple readability formula (lower is more readable)
        readability = (avg_sentence_length + (complex_words / len(words)) * 100) / 2
        return max(0, min(100, 100 - readability))
    
    def extract_entities(self, text):
        """Extract potential entities (simple pattern matching)."""
        entities = {
            'organizations': [],
            'locations': [],
            'dates': [],
            'persons': []
        }
        
        # Simple patterns for entity extraction
        # Organizations (capitalized words followed by Inc, Corp, Ltd, etc.)
        org_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Inc|Corp|Ltd|LLC|Company)\b'
        entities['organizations'] = re.findall(org_pattern, text)
        
        # Dates (simple date patterns)
        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}\b'
        entities['dates'] = re.findall(date_pattern, text)
        
        # Locations (capitalized words followed by city/state indicators)
        loc_pattern = r'\b([A-Z][a-z]+),\s*[A-Z]{2}\b'
        entities['locations'] = re.findall(loc_pattern, text)
        
        return entities

# Developer Details
# Created by Molla Samser (RSK World)
# 2026
