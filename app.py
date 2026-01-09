"""
Main Flask Application for News Summary Bot
Developer: Molla Samser
Design & Testing: Rima Khatun
Company: RSK World
Year: 2026
Website: https://rskworld.in
"""

from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash, Response
from flask_cors import CORS
from datetime import datetime
from news_bot import NewsBot
from analytics import NewsAnalytics, AdvancedNLP
from cache import cache_manager, news_cache
from auth import auth_manager, user_preferences, login_required
from search import advanced_search, SearchFilters
from security import rate_limit, security_headers
from export import data_exporter
import os
from dotenv import load_dotenv
import hashlib

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')
CORS(app)

# Register security headers middleware
@app.after_request
def apply_security_headers(response):
    return security_headers.add_security_headers(response)

bot = NewsBot()
analytics = NewsAnalytics()
nlp = AdvancedNLP()

# Register admin blueprint
from admin import admin_bp
app.register_blueprint(admin_bp)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/demo')
def demo():
    return render_template('demo.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        result = auth_manager.authenticate_user(username, password)
        if result['success']:
            # Create session
            session_token = auth_manager.create_session(
                result['user_id'], 
                request.remote_addr,
                request.headers.get('User-Agent')
            )
            session['user_token'] = session_token
            session['user_id'] = result['user_id']
            session['username'] = result['username']
            
            flash('Login successful!', 'success')
            return redirect(url_for('demo'))
        else:
            flash(result['error'], 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('register.html')
        
        result = auth_manager.register_user(username, email, password)
        if result['success']:
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash(result['error'], 'error')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    if 'user_token' in session:
        auth_manager.invalidate_session(session['user_token'])
        session.clear()
        flash('Logged out successfully!', 'info')
    return redirect(url_for('home'))

@app.route('/api/news', methods=['GET'])
@rate_limit(limit=100, window=3600)
def get_news():
    category = request.args.get('category', 'general')
    query = request.args.get('q')
    country = request.args.get('country', 'us')
    
    # Check cache first
    cache_key_data = news_cache.get_news(category, query, country)
    if cache_key_data:
        return jsonify(cache_key_data)
    
    # Fetch fresh data
    news_data = bot.fetch_news(category=category, query=query)
    
    # Cache the results
    if 'articles' in news_data:
        news_cache.set_news(category, query, country, news_data)
        
        # Index articles for search
        for article in news_data['articles'][:10]:  # Limit to avoid overloading
            article_data = {
                'article_id': str(article.get('publishedAt', '')) + str(hash(article.get('title', ''))),
                'title': article.get('title', ''),
                'content': article.get('description', ''),
                'category': category,
                'source': article.get('source', {}).get('name', ''),
                'author': article.get('author', ''),
                'published_at': article.get('publishedAt', ''),
                'word_count': len(article.get('description', '').split())
            }
            advanced_search.index_article(article_data)
    
    return jsonify(news_data)

@app.route('/api/summarize', methods=['POST'])
@rate_limit(limit=50, window=3600)
def summarize():
    data = request.get_json()
    content = data.get('content')
    language = data.get('language', 'English')
    
    if not content:
        return jsonify({"error": "No content provided for summarization"}), 400
    
    # Generate content hash for caching
    content_hash = hashlib.md5(content.encode()).hexdigest()
    
    # Check cache first
    cached_summary = news_cache.get_summary(content_hash, language)
    if cached_summary:
        return jsonify({"summary": cached_summary, "cached": True})
    
    # Generate summary
    summary = bot.summarize_article(content, language=language)
    
    # Cache the summary
    news_cache.set_summary(content_hash, language, summary)
    
    # Track user activity if logged in
    if 'user_id' in session:
        analytics.track_user_interaction(session['user_id'], 'summarize', content_hash=content_hash)
    
    return jsonify({"summary": summary, "cached": False})

@app.route('/api/analyze', methods=['POST'])
@rate_limit(limit=50, window=3600)
def analyze():
    data = request.get_json()
    content = data.get('content')
    
    if not content:
        return jsonify({"error": "No content provided for analysis"}), 400
    
    # Generate content hash for caching
    content_hash = hashlib.md5(content.encode()).hexdigest()
    
    # Check cache first
    cached_sentiment = news_cache.get_sentiment(content_hash)
    if cached_sentiment:
        return jsonify({"sentiment": cached_sentiment, "cached": True})
    
    # Analyze sentiment
    sentiment = bot.analyze_sentiment(content)
    
    # Cache the result
    news_cache.set_sentiment(content_hash, sentiment)
    
    # Store analytics
    if 'user_id' in session:
        analytics.track_user_interaction(session['user_id'], 'analyze', content_hash=content_hash)
    
    return jsonify({"sentiment": sentiment, "cached": False})

@app.route('/api/reliability', methods=['POST'])
@rate_limit(limit=50, window=3600)
def reliability():
    data = request.get_json()
    content = data.get('content')
    
    if not content:
        return jsonify({"error": "No content provided for reliability analysis"}), 400
    
    score = bot.analyze_reliability(content)
    return jsonify({"score": score})

@app.route('/api/search', methods=['GET'])
@rate_limit(limit=200, window=3600)
def search_articles():
    query = request.args.get('q', '')
    filters = {}
    
    # Parse filters from query parameters
    if request.args.get('category'):
        filters['category'] = request.args.get('category')
    if request.args.get('sentiment'):
        filters['sentiment'] = request.args.get('sentiment')
    if request.args.get('language'):
        filters['language'] = request.args.get('language')
    if request.args.get('min_reliability'):
        filters['min_reliability'] = request.args.get('min_reliability')
    if request.args.get('date_from'):
        filters['date_from'] = request.args.get('date_from')
    if request.args.get('date_to'):
        filters['date_to'] = request.args.get('date_to')
    
    # Validate filters
    filters = SearchFilters.validate_filters(filters)
    
    # Search parameters
    sort_by = request.args.get('sort', 'relevance')
    limit = int(request.args.get('limit', 20))
    offset = int(request.args.get('offset', 0))
    
    # Perform search
    results = advanced_search.search(query, filters, sort_by, limit, offset)
    
    # Track search
    user_id = session.get('user_id') if 'user_id' in session else None
    advanced_search.track_search(user_id, query, filters, results['total_count'])
    
    return jsonify(results)

@app.route('/api/search/suggestions')
def search_suggestions():
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 10))
    
    suggestions = advanced_search.get_suggestions(query, limit)
    return jsonify({"suggestions": suggestions})

