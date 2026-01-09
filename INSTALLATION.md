# Installation Guide - News Summary Bot

## Developer Information
- **Developer:** Molla Samser
- **Design & Testing:** Rima Khatun  
- **Company:** RSK World
- **Website:** [https://rskworld.in](https://rskworld.in)
- **Contact:** +91 93305 39277 | info@rskworld.com
- **Address:** Nutanhat, Mongolkote, Purba Burdwan, West Bengal, India, 713147
- **Year:** 2026

## Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Valid API keys for NewsAPI and OpenAI

## Step-by-Step Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd news-summary-bot
```

### 2. Create Virtual Environment
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Mac/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file with your API keys:
```env
NEWS_API_KEY=your_newsapi_org_key
OPENAI_API_KEY=your_openai_api_key
PORT=5000
DEBUG=True
```

### 5. Run the Application
```bash
python app.py
```

### 6. Access the Application
- **Main Page:** http://localhost:5000
- **Demo Interface:** http://localhost:5000/demo

## API Endpoints

### Fetch News
- **GET** `/api/news?category={category}&q={query}`
- Categories: general, business, technology, entertainment, health, science, sports

### Summarize Article
- **POST** `/api/summarize`
- Body: `{"content": "article text", "language": "English"}`

### Analyze Sentiment
- **POST** `/api/analyze`
- Body: `{"content": "article text"}`

### Check Reliability
- **POST** `/api/reliability`
- Body: `{"content": "article text"}`

## Features
- ✅ Real-time news fetching from multiple sources
- ✅ AI-powered article summarization
- ✅ Multi-language summary support
- ✅ Category-based news filtering
- ✅ Sentiment analysis
- ✅ Reliability scoring
- ✅ Voice search capability
- ✅ PDF export functionality
- ✅ Bookmark/favorites system
- ✅ Mobile responsive design

## Technologies Used
- **Backend:** Python Flask
- **AI/NLP:** OpenAI GPT-3.5 Turbo
- **News API:** NewsAPI.org
- **Frontend:** HTML5, CSS3, JavaScript
- **Styling:** Glassmorphism design
- **Icons:** Font Awesome 6.0

## Troubleshooting

### Common Issues
1. **API Key Errors:** Ensure valid API keys in `.env` file
2. **Port Conflicts:** Change PORT in `.env` if needed
3. **CORS Issues:** Ensure flask-cors is installed
4. **Import Errors:** Run `pip install -r requirements.txt` again

### Support
For technical support:
- Email: support@rskworld.in
- Phone: +91 93305 39277
- Website: https://rskworld.in

---
&copy; 2026 RSK World. All rights reserved.
Developed by Molla Samser | Design & Testing by Rima Khatun
