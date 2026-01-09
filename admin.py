"""
Admin Panel for News Summary Bot
Developer: Molla Samser
Design & Testing: Rima Khatun
Company: RSK World
Year: 2026
Website: https://rskworld.in
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, flash
from functools import wraps
import json
from datetime import datetime, timedelta
from analytics import NewsAnalytics, AdvancedNLP
import os

# Create admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin credentials (in production, use proper authentication)
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

# Initialize analytics
analytics = NewsAnalytics()
nlp = AdvancedNLP()

def admin_required(f):
    """Decorator to require admin authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
def index():
    """Redirect to dashboard if logged in, otherwise to login."""
    if session.get('admin_logged_in'):
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('admin.login'))

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    """Admin logout."""
    session.clear()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('admin.login'))

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Main admin dashboard."""
    # Get key metrics
    total_articles = get_total_articles()
    total_users = get_total_users()
    avg_reliability = get_avg_reliability()
    trending_topics = analytics.analyze_trending_topics(days=7)
    
    # Get sentiment trends for the last 30 days
    sentiment_trends = analytics.get_sentiment_trends(days=30)
    
    # Get category analytics
    category_stats = analytics.get_category_analytics()
    
    return render_template('admin/dashboard.html',
                         total_articles=total_articles,
                         total_users=total_users,
                         avg_reliability=avg_reliability,
                         trending_topics=trending_topics[:5],
                         sentiment_trends=sentiment_trends,
                         category_stats=category_stats)

@admin_bp.route('/analytics')
@admin_required
def analytics_page():
    """Detailed analytics page."""
    # Get date range from request
    days = int(request.args.get('days', 30))
    
    # Get various analytics
    trending_topics = analytics.analyze_trending_topics(days=days)
    sentiment_trends = analytics.get_sentiment_trends(days=days)
    category_analytics = analytics.get_category_analytics()
    user_activity = analytics.get_user_activity_summary(days=days)
    
    return render_template('admin/analytics.html',
                         trending_topics=trending_topics,
                         sentiment_trends=sentiment_trends,
                         category_analytics=category_analytics,
                         user_activity=user_activity,
                         days=days)

@admin_bp.route('/users')
@admin_required
def users():
    """User management page."""
    # Get user statistics
    user_activity = analytics.get_user_activity_summary()
    
    # Mock user data (in production, this would come from a database)
    users = [
        {'id': 'user1', 'name': 'John Doe', 'email': 'john@example.com', 'last_active': '2024-01-10', 'actions': 45},
        {'id': 'user2', 'name': 'Jane Smith', 'email': 'jane@example.com', 'last_active': '2024-01-09', 'actions': 32},
        {'id': 'user3', 'name': 'Bob Johnson', 'email': 'bob@example.com', 'last_active': '2024-01-08', 'actions': 28}
    ]
    
    return render_template('admin/users.html', users=users, user_activity=user_activity)

@admin_bp.route('/content')
@admin_required
def content():
    """Content management page."""
    # Get recent articles and their analysis
    # This would typically fetch from database
    articles = []  # Mock data
    
    return render_template('admin/content.html', articles=articles)

@admin_bp.route('/settings')
@admin_required
def settings():
    """Settings page."""
    # Get current settings
    settings = {
        'news_api_key': os.getenv('NEWS_API_KEY', ''),
        'openai_api_key': os.getenv('OPENAI_API_KEY', ''),
        'max_articles_per_category': os.getenv('MAX_ARTICLES', '10'),
        'cache_duration': os.getenv('CACHE_DURATION', '300'),
        'enable_analytics': os.getenv('ENABLE_ANALYTICS', 'True')
    }
    
    return render_template('admin/settings.html', settings=settings)

@admin_bp.route('/api/analytics/data')
@admin_required
def analytics_data():
    """API endpoint for analytics data."""
    days = int(request.args.get('days', 30))
    data_type = request.args.get('type', 'overview')
    
    if data_type == 'overview':
        data = {
            'total_articles': get_total_articles(),
            'total_users': get_total_users(),
            'avg_reliability': get_avg_reliability(),
            'trending_topics': analytics.analyze_trending_topics(days=days)[:10]
        }
    elif data_type == 'sentiment':
        data = analytics.get_sentiment_trends(days=days)
    elif data_type == 'categories':
        data = analytics.get_category_analytics()
    elif data_type == 'activity':
        data = analytics.get_user_activity_summary(days=days)
    else:
        data = {'error': 'Invalid data type'}
    
    return jsonify(data)

@admin_bp.route('/api/settings/update', methods=['POST'])
@admin_required
def update_settings():
    """Update application settings."""
    try:
        settings = request.get_json()
        
        # Update environment variables (in production, this would update a config file)
        for key, value in settings.items():
            if key.upper() in ['NEWS_API_KEY', 'OPENAI_API_KEY', 'MAX_ARTICLES', 'CACHE_DURATION', 'ENABLE_ANALYTICS']:
                os.environ[key.upper()] = str(value)
        
        return jsonify({'success': True, 'message': 'Settings updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Helper functions
def get_total_articles():
    """Get total number of articles processed."""
    # This would typically query a database
    return 1250  # Mock data

def get_total_users():
    """Get total number of users."""
    # This would typically query a database
    return 342  # Mock data

def get_avg_reliability():
    """Get average reliability score."""
    # This would typically calculate from database
    return 78.5  # Mock data

# Error handlers
@admin_bp.errorhandler(404)
def not_found(error):
    return render_template('admin/404.html'), 404

@admin_bp.errorhandler(500)
def internal_error(error):
    return render_template('admin/500.html'), 500

# Developer Details
# Created by Molla Samser (RSK World)
# 2026
