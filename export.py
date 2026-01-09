"""
Data Export and Reporting Features
Developer: Molla Samser
Design & Testing: Rima Khatun
Company: RSK World
Year: 2026
Website: https://rskworld.in
"""

import csv
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sqlite3
from io import StringIO, BytesIO
import zipfile
from analytics import NewsAnalytics
from auth import UserPreferences
from search import advanced_search

class DataExporter:
    def __init__(self):
        self.analytics = NewsAnalytics()
        self.user_prefs = UserPreferences()
        self.search = advanced_search
    
    def export_user_data(self, user_id: int, format_type: str = 'json') -> bytes:
        """Export all user data in specified format."""
        # Gather user data
        user_preferences = self.user_prefs.get_all_preferences(user_id)
        reading_history = self.user_prefs.get_reading_history(user_id, limit=1000)
        reading_stats = self.user_prefs.get_reading_stats(user_id, days=365)
        
        user_data = {
            'user_id': user_id,
            'export_date': datetime.now().isoformat(),
            'preferences': user_preferences,
            'reading_history': reading_history,
            'reading_stats': reading_stats
        }
        
        if format_type.lower() == 'json':
            return self._export_json(user_data)
        elif format_type.lower() == 'csv':
            return self._export_user_csv(user_data)
        elif format_type.lower() == 'xml':
            return self._export_xml(user_data, 'user_data')
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def export_analytics_data(self, days: int = 30, format_type: str = 'json') -> bytes:
        """Export analytics data for specified period."""
        # Gather analytics data
        sentiment_trends = self.analytics.get_sentiment_trends(days)
        category_analytics = self.analytics.get_category_analytics()
        trending_topics = self.analytics.analyze_trending_topics(days)
        search_analytics = self.search.get_search_analytics(days)
        
        analytics_data = {
            'export_date': datetime.now().isoformat(),
            'period_days': days,
            'sentiment_trends': sentiment_trends,
            'category_analytics': category_analytics,
            'trending_topics': trending_topics,
            'search_analytics': search_analytics
        }
        
        if format_type.lower() == 'json':
            return self._export_json(analytics_data)
        elif format_type.lower() == 'csv':
            return self._export_analytics_csv(analytics_data)
        elif format_type.lower() == 'xml':
            return self._export_xml(analytics_data, 'analytics_data')
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def export_news_articles(self, category: Optional[str] = None, 
                          date_from: Optional[str] = None, 
                          date_to: Optional[str] = None,
                          format_type: str = 'json') -> bytes:
        """Export news articles with filters."""
        # This would typically query the database
        # For now, we'll create a mock export structure
        
        articles_data = {
            'export_date': datetime.now().isoformat(),
            'filters': {
                'category': category,
                'date_from': date_from,
                'date_to': date_to
            },
            'articles': []  # Would contain actual article data
        }
        
        if format_type.lower() == 'json':
            return self._export_json(articles_data)
        elif format_type.lower() == 'csv':
            return self._export_articles_csv(articles_data)
        elif format_type.lower() == 'xml':
            return self._export_xml(articles_data, 'articles_data')
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def create_full_backup(self, include_user_data: bool = False) -> bytes:
        """Create a complete backup of all system data."""
        backup_data = {
            'backup_date': datetime.now().isoformat(),
            'version': '1.0',
            'analytics': json.loads(self.export_analytics_data(365, 'json').decode()),
            'search_index': [],  # Would include search index data
            'cache_stats': {},   # Would include cache statistics
        }
        
        if include_user_data:
            # This would include all user data (with proper privacy considerations)
            backup_data['users'] = []  # Would contain anonymized user data
        
        # Create ZIP file with multiple formats
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add JSON backup
            json_data = self._export_json(backup_data)
            zip_file.writestr('backup.json', json_data)
            
            # Add CSV exports
            analytics_csv = self._export_analytics_csv(backup_data['analytics'])
            zip_file.writestr('analytics.csv', analytics_csv)
            
            # Add XML export
            analytics_xml = self._export_xml(backup_data['analytics'], 'analytics')
            zip_file.writestr('analytics.xml', analytics_xml)
            
            # Add metadata
            metadata = {
                'created_by': 'News Summary Bot',
                'developer': 'Molla Samser',
                'company': 'RSK World',
                'website': 'https://rskworld.in',
                'export_date': datetime.now().isoformat(),
                'file_count': 3,
                'formats': ['json', 'csv', 'xml']
            }
            zip_file.writestr('metadata.json', json.dumps(metadata, indent=2))
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
    
    def _export_json(self, data: Dict) -> bytes:
        """Export data as JSON."""
        return json.dumps(data, indent=2, default=str).encode('utf-8')
    
    def _export_xml(self, data: Dict, root_name: str) -> bytes:
        """Export data as XML."""
        root = ET.Element(root_name)
        
        def dict_to_xml(parent, data):
            if isinstance(data, dict):
                for key, value in data.items():
                    child = ET.SubElement(parent, key)
                    dict_to_xml(child, value)
            elif isinstance(data, list):
                for item in data:
                    child = ET.SubElement(parent, 'item')
                    dict_to_xml(child, item)
            else:
                parent.text = str(data)
        
        dict_to_xml(root, data)
        
        xml_str = ET.tostring(root, encoding='unicode')
        return xml_str.encode('utf-8')
    
    def _export_user_csv(self, user_data: Dict) -> bytes:
        """Export user data as CSV."""
        output = StringIO()
        
        # Export reading history
        if user_data.get('reading_history'):
            writer = csv.writer(output)
            writer.writerow(['Article ID', 'Title', 'Category', 'Read At', 'Reading Time'])
            
            for item in user_data['reading_history']:
                writer.writerow([
                    item.get('article_id'),
                    item.get('article_title'),
                    item.get('category'),
                    item.get('read_at'),
                    item.get('reading_time')
                ])
        
        return output.getvalue().encode('utf-8')
    
    def _export_analytics_csv(self, analytics_data: Dict) -> bytes:
        """Export analytics data as CSV."""
        output = StringIO()
        writer = csv.writer(output)
        
        # Export sentiment trends
        if analytics_data.get('sentiment_trends'):
            writer.writerow(['Date', 'Positive', 'Negative', 'Neutral'])
            for date, sentiments in analytics_data['sentiment_trends'].items():
                writer.writerow([
                    date,
                    sentiments.get('Positive', 0),
                    sentiments.get('Negative', 0),
                    sentiments.get('Neutral', 0)
                ])
        
        return output.getvalue().encode('utf-8')
    
    def _export_articles_csv(self, articles_data: Dict) -> bytes:
        """Export articles data as CSV."""
        output = StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['ID', 'Title', 'Category', 'Source', 'Published At', 'Sentiment', 'Reliability'])
        
        for article in articles_data.get('articles', []):
            writer.writerow([
                article.get('id'),
                article.get('title'),
                article.get('category'),
                article.get('source'),
                article.get('published_at'),
                article.get('sentiment'),
                article.get('reliability_score')
            ])
        
        return output.getvalue().encode('utf-8')

