"""
API Rate Limiting and Security Features
Developer: Molla Samser
Design & Testing: Rima Khatun
Company: RSK World
Year: 2026
Website: https://rskworld.in
"""

import time
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g
from typing import Dict, Optional, Tuple, List
import re
import os

class RateLimiter:
    """API rate limiting implementation."""
    
    def __init__(self, db_path='rate_limits.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize rate limiting database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rate_limits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identifier TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                request_count INTEGER DEFAULT 1,
                window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_request TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_blocked BOOLEAN DEFAULT 0,
                block_until TIMESTAMP,
                UNIQUE(identifier, endpoint)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                identifier TEXT,
                ip_address TEXT,
                user_agent TEXT,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def is_allowed(self, identifier: str, endpoint: str, limit: int, window: int) -> Tuple[bool, Dict]:
        """Check if request is allowed based on rate limits."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now()
        window_start = now - timedelta(seconds=window)
        
        # Check if identifier is blocked
        cursor.execute('''
            SELECT is_blocked, block_until FROM rate_limits 
            WHERE identifier = ? AND is_blocked = 1 AND block_until > ?
        ''', (identifier, now))
        
        block_result = cursor.fetchone()
        if block_result:
            conn.close()
            return False, {
                'error': 'Request blocked',
                'reason': 'Rate limit exceeded',
                'retry_after': int((block_result[1] - now).total_seconds())
            }
        
        # Get current rate limit record
        cursor.execute('''
            SELECT request_count, window_start FROM rate_limits 
            WHERE identifier = ? AND endpoint = ?
        ''', (identifier, endpoint))
        
        result = cursor.fetchone()
        
        if result:
            request_count, record_window_start = result
            
            # Check if window has expired
            if isinstance(record_window_start, str):
                record_dt = datetime.fromisoformat(record_window_start)
            else:
                record_dt = record_window_start
            
            if record_dt < window_start:
                # Reset window
                cursor.execute('''
                    UPDATE rate_limits 
                    SET request_count = 1, window_start = ?, last_request = ?
                    WHERE identifier = ? AND endpoint = ?
                ''', (now, now, identifier, endpoint))
                conn.commit()
                conn.close()
                return True, {'remaining': limit - 1}
            
            # Check if limit exceeded
            if request_count >= limit:
                # Block for exponential backoff
                block_duration = min(300, 2 ** (request_count - limit + 1))  # Max 5 minutes
                block_until = now + timedelta(seconds=block_duration)
                
                cursor.execute('''
                    UPDATE rate_limits 
                    SET is_blocked = 1, block_until = ?
                    WHERE identifier = ? AND endpoint = ?
                ''', (block_until, identifier, endpoint))
                
                conn.commit()
                conn.close()
                
                # Log security event
                self.log_security_event('rate_limit_exceeded', identifier, {
                    'endpoint': endpoint,
                    'request_count': request_count,
                    'limit': limit,
                    'block_duration': block_duration
                })
                
                return False, {
                    'error': 'Rate limit exceeded',
                    'retry_after': block_duration
                }
            
            # Increment request count
            cursor.execute('''
                UPDATE rate_limits 
                SET request_count = request_count + 1, last_request = ?
                WHERE identifier = ? AND endpoint = ?
            ''', (now, identifier, endpoint))
            
            conn.commit()
            conn.close()
            
            return True, {'remaining': limit - request_count - 1}
        
        else:
            # Create new record
            cursor.execute('''
                INSERT INTO rate_limits (identifier, endpoint, window_start, last_request)
                VALUES (?, ?, ?, ?)
            ''', (identifier, endpoint, now, now))
            
            conn.commit()
            conn.close()
            
            return True, {'remaining': limit - 1}
    
    def log_security_event(self, event_type: str, identifier: Optional[str], details: Dict):
        """Log security-related events."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO security_events (event_type, identifier, ip_address, user_agent, details)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            event_type,
            identifier,
            getattr(request, 'remote_addr', None),
            getattr(request, 'headers', {}).get('User-Agent'),
            str(details)
        ))
        
        conn.commit()
        conn.close()
    
    def get_stats(self) -> Dict:
        """Get rate limiting statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total requests
        cursor.execute('SELECT SUM(request_count) FROM rate_limits')
        total_requests = cursor.fetchone()[0] or 0
        
        # Active blocks
        cursor.execute('SELECT COUNT(*) FROM rate_limits WHERE is_blocked = 1 AND block_until > ?', (datetime.now(),))
        active_blocks = cursor.fetchone()[0] or 0
        
        # Security events in last 24 hours
        cutoff = datetime.now() - timedelta(hours=24)
        cursor.execute('SELECT COUNT(*) FROM security_events WHERE timestamp >= ?', (cutoff,))
        recent_events = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_requests': total_requests,
            'active_blocks': active_blocks,
            'recent_events': recent_events
        }

class SecurityValidator:
    """Input validation and security checks."""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, List[str]]:
        """Validate password strength."""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def sanitize_input(input_string: str) -> str:
        """Sanitize user input to prevent XSS."""
        if not input_string:
            return ""
        
        # Basic XSS prevention
        dangerous_chars = {
            '<': '&lt;',
            '>': '&gt;',
            '&': '&amp;',
            '"': '&quot;',
            "'": '&#x27;',
            '/': '&#x2F;'
        }
        
        sanitized = input_string
        for char, replacement in dangerous_chars.items():
            sanitized = sanitized.replace(char, replacement)
        
        return sanitized
    
    @staticmethod
    def validate_search_query(query: str) -> Tuple[bool, str]:
        """Validate search query."""
        if not query or not query.strip():
            return False, "Search query cannot be empty"
        
        if len(query) > 500:
            return False, "Search query too long (max 500 characters)"
        
        # Check for potentially dangerous patterns
        dangerous_patterns = [
            r'<script.*?>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'eval\s*\(',
            r'document\.',
            r'window\.',
            r'alert\s*\('
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return False, "Invalid characters in search query"
        
        return True, ""
    
    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """Validate API key format."""
        if not api_key:
            return False
        
        # Check if it looks like a valid API key (alphanumeric, reasonable length)
        return len(api_key) >= 20 and api_key.replace('-', '').replace('_', '').isalnum()

class CSRFProtection:
    """CSRF protection utilities."""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize CSRF protection with Flask app."""
        app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
    
    @staticmethod
    def generate_token() -> str:
        """Generate CSRF token."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_token(token: str, session_token: str) -> bool:
        """Validate CSRF token."""
        return secrets.compare_digest(token, session_token)

class SecurityHeaders:
    """Security headers middleware."""
    
    @staticmethod
    def add_security_headers(response):
        """Add security headers to response."""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self'"
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response

# Rate limiting decorators
def rate_limit(limit: int = 100, window: int = 3600, per_ip: bool = True):
    """Rate limiting decorator."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get identifier (IP address or user ID)
            if per_ip:
                identifier = request.remote_addr or 'unknown'
            else:
                identifier = getattr(g, 'user_id', request.remote_addr or 'anonymous')
            
            endpoint = f"{request.method}:{request.endpoint}"
            
            # Check rate limit
            allowed, info = rate_limiter.is_allowed(identifier, endpoint, limit, window)
            
            if not allowed:
                response = jsonify({'error': info.get('error', 'Rate limit exceeded')})
                if 'retry_after' in info:
                    response.headers['Retry-After'] = str(info['retry_after'])
                response.status_code = 429
                return response
            
            # Add rate limit headers
            response = f(*args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(limit)
                response.headers['X-RateLimit-Remaining'] = str(info.get('remaining', 0))
                response.headers['X-RateLimit-Reset'] = str(int(time.time() + window))
            
            return response
        
        return decorated_function
    return decorator

def require_api_key(f):
    """Decorator to require valid API key."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        if not SecurityValidator.validate_api_key(api_key):
            return jsonify({'error': 'Invalid API key format'}), 401
        
        # In production, validate against database or config
        valid_keys = os.getenv('VALID_API_KEYS', '').split(',')
        if api_key not in valid_keys:
            rate_limiter.log_security_event('invalid_api_key', None, {'api_key': api_key[:10] + '...'})
            return jsonify({'error': 'Invalid API key'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

# Initialize global instances
rate_limiter = RateLimiter()
csrf_protection = CSRFProtection()
security_headers = SecurityHeaders()

# Developer Details
# Created by Molla Samser (RSK World)
# 2026
