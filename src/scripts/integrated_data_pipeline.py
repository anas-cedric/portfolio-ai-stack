"""
Integrated Data Pipeline for Financial AI Stack

This script combines all real-time data sources:
1. Market data from Alpaca (prices, volatility, volume)
2. Economic indicators from FRED (interest rates, inflation, employment)
3. Sector performance metrics

It schedules regular updates and integrates all data into the knowledge base.
"""

import os
import sys
import time
import logging
import threading
import schedule
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.knowledge.knowledge_base import KnowledgeBase
from src.data_integration.alpaca_market_data import AlpacaMarketData
from src.data_integration.alpaca_real_time import AlpacaRealTimeIntegration
from src.data_integration.economic_indicators import EconomicDataIntegration

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/integrated_pipeline.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class IntegratedDataPipeline:
    """
    Integrated data pipeline that combines market data, economic indicators,
    and other financial data sources into a unified knowledge base.
    """
    
    def __init__(
        self,
        knowledge_base=None,
        market_update_interval=15,  # minutes
        economic_update_interval=24,  # hours (daily)
        watchlist=None
    ):
        """
        Initialize the integrated data pipeline.
        
        Args:
            knowledge_base: Knowledge base instance to use
            market_update_interval: Interval for market data updates (minutes)
            economic_update_interval: Interval for economic data updates (hours)
            watchlist: List of symbols to track
        """
        self.knowledge_base = knowledge_base or KnowledgeBase(
            namespace="integrated_financial_data"
        )
        
        # Default watchlist
        self.watchlist = watchlist or [
            "SPY",   # S&P 500 ETF
            "QQQ",   # Nasdaq 100 ETF
            "DIA",   # Dow Jones Industrial Average ETF
            "IWM",   # Russell 2000 ETF
            "VTI",   # Total Stock Market ETF
            "AAPL",  # Apple
            "MSFT",  # Microsoft
            "AMZN",  # Amazon
            "TSLA",  # Tesla
            "XLK",   # Technology Sector ETF
            "XLF",   # Financial Sector ETF
            "XLE",   # Energy Sector ETF
        ]
        
        # Initialize Alpaca client
        alpaca_keys_present = os.getenv("ALPACA_DATA_API_KEY") and os.getenv("ALPACA_DATA_API_SECRET")
        self.alpaca_client = None
        if alpaca_keys_present:
            self.alpaca_client = AlpacaMarketData(
                api_key=os.getenv("ALPACA_DATA_API_KEY"),
                api_secret=os.getenv("ALPACA_DATA_API_SECRET"),
                base_url=os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets"),
                is_free_tier=True
            )
        
        # Initialize market data integration
        self.market_integration = None
        if self.alpaca_client:
            self.market_integration = AlpacaRealTimeIntegration(
                knowledge_base=self.knowledge_base,
                alpaca_client=self.alpaca_client,
                watchlist=self.watchlist,
                update_interval=market_update_interval,
                market_hour_only=False  # Update outside market hours too
            )
        
        # Initialize economic data integration
        fred_key_present = os.getenv("FRED_API_KEY")
        self.economic_integration = None
        if fred_key_present:
            self.economic_integration = EconomicDataIntegration(
                knowledge_base=self.knowledge_base,
                fred_api_key=os.getenv("FRED_API_KEY")
            )
        
        # Settings
        self.market_update_interval = market_update_interval
        self.economic_update_interval = economic_update_interval
        
        # State
        self.is_running = False
        self.scheduler_thread = None
        
        # Log status of integrations
        self._log_integration_status()
    
    def _log_integration_status(self):
        """Log the status of each integration component."""
        logger.info("=== Integration Components Status ===")
        
        if self.alpaca_client:
            logger.info("✓ Alpaca Market Data: Connected")
        else:
            logger.warning("✗ Alpaca Market Data: Not available (missing API keys)")
            
        if self.market_integration:
            logger.info(f"✓ Market Data Integration: Ready with {len(self.watchlist)} symbols")
        else:
            logger.warning("✗ Market Data Integration: Not available")
            
        if self.economic_integration:
            logger.info(f"✓ Economic Data Integration: Ready with {len(self.economic_integration.track_indicators)} indicators")
        else:
            logger.warning("✗ Economic Data Integration: Not available (missing FRED API key)")
    
    def start(self):
        """Start the integrated data pipeline."""
        if self.is_running:
            logger.warning("Integrated data pipeline is already running")
            return
        
        logger.info("Starting integrated data pipeline")
        
        # Start market data integration if available
        if self.market_integration:
            logger.info("Starting market data integration")
            self.market_integration.start()
        else:
            logger.warning("Market data integration not available")
        
        # Schedule economic data updates if available
        if self.economic_integration:
            logger.info("Scheduling economic data updates")
            schedule.every(self.economic_update_interval).hours.do(self.update_economic_data)
            
            # Also run on startup
            self.update_economic_data()
        else:
            logger.warning("Economic data integration not available")
        
        # Start scheduler if we're handling economic data
        if self.economic_integration:
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
        
        self.is_running = True
        logger.info("Integrated data pipeline started")
    
    def _run_scheduler(self):
        """Run the scheduler in a background thread."""
        while self.is_running:
            schedule.run_pending()
            time.sleep(1)
    
    def stop(self):
        """Stop the integrated data pipeline."""
        logger.info("Stopping integrated data pipeline")
        
        # Stop the market data integration
        if self.market_integration:
            self.market_integration.stop()
        
        # Stop the scheduler
        self.is_running = False
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        # Clear all scheduled jobs
        schedule.clear()
        
        logger.info("Integrated data pipeline stopped")
    
    def update_economic_data(self):
        """Update economic indicators."""
        if not self.economic_integration:
            logger.warning("Economic data integration not available")
            return
            
        try:
            logger.info("Updating economic indicators")
            start_time = time.time()
            
            # Update all indicators
            self.economic_integration.update_economic_indicators()
            
            # Log completion
            duration = time.time() - start_time
            logger.info(f"Economic indicators updated successfully in {duration:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Error updating economic indicators: {str(e)}")
    
    def get_current_prices(self, symbols=None):
        """
        Get current prices for specific symbols.
        
        Args:
            symbols: List of symbols to check (defaults to watchlist)
            
        Returns:
            Dictionary of symbol to price mappings
        """
        if not self.alpaca_client:
            logger.warning("Alpaca client not available")
            return {}
            
        symbols_to_check = symbols or self.watchlist
        
        prices = {}
        for symbol in symbols_to_check:
            price = self.alpaca_client.get_current_price(symbol)
            if price:
                prices[symbol] = price
        
        return prices
    
    def query_knowledge_base(self, query, top_k=5):
        """
        Query the knowledge base.
        
        Args:
            query: Query string
            top_k: Number of results to return
            
        Returns:
            List of matching items
        """
        results = self.knowledge_base.query(query_text=query, top_k=top_k)
        return results
    
    def run_manual_update(self):
        """Run a manual update of all data sources."""
        logger.info("Running manual update of all data sources")
        
        if self.market_integration:
            logger.info("Updating market data...")
            self.market_integration.update_market_data()
            self.market_integration.update_sector_performance()
        
        if self.economic_integration:
            logger.info("Updating economic indicators...")
            self.update_economic_data()
        
        logger.info("Manual update completed")
        
        # Return some statistics
        return {
            "kb_stats": self.knowledge_base.get_statistics(),
            "update_time": datetime.now().isoformat()
        }