@app.route('/api/search/popular')
def popular_searches():
    limit = int(request.args.get('limit', 10))
    popular = advanced_search.get_popular_searches(limit)
    return jsonify({"popular": popular})

@app.route('/api/user/preferences', methods=['GET', 'POST'])
@login_required
def user_preferences_api():
    user_id = session['user_id']
    
    if request.method == 'POST':
        data = request.get_json()
        for pref_type, pref_value in data.items():
            user_preferences.set_preference(user_id, pref_type, pref_value)
        return jsonify({"success": True})
    
    preferences = user_preferences.get_all_preferences(user_id)
    return jsonify(preferences)

@app.route('/api/user/history')
@login_required
def reading_history():
    user_id = session['user_id']
    limit = int(request.args.get('limit', 50))
    history = user_preferences.get_reading_history(user_id, limit)
    return jsonify(history)

@app.route('/api/user/stats')
@login_required
def user_stats():
    user_id = session['user_id']
    days = int(request.args.get('days', 30))
    stats = user_preferences.get_reading_stats(user_id, days)
    return jsonify(stats)

@app.route('/api/trending')
def trending_topics():
    days = int(request.args.get('days', 7))
    
    # Check cache first
    cached_trending = news_cache.get_trending_topics(days)
    if cached_trending:
        return jsonify({"trending": cached_trending, "cached": True})
    
    # Get fresh trending data
    trending = analytics.analyze_trending_topics(days)
    
    # Cache the results
    news_cache.set_trending_topics(days, trending)
    
    return jsonify({"trending": trending, "cached": False})

@app.route('/api/analytics/overview')
def analytics_overview():
    """Public analytics endpoint."""
    days = int(request.args.get('days', 30))
    
    # Get various analytics
    sentiment_trends = analytics.get_sentiment_trends(days)
    category_analytics = analytics.get_category_analytics()
    search_analytics = advanced_search.get_search_analytics(days)
    
    return jsonify({
        "sentiment_trends": sentiment_trends,
        "category_analytics": category_analytics,
        "search_analytics": search_analytics
    })

@app.route('/api/cache/stats')
def cache_stats():
    """Cache statistics endpoint."""
    stats = cache_manager.get_stats()
    return jsonify(stats)

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Clear cache endpoint."""
    # This should be protected in production
    cache_manager.clear()
    return jsonify({"success": True, "message": "Cache cleared successfully"})

@app.route('/api/export/user-data', methods=['GET'])
@login_required
@rate_limit(limit=10, window=3600)
def export_user_data():
    """Export user data in various formats."""
    user_id = session['user_id']
    format_type = request.args.get('format', 'json').lower()
    
    try:
        data = data_exporter.export_user_data(user_id, format_type)
        
        # Set appropriate content type and filename
        content_types = {
            'json': 'application/json',
            'csv': 'text/csv',
            'xml': 'application/xml'
        }
        
        filename = f'user_data_{user_id}_{datetime.now().strftime("%Y%m%d")}.{format_type}'
        
        return Response(
            data,
            mimetype=content_types.get(format_type, 'application/octet-stream'),
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/export/analytics', methods=['GET'])
@rate_limit(limit=20, window=3600)
def export_analytics():
    """Export analytics data."""
    days = int(request.args.get('days', 30))
    format_type = request.args.get('format', 'json').lower()
    
    try:
        data = data_exporter.export_analytics_data(days, format_type)
        
        content_types = {
            'json': 'application/json',
            'csv': 'text/csv',
            'xml': 'application/xml'
        }
        
        filename = f'analytics_{days}days_{datetime.now().strftime("%Y%m%d")}.{format_type}'
        
        return Response(
            data,
            mimetype=content_types.get(format_type, 'application/octet-stream'),
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/export/backup', methods=['GET'])
@rate_limit(limit=5, window=3600)
def export_backup():
    """Create full system backup."""
    include_user_data = request.args.get('include_users', 'false').lower() == 'true'
    
    try:
        data = data_exporter.create_full_backup(include_user_data=include_user_data)
        filename = f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
        
        return Response(
            data,
            mimetype='application/zip',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "True") == "True"
    
    # Cleanup expired cache entries on startup
    cache_manager.cleanup_expired()
    
    app.run(host='0.0.0.0', port=port, debug=debug)

# Developed by Molla Samser | 2026 | RSK World
