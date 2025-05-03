"""
Real-Time Portfolio AI Inputs Demo

This script demonstrates the comprehensive real-time data inputs for the portfolio AI stack:
1. Market data from Alpaca (prices, volatility, volume)
2. Economic indicators from FRED (interest rates, inflation, employment)
3. Financial news with sentiment analysis from various sources
"""

import os
import sys
import time
import logging
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.knowledge.knowledge_base import KnowledgeBase
from src.data_integration.alpaca_market_data import AlpacaMarketData
from src.data_integration.alpaca_real_time import AlpacaRealTimeIntegration
from src.data_integration.economic_indicators import EconomicDataIntegration
from src.data_integration.news_integration import NewsIntegration

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def run_demo():
    """Run a comprehensive demonstration of real-time inputs."""
    logger.info("Starting comprehensive real-time inputs demo")
    
    # Initialize the knowledge base
    knowledge_base = KnowledgeBase(
        embedding_client_type="voyage",
        namespace="portfolio_inputs_demo"
    )
    
    # Initialize Alpaca market data client
    alpaca_client = AlpacaMarketData(
        is_free_tier=True  # Using free tier (15-min delay)
    )
    
    # Custom watchlist for the demo
    demo_watchlist = [
        "SPY",   # S&P 500 ETF
        "QQQ",   # Nasdaq 100 ETF
        "AAPL",  # Apple
        "MSFT",  # Microsoft
        "AMZN",  # Amazon
        "TSLA",  # Tesla
        "NVDA",  # NVIDIA
        "GLD",   # Gold ETF
        "TLT",   # 20+ Year Treasury ETF
        "VTI",   # Total Market ETF
        "GOOGL", # Alphabet/Google
        "META",  # Meta/Facebook
        "XLE",   # Energy Sector ETF
        "XLF",   # Financial Sector ETF
        "XLK",   # Technology Sector ETF
    ]
    
    # Initialize all real-time data sources
    market_integration = AlpacaRealTimeIntegration(
        knowledge_base=knowledge_base,
        alpaca_client=alpaca_client,
        watchlist=demo_watchlist,
        update_interval=15,  # 15 minutes minimum for free tier
        market_hour_only=False  # Allow updates outside market hours for demo
    )
    
    economic_integration = EconomicDataIntegration(
        knowledge_base=knowledge_base
    )
    
    news_integration = NewsIntegration(
        knowledge_base=knowledge_base,
        max_news_per_source=5  # Limit for demo purposes
    )
    
    try:
        # Display available data sources
        logger.info("\n=== Real-Time Data Sources ===")
        logger.info(f"Market Data: Alpaca API (free tier, 15-min delay)")
        logger.info(f"Watchlist: {', '.join(demo_watchlist[:5])}... ({len(demo_watchlist)} stocks total)")
        
        if os.getenv("FRED_API_KEY"):
            logger.info(f"Economic Indicators: FRED (Federal Reserve Economic Data)")
        else:
            logger.info(f"Economic Indicators: DEMO MODE (FRED API key not provided)")
            
        news_sources = []
        if os.getenv("ALPHA_VANTAGE_API_KEY"):
            news_sources.append("Alpha Vantage")
        if os.getenv("NEWS_API_KEY"):
            news_sources.append("News API")
        if os.getenv("FINNHUB_API_KEY"):
            news_sources.append("Finnhub")
            
        if news_sources:
            logger.info(f"Financial News: {', '.join(news_sources)}")
        else:
            logger.info(f"Financial News: DEMO MODE (no news API keys provided)")
        
        # Start market data integration
        logger.info("\n=== Starting Market Data Integration ===")
        market_integration.start()
        
        # Initial data collection wait
        logger.info("Waiting for initial market data collection...")
        time.sleep(10)
        
        # Update economic indicators
        logger.info("\n=== Updating Economic Indicators ===")
        try:
            economic_integration.update_economic_indicators()
        except Exception as e:
            logger.error(f"Error updating economic indicators: {str(e)}")
            if not os.getenv("FRED_API_KEY"):
                logger.error("FRED API key not provided. Set FRED_API_KEY in .env file.")
        
        # Update financial news
        logger.info("\n=== Updating Financial News ===")
        try:
            news_integration.update_financial_news()
        except Exception as e:
            logger.error(f"Error updating financial news: {str(e)}")
            if not any([os.getenv("ALPHA_VANTAGE_API_KEY"), os.getenv("NEWS_API_KEY"), os.getenv("FINNHUB_API_KEY")]):
                logger.error("No news API keys provided. Set at least one in .env file.")
        
        # Query different types of data
        logger.info("\n=== Sample Knowledge Base Queries ===")
        
        # Market data queries
        logger.info("\n--- Market Data Queries ---")
        market_queries = [
            "stocks with high volatility",
            "best performing stocks today",
            "technology sector performance",
            "unusual trading volume"
        ]
        
        for query in market_queries:
            results = knowledge_base.query(
                query_text=query,
                filter_categories=[knowledge_base.schema.KnowledgeCategory.MARKET_DATA.value],
                top_k=2
            )
            
            logger.info(f"\nQuery: {query}")
            for i, result in enumerate(results):
                logger.info(f"Result {i+1}: {result.content[:250]}...")
        
        # Economic indicator queries
        logger.info("\n--- Economic Indicator Queries ---")
        economic_queries = [
            "current interest rates",
            "inflation trends",
            "yield curve shape",
            "employment situation"
        ]
        
        for query in economic_queries:
            results = knowledge_base.query(
                query_text=query,
                filter_categories=[knowledge_base.schema.KnowledgeCategory.ECONOMIC_INDICATORS.value],
                top_k=2
            )
            
            logger.info(f"\nQuery: {query}")
            for i, result in enumerate(results):
                logger.info(f"Result {i+1}: {result.content[:250]}...")
        
        # News queries
        logger.info("\n--- Financial News Queries ---")
        news_queries = [
            "latest market news",
            "news about technology companies",
            "interest rate news",
            "market sentiment today"
        ]
        
        for query in news_queries:
            results = knowledge_base.query(
                query_text=query,
                filter_categories=[knowledge_base.schema.KnowledgeCategory.MARKET_DATA.value],
                top_k=2
            )
            
            logger.info(f"\nQuery: {query}")
            for i, result in enumerate(results):
                logger.info(f"Result {i+1}: {result.content[:250]}...")
        
        # Combined queries
        logger.info("\n--- Portfolio Decision Queries ---")
        combined_queries = [
            "how should I adjust my portfolio based on current market conditions",
            "is it a good time to invest in technology stocks",
            "what sectors are showing strength in the current economic environment",
            "should I be concerned about the yield curve for my bond portfolio"
        ]
        
        for query in combined_queries:
            # Search across all categories
            results = knowledge_base.query(
                query_text=query,
                top_k=3
            )
            
            logger.info(f"\nQuery: {query}")
            for i, result in enumerate(results):
                logger.info(f"Result {i+1}: {result.content[:250]}...")
        
        # Summary statistics
        logger.info("\n=== Knowledge Base Statistics ===")
        stats = knowledge_base.get_statistics()
        logger.info(f"Total Items Added: {stats['items_added']}")
        logger.info("Items by Category:")
        for category, count in stats["items_by_category"].items():
            logger.info(f"  - {category}: {count}")
        logger.info(f"Last Updated: {stats['last_updated']}")
        
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    finally:
        # Stop the market data integration
        logger.info("\n=== Stopping Market Data Integration ===")
        market_integration.stop()
        logger.info("Demo completed")


def print_api_key_help():
    """Print help message for API keys."""
    print("\nFor full functionality, add the following API keys to your .env file:")
    print("  ALPACA_API_KEY and ALPACA_API_SECRET - For market data")
    print("  FRED_API_KEY - For economic indicators")
    print("  ALPHA_VANTAGE_API_KEY - For financial news and sentiment")
    print("  NEWS_API_KEY - For general financial news")
    print("  FINNHUB_API_KEY - For additional financial news")
    print("\nThe demo will run with limited functionality without these keys.")


if __name__ == "__main__":
    print_api_key_help()
    run_demo() 