def run_demo():
    """Run a demonstration of the integrated data pipeline."""
    logger.info("Starting integrated data pipeline demo")
    
    try:
        # Initialize the pipeline
        pipeline = IntegratedDataPipeline(
            market_update_interval=15,  # 15 minutes for market data
            economic_update_interval=24  # Daily for economic data
        )
        
        # Start the pipeline
        pipeline.start()
        
        # Wait for initial data collection
        logger.info("Waiting for initial data collection (30 seconds)...")
        time.sleep(30)
        
        # Get some current prices
        prices = pipeline.get_current_prices(["SPY", "QQQ", "AAPL"])
        logger.info("Current Prices (15-min delayed):")
        for symbol, price in prices.items():
            logger.info(f"  {symbol}: ${price:.2f}")
        
        # Run for a specified time or until interrupted
        demo_runtime = 60 * 5  # 5 minutes
        end_time = time.time() + demo_runtime
        
        logger.info(f"Demo will run for {demo_runtime/60:.1f} minutes. Press Ctrl+C to stop earlier.")
        
        while time.time() < end_time:
            # Show current status every minute
            logger.info(f"Pipeline running... (press Ctrl+C to stop)")
            
            # Get knowledge base statistics
            stats = pipeline.knowledge_base.get_statistics()
            logger.info(f"Knowledge Base Items: {stats['items_added']}")
            
            # Sleep for a minute
            time.sleep(60)
        
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    finally:
        # Stop the pipeline
        pipeline.stop()
        logger.info("Demo completed")


if __name__ == "__main__":
    # Make sure the logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Run the demo
    run_demo() 