class ReportGenerator:
    """Generate various reports from system data."""
    
    def __init__(self):
        self.analytics = NewsAnalytics()
        self.search = advanced_search
    
    def generate_usage_report(self, days: int = 30) -> Dict:
        """Generate comprehensive usage report."""
        # Gather usage statistics
        sentiment_trends = self.analytics.get_sentiment_trends(days)
        category_analytics = self.analytics.get_category_analytics()
        search_analytics = self.search.get_search_analytics(days)
        
        # Calculate summary statistics
        total_searches = search_analytics.get('total_searches', 0)
        top_category = max(category_analytics.items(), key=lambda x: x[1].get('total_articles', 0)) if category_analytics else None
        
        report = {
            'report_type': 'usage_report',
            'period_days': days,
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_searches': total_searches,
                'top_category': top_category[0] if top_category else None,
                'total_categories': len(category_analytics),
                'avg_daily_searches': total_searches / days if days > 0 else 0
            },
            'detailed_analytics': {
                'sentiment_trends': sentiment_trends,
                'category_analytics': category_analytics,
                'search_analytics': search_analytics
            },
            'insights': self._generate_insights(sentiment_trends, category_analytics, search_analytics)
        }
        
        return report
    
    def generate_performance_report(self) -> Dict:
        """Generate system performance report."""
        # This would typically include performance metrics
        report = {
            'report_type': 'performance_report',
            'generated_at': datetime.now().isoformat(),
            'metrics': {
                'cache_hit_rate': 85.5,  # Mock data
                'avg_response_time': 0.234,  # seconds
                'api_calls_today': 1250,
                'error_rate': 0.02,  # 2%
                'uptime_percentage': 99.9
            },
            'recommendations': [
                'Consider increasing cache size for better performance',
                'Monitor API rate limits during peak hours',
                'Regular database maintenance recommended'
            ]
        }
        
        return report
    
    def generate_user_engagement_report(self, days: int = 30) -> Dict:
        """Generate user engagement report."""
        # This would typically analyze user engagement patterns
        report = {
            'report_type': 'user_engagement_report',
            'period_days': days,
            'generated_at': datetime.now().isoformat(),
            'metrics': {
                'active_users': 342,
                'new_users': 28,
                'avg_session_duration': 5.5,  # minutes
                'articles_per_user': 12.3,
                'summary_requests': 890,
                'search_queries': 456
            },
            'engagement_trends': {
                'daily_active_users': [12, 15, 18, 14, 20, 22, 19],  # Last 7 days
                'peak_hours': [9, 10, 14, 15, 20, 21],  # Most active hours
                'popular_categories': ['technology', 'business', 'health']
            }
        }
        
        return report
    
    def _generate_insights(self, sentiment_data: Dict, category_data: Dict, search_data: Dict) -> List[str]:
        """Generate insights from analytics data."""
        insights = []
        
        # Sentiment insights
        if sentiment_data:
            recent_sentiments = list(sentiment_data.values())[-7:] if len(sentiment_data) >= 7 else list(sentiment_data.values())
            if recent_sentiments:
                avg_positive = sum(s.get('Positive', 0) for s in recent_sentiments) / len(recent_sentiments)
                avg_negative = sum(s.get('Negative', 0) for s in recent_sentiments) / len(recent_sentiments)
                
                if avg_positive > avg_negative:
                    insights.append("News sentiment has been predominantly positive recently")
                elif avg_negative > avg_positive:
                    insights.append("News sentiment has been predominantly negative recently")
        
        # Category insights
        if category_data:
            top_category = max(category_data.items(), key=lambda x: x[1].get('total_articles', 0))
            insights.append(f"Most popular category: {top_category[0]} with {top_category[1].get('total_articles', 0)} articles")
        
        # Search insights
        if search_data.get('top_queries'):
            top_query = search_data['top_queries'][0]
            insights.append(f"Most searched topic: '{top_query['query']}' with {top_query['count']} searches")
        
        return insights

# Initialize global exporter and report generator
data_exporter = DataExporter()
report_generator = ReportGenerator()

# Developer Details
# Created by Molla Samser (RSK World)
# 2026
