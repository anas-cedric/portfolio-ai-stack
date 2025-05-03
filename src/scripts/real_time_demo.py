"""
Real-Time Market Data Integration Demo

This script demonstrates the real-time market data integration capabilities
of the portfolio AI stack, including:
1. Alpaca market data integration (with 15-minute delay on free tier)
2. Knowledge base storage of market data
3. Retrieval and usage of market data for decision making
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

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def run_demo():
    """Run a demonstration of real-time market data integration."""
    logger.info("Starting real-time market data integration demo")
    
    # Initialize the knowledge base
    knowledge_base = KnowledgeBase(
        embedding_client_type="voyage",
        namespace="market_data_demo"
    )
    
    # Initialize Alpaca market data client
    alpaca_client = AlpacaMarketData(
        is_free_tier=True  # Explicitly set to use free tier (15-min delay)
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
        "XLE",   # Energy Sector ETF
    ]
    
    # Initialize real-time integration
    real_time = AlpacaRealTimeIntegration(
        knowledge_base=knowledge_base,
        alpaca_client=alpaca_client,
        watchlist=demo_watchlist,
        update_interval=15,  # 15 minutes minimum for free tier
        market_hour_only=False  # Allow updates outside market hours for demo
    )
    
    try:
        # Start the integration
        logger.info("Starting real-time integration")
        real_time.start()
        
        # Wait for initial data collection
        logger.info("Waiting for initial data collection (30 seconds)...")
        time.sleep(30)
        
        # Get current market data for some symbols
        logger.info("\n--- Current Market Data ---")
        for symbol in ["SPY", "AAPL", "TSLA"]:
            price = alpaca_client.get_current_price(symbol)
            logger.info(f"{symbol}: ${price:.2f} (free tier: 15-min delayed)")
        
        # Demonstrate sector performance
        logger.info("\n--- Sector Performance ---")
        real_time.update_sector_performance()  # Force update for demo
        
        # Demonstrate retrieval from knowledge base
        query_market_data(knowledge_base)
        
        # Demonstrate scheduled updates
        logger.info("\n--- Leaving integration running for demonstration ---")
        logger.info("Press Ctrl+C to stop the demo")
        
        # Keep the demo running for a certain time
        demo_run_time = 60 * 5  # 5 minutes
        end_time = time.time() + demo_run_time
        
        while time.time() < end_time:
            # Show status every minute
            logger.info(f"Integration running... (press Ctrl+C to stop)")
            time.sleep(60)
            
            # Demonstrate retrieval again to show new data
            logger.info("\n--- Updated Market Data ---")
            query_market_data(knowledge_base)
        
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    finally:
        # Stop the integration
        logger.info("Stopping real-time integration")
        real_time.stop()
        logger.info("Demo completed")
        

def query_market_data(knowledge_base):
    """Query the knowledge base for market data insights."""
    
    # Retrieve recent market data points
    logger.info("Querying knowledge base for market data...")
    
    # Query for unusual volume
    unusual_volume_query = "stocks with unusual trading volume"
    results = knowledge_base.query(
        query_text=unusual_volume_query,
        filter_categories=[knowledge_base.schema.KnowledgeCategory.MARKET_DATA.value],
        top_k=3
    )
    
    logger.info(f"\nStocks with unusual volume:")
    for i, result in enumerate(results):
        logger.info(f"{i+1}. {result.content[:200]}...")
    
    # Query for sector performance
    sector_query = "best performing market sectors today"
    results = knowledge_base.query(
        query_text=sector_query,
        filter_categories=[knowledge_base.schema.KnowledgeCategory.MARKET_DATA.value],
        top_k=3
    )
    
    logger.info(f"\nBest performing sectors:")
    for i, result in enumerate(results):
        logger.info(f"{i+1}. {result.content[:200]}...")
    
    # Get general market sentiment
    market_query = "current market sentiment and direction"
    results = knowledge_base.query(
        query_text=market_query,
        filter_categories=[knowledge_base.schema.KnowledgeCategory.MARKET_DATA.value],
        top_k=3
    )
    
    logger.info(f"\nMarket sentiment:")
    for i, result in enumerate(results):
        logger.info(f"{i+1}. {result.content[:200]}...")


if __name__ == "__main__":
    run_demo() 