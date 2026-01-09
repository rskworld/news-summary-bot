"""
News Bot Logic - Fetching and Summarizing News Articles
Developer: Molla Samser
Design & Testing: Rima Khatun
Company: RSK World
Year: 2026
Website: https://rskworld.in
"""

import os
import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class NewsBot:
    def __init__(self):
        self.news_api_key = os.getenv("NEWS_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None

    def fetch_news(self, category="general", query=None):
        """Fetches news from NewsAPI."""
        if not self.news_api_key:
            return {"error": "News API Key not configured. Please add it to your .env file."}
        
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            "apiKey": self.news_api_key,
            "country": "us",
            "category": category,
            "pageSize": 10
        }
        if query:
            url = "https://newsapi.org/v2/everything"
            params = {"apiKey": self.news_api_key, "q": query, "pageSize": 10}

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def summarize_article(self, content, language="English"):
        """Summarizes an article using OpenAI API with language support."""
        if not self.client:
            return "OpenAI API Key not configured. Cannot generate summary."

        try:
            prompt = f"Summarize the following news article briefly and concisely in {language}. Provide only the summary."
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful news assistant."},
                    {"role": "user", "content": f"{prompt}\n\nArticle: {content}"}
                ],
                max_tokens=250
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error during summarization: {str(e)}"

    def analyze_sentiment(self, content):
        """Analyzes the sentiment of an article snippet."""
        if not self.client:
            # Fallback simple logic if no OpenAI client
            content_lower = content.lower()
            positive_words = ['great', 'good', 'success', 'breakthrough', 'positive', 'win', 'improve']
            negative_words = ['fail', 'crisis', 'bad', 'death', 'crash', 'negative', 'loss', 'decline']
            
            p_count = sum(1 for w in positive_words if w in content_lower)
            n_count = sum(1 for w in negative_words if w in content_lower)
            
            if p_count > n_count: return "Positive"
            if n_count > p_count: return "Negative"
            return "Neutral"

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Analyze the sentiment of the following news headline/snippet. Respond with exactly one word: Positive, Negative, or Neutral."},
                    {"role": "user", "content": content}
                ],
                max_tokens=10
            )
            sentiment = response.choices[0].message.content.strip().replace('.', '')
            return sentiment if sentiment in ["Positive", "Negative", "Neutral"] else "Neutral"
        except:
            return "Neutral"

    def analyze_reliability(self, content):
        """Analyzes the reliability and objectivity of a news snippet."""
        if not self.client:
            return 75  # Default dummy score

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Analyze the reliability and objectivity of the following news headline/snippet. Respond with exactly one number between 0 and 100, where 100 is highly reliable and objective."},
                    {"role": "user", "content": content}
                ],
                max_tokens=5
            )
            score_str = response.choices[0].message.content.strip()
            # Extract number
            import re
            match = re.search(r'\d+', score_str)
            return int(match.group()) if match else 75
        except:
            return 75

# Developer Details in comment
# Created by Molla Samser (RSK World)
# 2026
