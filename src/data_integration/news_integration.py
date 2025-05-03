"""
Financial News Integration Module

This module handles:
1. Fetching financial news from various sources
2. Processing and analyzing news content 
3. Sentiment analysis using NLP models
4. Storing analyzed news in the knowledge base
"""

import os
import logging
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import requests
from dotenv import load_dotenv

# Optional sentiment analysis with transformers if available
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from src.knowledge.knowledge_base import KnowledgeBase
from src.knowledge.schema import FinancialNews, KnowledgeCategory

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# API keys
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")


class NewsIntegration:
    """
    Integration for financial news from various sources with sentiment analysis.
    
    This class handles:
    1. Fetching news from financial news APIs
    2. Sentiment analysis and entity extraction
    3. Storage in the knowledge base with metadata
    """
    
    def __init__(
        self,
        knowledge_base: Optional[KnowledgeBase] = None,
        alpha_vantage_api_key: Optional[str] = None,
        news_api_key: Optional[str] = None,
        finnhub_api_key: Optional[str] = None,
        sentiment_model: Optional[str] = "distilbert-base-uncased-finetuned-sst-2-english",
        max_news_per_source: int = 10
    ):
        """
        Initialize the news integration.
        
        Args:
            knowledge_base: Knowledge base instance for storing news
            alpha_vantage_api_key: Alpha Vantage API key
            news_api_key: News API key
            finnhub_api_key: Finnhub API key
            sentiment_model: Transformer model to use for sentiment analysis
            max_news_per_source: Maximum number of news items to fetch per source
        """
        self.knowledge_base = knowledge_base or KnowledgeBase()
        self.alpha_vantage_api_key = alpha_vantage_api_key or ALPHA_VANTAGE_API_KEY
        self.news_api_key = news_api_key or NEWS_API_KEY
        self.finnhub_api_key = finnhub_api_key or FINNHUB_API_KEY
        self.max_news_per_source = max_news_per_source
        
        # Initialize sentiment analysis if transformers available
        self.sentiment_analyzer = None
        if TRANSFORMERS_AVAILABLE and sentiment_model:
            try:
                self.sentiment_analyzer = pipeline("sentiment-analysis", model=sentiment_model)
                logger.info(f"Initialized sentiment analysis with model: {sentiment_model}")
            except Exception as e:
                logger.error(f"Error initializing sentiment analysis: {str(e)}")
        else:
            logger.warning("Transformers not available. Sentiment analysis will be limited.")
        
        # Check which API keys are available
        available_sources = []
        if self.alpha_vantage_api_key:
            available_sources.append("Alpha Vantage")
        if self.news_api_key:
            available_sources.append("News API")
        if self.finnhub_api_key:
            available_sources.append("Finnhub")
            
        if not available_sources:
            logger.warning("No news API keys provided. Functionality will be limited.")
        else:
            logger.info(f"News integration initialized with sources: {', '.join(available_sources)}")
            
        # Cache to avoid duplicating news
        self.news_cache = set()
    
    def update_financial_news(self):
        """
        Update financial news from all available sources.
        
        Fetches, analyzes, and stores news in the knowledge base.
        """
        logger.info("Updating financial news")
        all_news = []
        
        # Alpha Vantage news
        if self.alpha_vantage_api_key:
            try:
                alpha_news = self._fetch_alpha_vantage_news()
                all_news.extend(alpha_news)
                logger.info(f"Fetched {len(alpha_news)} news items from Alpha Vantage")
            except Exception as e:
                logger.error(f"Error fetching Alpha Vantage news: {str(e)}")
        
        # News API financial news
        if self.news_api_key:
            try:
                news_api_items = self._fetch_news_api()
                all_news.extend(news_api_items)
                logger.info(f"Fetched {len(news_api_items)} news items from News API")
            except Exception as e:
                logger.error(f"Error fetching News API news: {str(e)}")
        
        # Finnhub news
        if self.finnhub_api_key:
            try:
                finnhub_news = self._fetch_finnhub_news()
                all_news.extend(finnhub_news)
                logger.info(f"Fetched {len(finnhub_news)} news items from Finnhub")
            except Exception as e:
                logger.error(f"Error fetching Finnhub news: {str(e)}")
        
        # Process and store news
        added_count = 0
        for news in all_news:
            try:
                # Generate a simple hash for deduplication
                news_hash = hash(f"{news.headline}_{news.source}")
                
                # Skip if we've seen this news before
                if news_hash in self.news_cache:
                    continue
                    
                # Add to cache
                self.news_cache.add(news_hash)
                
                # Add to knowledge base
                self.knowledge_base.add_financial_news(news)
                added_count += 1
                
            except Exception as e:
                logger.error(f"Error processing news item: {str(e)}")
        
        logger.info(f"Added {added_count} new financial news items to knowledge base")
    
    def _fetch_alpha_vantage_news(self) -> List[FinancialNews]:
        """
        Fetch news from Alpha Vantage.
        
        Returns:
            List of FinancialNews objects
        """
        if not self.alpha_vantage_api_key:
            return []
            
        base_url = "https://www.alphavantage.co/query"
        params = {
            "function": "NEWS_SENTIMENT",
            "apikey": self.alpha_vantage_api_key,
            "limit": self.max_news_per_source,
            "sort": "LATEST"
        }
        
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            feed = data.get("feed", [])
            
            if not feed:
                logger.warning("No news items returned from Alpha Vantage")
                return []
            
            news_items = []
            current_time = datetime.now().isoformat()
            
            for item in feed:
                # Extract data from Alpha Vantage response
                title = item.get("title", "")
                summary = item.get("summary", "")
                url = item.get("url", "")
                source = item.get("source", "Alpha Vantage")
                time_published = item.get("time_published", "")
                
                # Get sentiment if available from Alpha Vantage
                sentiment_score = 0.0
                confidence = 0.5
                av_sentiment = item.get("overall_sentiment_score")
                if av_sentiment is not None:
                    # Convert Alpha Vantage score (-1 to 1) to our scale (-1 to 1)
                    sentiment_score = float(av_sentiment)
                    confidence = float(item.get("overall_sentiment_label_score", 0.5))
                else:
                    # Use our sentiment analyzer if available
                    sentiment_score, confidence = self._analyze_sentiment(title + " " + summary)
                
                # Extract entities (tickers) if available
                entities = []
                ticker_sentiment = item.get("ticker_sentiment", [])
                if ticker_sentiment:
                    for ticker in ticker_sentiment:
                        entities.append({
                            "name": ticker.get("ticker", ""),
                            "type": "ticker",
                            "relevance_score": float(ticker.get("relevance_score", 0.0))
                        })
                
                # Create FinancialNews object
                news = FinancialNews(
                    timestamp=current_time,
                    headline=title,
                    summary=summary,
                    source=source,
                    url=url,
                    sentiment_score=sentiment_score,
                    confidence=confidence,
                    entities=entities if entities else None,
                    categories=["financial"]  # Default category
                )
                
                news_items.append(news)
            
            return news_items
            
        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage news: {str(e)}")
            return []
    
    def _fetch_news_api(self) -> List[FinancialNews]:
        """
        Fetch news from News API.
        
        Returns:
            List of FinancialNews objects
        """
        if not self.news_api_key:
            return []
            
        base_url = "https://newsapi.org/v2/everything"
        
        # Financial news queries
        queries = [
            "finance",
            "stock market",
            "economy",
            "federal reserve",
            "inflation"
        ]
        
        news_items = []
        current_time = datetime.now().isoformat()
        
        for query in queries:
            params = {
                "q": query,
                "apiKey": self.news_api_key,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": min(self.max_news_per_source // len(queries), 10)
            }
            
            try:
                response = requests.get(base_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                articles = data.get("articles", [])
                
                for article in articles:
                    # Extract data
                    title = article.get("title", "")
                    description = article.get("description", "")
                    content = article.get("content", "")
                    url = article.get("url", "")
                    source = article.get("source", {}).get("name", "News API")
                    
                    # Get sentiment
                    sentiment_score, confidence = self._analyze_sentiment(title + " " + description)
                    
                    # Create categories based on query
                    categories = ["financial"]
                    if "stock market" in query:
                        categories.append("stocks")
                    elif "economy" in query:
                        categories.append("economy")
                    elif "federal reserve" in query:
                        categories.append("monetary_policy")
                    elif "inflation" in query:
                        categories.append("inflation")
                    
                    # Create FinancialNews object
                    news = FinancialNews(
                        timestamp=current_time,
                        headline=title,
                        summary=description,
                        full_text=content if content else None,
                        source=source,
                        url=url,
                        sentiment_score=sentiment_score,
                        confidence=confidence,
                        categories=categories
                    )
                    
                    news_items.append(news)
                
                # Avoid rate limits
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error fetching News API for query '{query}': {str(e)}")
        
        return news_items
    
    def _fetch_finnhub_news(self) -> List[FinancialNews]:
        """
        Fetch news from Finnhub.
        
        Returns:
            List of FinancialNews objects
        """
        if not self.finnhub_api_key:
            return []
            
        base_url = "https://finnhub.io/api/v1/news"
        
        # Get news for market category
        params = {
            "category": "general",
            "token": self.finnhub_api_key
        }
        
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                return []
            
            news_items = []
            current_time = datetime.now().isoformat()
            
            for item in data[:self.max_news_per_source]:
                # Extract data
                headline = item.get("headline", "")
                summary = item.get("summary", "")
                url = item.get("url", "")
                source = item.get("source", "Finnhub")
                category = item.get("category", "")
                
                # Get related symbols if available
                entities = []
                related = item.get("related", "")
                if related:
                    symbols = related.split(",")
                    for symbol in symbols:
                        entities.append({
                            "name": symbol.strip(),
                            "type": "ticker",
                            "relevance_score": 0.8  # Default relevance
                        })
                
                # Get sentiment
                sentiment_score, confidence = self._analyze_sentiment(headline + " " + summary)
                
                # Map Finnhub categories to our categories
                categories = ["financial"]
                if category:
                    categories.append(category.lower())
                
                # Create FinancialNews object
                news = FinancialNews(
                    timestamp=current_time,
                    headline=headline,
                    summary=summary,
                    source=source,
                    url=url,
                    sentiment_score=sentiment_score,
                    confidence=confidence,
                    entities=entities if entities else None,
                    categories=categories
                )
                
                news_items.append(news)
            
            return news_items
            
        except Exception as e:
            logger.error(f"Error fetching Finnhub news: {str(e)}")
            return []
    
    def _analyze_sentiment(self, text: str) -> tuple:
        """
        Analyze sentiment of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (sentiment_score, confidence)
        """
        # Default neutral sentiment with low confidence
        sentiment_score = 0.0
        confidence = 0.5
        
        # Skip empty text
        if not text:
            return sentiment_score, confidence
        
        # Use transformer model if available
        if self.sentiment_analyzer:
            try:
                # Truncate text if too long for the model
                max_length = 512
                if len(text) > max_length:
                    text = text[:max_length]
                
                result = self.sentiment_analyzer(text)[0]
                label = result["label"]
                score = result["score"]
                
                # Convert to our scale (-1 to 1)
                if label == "POSITIVE":
                    sentiment_score = score
                elif label == "NEGATIVE":
                    sentiment_score = -score
                
                confidence = score
                
            except Exception as e:
                logger.error(f"Error in sentiment analysis: {str(e)}")
        else:
            # Simple rule-based sentiment analysis as fallback
            positive_words = ["gain", "rise", "increase", "growth", "positive", "bull", "rally", "up"]
            negative_words = ["loss", "drop", "decrease", "decline", "negative", "bear", "crash", "down"]
            
            text_lower = text.lower()
            
            # Count positive and negative words
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            total = positive_count + negative_count
            if total > 0:
                sentiment_score = (positive_count - negative_count) / total
                confidence = min(0.7, total / 10)  # Higher confidence with more signal words, max 0.7
        
        return sentiment_score, confidence


def main():
    """Test the news integration."""
    load_dotenv()
    
    # Initialize knowledge base and news integration
    kb = KnowledgeBase(namespace="news_test")
    news_client = NewsIntegration(knowledge_base=kb)
    
    # Update news
    news_client.update_financial_news()
    
    # Query for market news
    query = "latest market news and sentiment"
    results = kb.query(
        query_text=query,
        filter_categories=[KnowledgeCategory.MARKET_DATA.value],
        top_k=5
    )
    
    print("\nFinancial News Query Results:")
    for i, result in enumerate(results):
        print(f"{i+1}. {result.content}")


if __name__ == "__main__":
    main() 