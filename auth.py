"""
User Authentication and Personalization System
Developer: Molla Samser
Design & Testing: Rima Khatun
Company: RSK World
Year: 2026
Website: https://rskworld.in
"""

import sqlite3
import hashlib
import secrets
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import session, request, redirect, url_for, flash, jsonify
import os

class AuthManager:
    def __init__(self, db_path='users.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize user database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                preferences TEXT DEFAULT '{}'
            )
        ''')
        
        # User sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # User preferences and activity
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category TEXT,
                preference_type TEXT,
                preference_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # User reading history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reading_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                article_id TEXT,
                article_title TEXT,
                category TEXT,
                read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reading_time INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _generate_salt(self):
        """Generate a random salt for password hashing."""
        return secrets.token_hex(16)
    
    def _hash_password(self, password, salt):
        """Hash password with salt."""
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
    
    def register_user(self, username, email, password):
        """Register a new user."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if user already exists
            cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
            if cursor.fetchone():
                return {'success': False, 'error': 'User already exists'}
            
            # Create new user
            salt = self._generate_salt()
            password_hash = self._hash_password(password, salt)
            
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, salt)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, salt))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {'success': True, 'user_id': user_id}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def authenticate_user(self, username, password):
        """Authenticate user credentials."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, password_hash, salt, is_active
                FROM users WHERE username = ? OR email = ?
            ''', (username, username))
            
            user = cursor.fetchone()
            conn.close()
            
            if not user:
                return {'success': False, 'error': 'Invalid credentials'}
            
            user_id, username, email, stored_hash, salt, is_active = user
            
            if not is_active:
                return {'success': False, 'error': 'Account is disabled'}
            
            # Verify password
            password_hash = self._hash_password(password, salt)
            if password_hash != stored_hash:
                return {'success': False, 'error': 'Invalid credentials'}
            
            # Update last login
            self._update_last_login(user_id)
            
            return {
                'success': True,
                'user_id': user_id,
                'username': username,
                'email': email
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _update_last_login(self, user_id):
        """Update user's last login timestamp."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET last_login = ? WHERE id = ?
        ''', (datetime.now(), user_id))
        
        conn.commit()
        conn.close()
    
    def create_session(self, user_id, ip_address=None, user_agent=None):
        """Create a new user session."""
        try:
            session_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(days=7)  # 7 days expiry
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO user_sessions (user_id, session_token, expires_at, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, session_token, expires_at, ip_address, user_agent))
            
            conn.commit()
            conn.close()
            
            return session_token
        
        except Exception as e:
            return None
    
    def validate_session(self, session_token):
        """Validate session token and return user info."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT us.user_id, u.username, u.email, us.expires_at
                FROM user_sessions us
                JOIN users u ON us.user_id = u.id
                WHERE us.session_token = ? AND us.is_active = 1 AND u.is_active = 1
            ''', (session_token,))
            
            result = cursor.fetchone()
            
            if not result:
                return None
            
            user_id, username, email, expires_at = result
            
            # Check if session is expired
            if expires_at:
                if isinstance(expires_at, str):
                    expires_dt = datetime.fromisoformat(expires_at)
                else:
                    expires_dt = expires_at
                
                if datetime.now() > expires_dt:
                    self.invalidate_session(session_token)
                    return None
            
            return {
                'user_id': user_id,
                'username': username,
                'email': email
            }
        
        except Exception as e:
            return None
        finally:
            if conn:
                conn.close()
    
    def invalidate_session(self, session_token):
        """Invalidate a session."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_sessions SET is_active = 0 WHERE session_token = ?
        ''', (session_token,))
        
        conn.commit()
        conn.close()
    
    def invalidate_all_sessions(self, user_id):
        """Invalidate all sessions for a user."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_sessions SET is_active = 0 WHERE user_id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()

class UserPreferences:
    """Manage user preferences and personalization."""
    
    def __init__(self, db_path='users.db'):
        self.db_path = db_path
    
    def set_preference(self, user_id, preference_type, preference_value, category=None):
        """Set a user preference."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_preferences 
            (user_id, category, preference_type, preference_value)
            VALUES (?, ?, ?, ?)
        ''', (user_id, category, preference_type, json.dumps(preference_value)))
        
        conn.commit()
        conn.close()
    
    def get_preference(self, user_id, preference_type, category=None):
        """Get a user preference."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT preference_value FROM user_preferences 
            WHERE user_id = ? AND preference_type = ? AND (category = ? OR category IS NULL)
        ''', (user_id, preference_type, category))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return json.loads(result[0])
        return None
    
    def get_all_preferences(self, user_id):
        """Get all user preferences."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT category, preference_type, preference_value 
            FROM user_preferences WHERE user_id = ?
        ''', (user_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        preferences = {}
        for category, pref_type, pref_value in results:
            if category not in preferences:
                preferences[category] = {}
            preferences[category][pref_type] = json.loads(pref_value)
        
        return preferences
    
    def track_reading_history(self, user_id, article_id, article_title, category, reading_time=0):
        """Track user reading history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO reading_history 
            (user_id, article_id, article_title, category, reading_time)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, article_id, article_title, category, reading_time))
        
        conn.commit()
        conn.close()
    
    def get_reading_history(self, user_id, limit=50):
        """Get user reading history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT article_id, article_title, category, read_at, reading_time
            FROM reading_history 
            WHERE user_id = ? 
            ORDER BY read_at DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'article_id': row[0],
                'article_title': row[1],
                'category': row[2],
                'read_at': row[3],
                'reading_time': row[4]
            }
            for row in results
        ]
    
    def get_reading_stats(self, user_id, days=30):
        """Get user reading statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Total articles read
        cursor.execute('''
            SELECT COUNT(*) FROM reading_history 
            WHERE user_id = ? AND read_at >= ?
        ''', (user_id, cutoff_date))
        total_articles = cursor.fetchone()[0]
        
        # Articles by category
        cursor.execute('''
            SELECT category, COUNT(*) FROM reading_history 
            WHERE user_id = ? AND read_at >= ?
            GROUP BY category
        ''', (user_id, cutoff_date))
        category_stats = dict(cursor.fetchall())
        
        # Total reading time
        cursor.execute('''
            SELECT SUM(reading_time) FROM reading_history 
            WHERE user_id = ? AND read_at >= ?
        ''', (user_id, cutoff_date))
        total_time = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_articles': total_articles,
            'category_stats': category_stats,
            'total_reading_time': total_time,
            'avg_reading_time': total_time / total_articles if total_articles > 0 else 0
        }

# Flask decorators
def login_required(f):
    """Decorator to require user login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_token' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        
        # Validate session
        user_info = auth_manager.validate_session(session['user_token'])
        if not user_info:
            session.pop('user_token', None)
            flash('Session expired. Please log in again.', 'warning')
            return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin privileges."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_token' not in session:
            flash('Admin access required.', 'error')
            return redirect(url_for('admin.login'))
        
        user_info = auth_manager.validate_session(session['user_token'])
        if not user_info or user_info.get('username') != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('admin.login'))
        
        return f(*args, **kwargs)
    return decorated_function

# Initialize global auth manager
auth_manager = AuthManager()
user_preferences = UserPreferences()

# Developer Details
# Created by Molla Samser (RSK World)
# 2026
