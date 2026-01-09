# News Summary Bot

An advanced AI-powered chatbot that fetches real-time news articles and provides concise summaries using Natural Language Processing (NLP) and OpenAI. This project includes cutting-edge features like user authentication, advanced analytics, caching, search, and comprehensive security.

## Project Details
- **Developer:** Molla Samser
- **Design & Testing:** Rima Khatun
- **Company:** RSK World
- **Website:** [rskworld.in](https://rskworld.in)
- **Contact:** +91 93305 39277 | info@rskworld.com
- **Address:** Nutanhat, Mongolkote, Purba Burdwan, West Bengal, India, 713147
- **Year:** 2026

## 🚀 Advanced Features

### Core Functionality
- **Real-time News Fetching:** Fetches top headlines from multiple sources using NewsAPI
- **AI Article Summarization:** Generates high-quality summaries using OpenAI GPT-3.5 Turbo
- **Multi-language Support:** Summarize news in English, Hindi, Spanish, French, German
- **Voice Search:** Search news using voice commands
- **Category Filtering:** Browse news in Business, Tech, Health, Science, Sports, etc.
- **Sentiment Analysis:** Analyze the sentiment of news articles with advanced NLP
- **Reliability Scoring:** Check the reliability and objectivity of news sources
- **Mobile Responsive:** Modern glassmorphism design that works on all devices

### Advanced Features
- **User Authentication System:** Complete user registration, login, and session management
- **Personalization:** User preferences, reading history, and personalized recommendations
- **Advanced Search:** Full-text search with filters, sorting, and suggestions
- **Caching System:** Intelligent caching for improved performance and reduced API costs
- **Analytics Dashboard:** Comprehensive admin panel with real-time analytics
- **Data Export:** Export data in JSON, CSV, XML formats with backup capabilities
- **Rate Limiting:** Advanced API rate limiting and security features
- **Admin Panel:** Complete admin interface for monitoring and management

### Security Features
- **Input Validation:** Comprehensive input sanitization and validation
- **Rate Limiting:** Configurable rate limiting with exponential backoff
- **CSRF Protection:** Cross-site request forgery protection
- **Security Headers:** Complete security header implementation
- **API Key Authentication:** Secure API key validation
- **Session Management:** Secure session handling with expiration

## 🛠 Technologies Used

### Backend
- **Framework:** Python Flask
- **AI/NLP:** OpenAI API (GPT-3.5 Turbo)
- **APIs:** NewsAPI.org
- **Database:** SQLite (with full-text search)
- **Caching:** Custom caching system with SQLite backend
- **Authentication:** Custom auth system with secure password hashing
- **Security:** Rate limiting, CSRF protection, input validation

### Frontend
- **Languages:** HTML5, CSS3, JavaScript (Vanilla)
- **Styling:** Glassmorphism design with CSS animations
- **Icons:** Font Awesome 6.0
- **Charts:** Chart.js for analytics visualization
- **PDF Export:** jsPDF for document export

### Development Tools
- **Environment:** Python 3.8+
- **Package Management:** pip with requirements.txt
- **Configuration:** Environment variables with .env
- **Version Control:** Git ready

## 📁 Project Structure

```
news-summary-bot/
├── app.py                    # Main Flask application
├── news_bot.py              # Core news fetching and processing
├── analytics.py             # Advanced analytics and NLP processing
├── cache.py                 # Intelligent caching system
├── auth.py                  # User authentication and preferences
├── search.py                # Advanced search functionality
├── export.py                # Data export and reporting
├── security.py              # Security and rate limiting
├── admin.py                 # Admin panel routes
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables
├── README.md               # Project documentation
├── INSTALLATION.md         # Detailed installation guide
├── templates/              # HTML templates
│   ├── index.html          # Landing page
│   ├── demo.html           # Demo interface
│   ├── login.html          # User login
│   ├── register.html       # User registration
│   └── admin/              # Admin panel templates
│       ├── login.html      # Admin login
│       └── dashboard.html  # Admin dashboard
├── static/                 # Static assets
│   ├── css/
│   │   └── style.css       # Custom styles
│   └── js/
│       └── script.js       # JavaScript logic
└── databases/              # SQLite databases (auto-created)
    ├── news_analytics.db   # Analytics data
    ├── users.db            # User data
    ├── cache.db            # Cache storage
    ├── search_index.db     # Search index
    └── rate_limits.db      # Rate limiting data
```

## 🚀 Setup Instructions

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Valid API keys (NewsAPI and OpenAI)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd news-summary-bot
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On Mac/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file with your configuration:
   ```env
   # API Keys
   NEWS_API_KEY=your_newsapi_org_key
   OPENAI_API_KEY=your_openai_api_key
   
   # Server Configuration
   PORT=5000
   DEBUG=True
   SECRET_KEY=your-secret-key-here
   
   # Admin Credentials
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=admin123
   
   # Security
   VALID_API_KEYS=key1,key2,key3
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   - **Main Page:** http://localhost:5000
   - **Demo Interface:** http://localhost:5000/demo
   - **Admin Panel:** http://localhost:5000/admin

## 📡 API Endpoints

### News Endpoints
- `GET /api/news` - Fetch news articles (with caching)
- `POST /api/summarize` - Summarize article content
- `POST /api/analyze` - Analyze sentiment
- `POST /api/reliability` - Check reliability score

### Search Endpoints
- `GET /api/search` - Advanced search with filters
- `GET /api/search/suggestions` - Get search suggestions
- `GET /api/search/popular` - Get popular searches

### User Endpoints
- `POST /api/login` - User login
- `POST /api/register` - User registration
- `GET /api/logout` - User logout
- `GET/POST /api/user/preferences` - User preferences
- `GET /api/user/history` - Reading history
- `GET /api/user/stats` - User statistics

### Analytics Endpoints
- `GET /api/trending` - Trending topics
- `GET /api/analytics/overview` - Public analytics
- `GET /api/cache/stats` - Cache statistics

### Admin Endpoints
- `GET /admin/` - Admin dashboard
- `GET /admin/analytics` - Detailed analytics
- `GET /admin/users` - User management
- `GET /admin/settings` - System settings

## 🔧 Configuration

### Rate Limiting
Configure rate limits per endpoint:
```python
@app.route('/api/news')
@rate_limit(limit=100, window=3600)  # 100 requests per hour
def get_news():
    # Endpoint logic
```

### Caching
Configure cache TTL (time to live):
```python
# News cache: 5 minutes
news_cache.set_news(category, query, country, data, ttl=300)

# Summary cache: 1 hour
news_cache.set_summary(content_hash, language, summary, ttl=3600)
```

### Search Filters
Available search filters:
- `category`: News category
- `sentiment`: Positive/Negative/Neutral
- `language`: Article language
- `min_reliability`: Minimum reliability score
- `date_from/date_to`: Date range
- `sort`: relevance/date/reliability/popularity

## 📊 Analytics Features

### User Analytics
- Reading history tracking
- Category preferences
- Session duration
- Search patterns
- Summary requests

### System Analytics
- Sentiment trends over time
- Category distribution
- Popular search queries
- Cache hit rates
- API usage statistics

### Admin Dashboard
- Real-time metrics
- Interactive charts
- User management
- System monitoring
- Performance analytics

## 🔒 Security Features

### Input Validation
- Email format validation
- Password strength requirements
- XSS prevention
- SQL injection protection
- Search query validation

### Rate Limiting
- Per-IP and per-user limits
- Exponential backoff for violations
- Configurable windows and limits
- Automatic blocking for abuse

### Authentication Security
- Secure password hashing with salt
- Session management with expiration
- CSRF token protection
- API key validation

## 📤 Data Export

### Supported Formats
- **JSON:** Complete data structure
- **CSV:** Tabular data for spreadsheets
- **XML:** Structured data format
- **ZIP:** Multiple formats in one package

### Export Types
- User data export (GDPR compliant)
- Analytics data export
- News articles export
- Full system backup

## 🎯 Performance Optimization

### Caching Strategy
- Multi-level caching
- Intelligent cache invalidation
- Cache statistics and monitoring
- Automatic cleanup of expired entries

### Database Optimization
- Full-text search indexes
- Optimized queries
- Connection pooling
- Regular maintenance

### API Optimization
- Response compression
- Efficient data structures
- Minimal API calls
- Background processing

## 🐛 Troubleshooting

### Common Issues

1. **API Key Errors**
   - Verify keys in `.env` file
   - Check API key validity and permissions
   - Ensure sufficient API credits

2. **Database Errors**
   - Check file permissions for database files
   - Ensure SQLite is properly installed
   - Clear cache if corrupted

3. **Performance Issues**
   - Check cache hit rates
   - Monitor API usage limits
   - Review database indexes

4. **Authentication Issues**
   - Clear browser cookies
   - Check session configuration
   - Verify SECRET_KEY in .env

### Debug Mode
Enable debug mode for detailed error messages:
```env
DEBUG=True
```

## 📞 Support & Contact

For technical support and inquiries:
- **Email:** info@rskworld.com, support@rskworld.in
- **Phone:** +91 93305 39277
- **Website:** https://rskworld.in
- **Address:** Nutanhat, Mongolkote, Purba Burdwan, West Bengal, India, 713147

## 📄 License

&copy; 2026 RSK World. All rights reserved.
Developed by Molla Samser | Design & Testing by Rima Khatun

---

## 🌟 Acknowledgments

This project is part of the RSK World AI Chatbots collection. Visit https://rskworld.in for more projects and resources.

### Technologies Used
- [OpenAI](https://openai.com/) - AI-powered summarization
- [NewsAPI](https://newsapi.org/) - Real-time news data
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Chart.js](https://www.chartjs.org/) - Data visualization
- [Font Awesome](https://fontawesome.com/) - Icon library

### Contributing
Contributions are welcome! Please ensure all code follows the project standards and includes proper documentation.

---

*Last updated: January 2026*
