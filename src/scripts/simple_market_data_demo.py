"""
Simple Market Data Demo

A streamlined demo focusing only on Alpaca market data integration,
without requiring additional API keys for news or economic data.
"""

import os
import sys
import time
import logging
from datetime import datetime
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


def run_simple_demo():
    """Run a simple demonstration of market data integration."""
    logger.info("Starting simple market data demo")
    
    # Check if Alpaca keys are present
    if not os.getenv("ALPACA_DATA_API_KEY") or not os.getenv("ALPACA_DATA_API_SECRET"):
        logger.error("Alpaca API keys not found in .env file")
        logger.error("Please set ALPACA_DATA_API_KEY and ALPACA_DATA_API_SECRET in your .env file")
        return
    
    # Initialize the knowledge base
    knowledge_base = KnowledgeBase(
        embedding_client_type="voyage",
        namespace="market_data_demo"
    )
    
    # Initialize Alpaca market data client with the correct environment variable names
    alpaca_client = AlpacaMarketData(
        api_key=os.getenv("ALPACA_DATA_API_KEY"),
        api_secret=os.getenv("ALPACA_DATA_API_SECRET"),
        base_url=os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets"),
        is_free_tier=True  # Using free tier (15-min delay)
    )
    
    # Custom watchlist for the demo - focusing on major ETFs and indices
    demo_watchlist = [
        "SPY",   # S&P 500 ETF
        "QQQ",   # Nasdaq 100 ETF
        "DIA",   # Dow Jones Industrial Average ETF
        "IWM",   # Russell 2000 ETF
        "VTI",   # Total Stock Market ETF
        "AAPL",  # Apple (popular stock example)
        "TSLA",  # Tesla (popular stock example)
        "XLK",   # Technology Sector ETF
        "XLF",   # Financial Sector ETF
        "XLE",   # Energy Sector ETF
    ]
    
    # Initialize market data integration
    market_integration = AlpacaRealTimeIntegration(
        knowledge_base=knowledge_base,
        alpaca_client=alpaca_client,
        watchlist=demo_watchlist,
        update_interval=15,  # 15 minutes minimum for free tier
        market_hour_only=False  # Allow updates outside market hours for demo
    )
    
    try:
        # Display current watchlist
        logger.info(f"Watchlist: {', '.join(demo_watchlist)}")
        
        # Start market data integration
        logger.info("Starting market data integration...")
        market_integration.start()
        
        # Wait for initial data collection
        logger.info("Waiting for initial data collection (20 seconds)...")
        time.sleep(20)
        
        # Get current prices for watchlist
        logger.info("\n=== Current Market Prices (15-min delayed) ===")
        for symbol in demo_watchlist:
            price = alpaca_client.get_current_price(symbol)
            if price:
                logger.info(f"{symbol}: ${price:.2f}")
            else:
                logger.info(f"{symbol}: Data not available")
        
        # Force an update of sector performance
        logger.info("\n=== Updating Sector Performance ===")
        market_integration.update_sector_performance()
        time.sleep(5)  # Give it a moment to process
        
        # Query the knowledge base for market insights
        logger.info("\n=== Market Data Queries ===")
        
        queries = [
            "technology sector performance",
            "stocks with high volatility",
            "current market prices for major indices",
            "energy sector performance",
            "market sectors relative strength"
        ]
        
        for query in queries:
            results = knowledge_base.query(
                query_text=query,
                filter_categories=[knowledge_base.schema.KnowledgeCategory.MARKET_DATA.value],
                top_k=2
            )
            
            logger.info(f"\nQuery: {query}")
            if results:
                for i, result in enumerate(results):
                    logger.info(f"Result {i+1}: {result.content[:300]}...")
            else:
                logger.info("No results found")
        
        # Show statistics
        logger.info("\n=== Knowledge Base Statistics ===")
        stats = knowledge_base.get_statistics()
        logger.info(f"Total Items Added: {stats['items_added']}")
        logger.info("Items by Category:")
        for category, count in stats["items_by_category"].items():
            logger.info(f"  - {category}: {count}")
        logger.info(f"Last Updated: {stats['last_updated']}")
        
        # Allow the user to add a custom symbol
        custom_symbol = input("\nEnter a stock symbol to add to the watchlist (or press Enter to skip): ").strip().upper()
        if custom_symbol:
            logger.info(f"Adding {custom_symbol} to watchlist...")
            market_integration.add_custom_symbol(custom_symbol)
            time.sleep(10)  # Wait for data collection
            
            # Get price for the new symbol
            price = alpaca_client.get_current_price(custom_symbol)
            if price:
                logger.info(f"{custom_symbol}: ${price:.2f}")
            else:
                logger.info(f"{custom_symbol}: Data not available")
        
        # Demonstrate running for a few minutes
        logger.info("\n=== Continuous Monitoring ===")
        logger.info("Monitoring market data for 2 minutes... (press Ctrl+C to stop)")
        
        end_time = time.time() + 120  # 2 minutes
        while time.time() < end_time:
            time.sleep(30)
            logger.info(f"Market data integration running... (Time: {datetime.now().strftime('%H:%M:%S')})")
            
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    finally:
        # Stop the market data integration
        logger.info("Stopping market data integration...")
        market_integration.stop()
        logger.info("Demo completed")


if __name__ == "__main__":
    print("Simple Market Data Demo")
    print("This demo requires Alpaca API keys (ALPACA_DATA_API_KEY and ALPACA_DATA_API_SECRET) in your .env file")
    run_simple_demo() 