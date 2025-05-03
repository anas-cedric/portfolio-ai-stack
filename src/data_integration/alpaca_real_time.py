"""
Real-time Alpaca Market Data Integration Module

This module bridges the Alpaca market data client with the knowledge base,
continuously fetching market data and transforming it into the appropriate
knowledge structures for storage and retrieval.

Key features:
1. Regular data collection from Alpaca API (with free tier 15-min delay considerations)
2. Transformation into knowledge schema types
3. Storage in vector database via knowledge base
4. Background processing to maintain up-to-date market information
"""

import os
import time
import logging
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
import threading
import schedule
import pandas as pd
import numpy as np

from src.data_integration.alpaca_market_data import AlpacaMarketData
from src.knowledge.knowledge_base import KnowledgeBase
from src.knowledge.schema import (
    MarketDataPoint,
    SectorPerformance,
    FinancialNews,
    KnowledgeCategory
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlpacaRealTimeIntegration:
    """
    Integrates real-time (delayed for free tier) Alpaca market data with the knowledge base.
    
    This class handles:
    1. Scheduled data collection from Alpaca
    2. Data transformation to knowledge base schemas
    3. Storage of market data in the knowledge base
    4. Calculation of derived metrics (RSI, volatility, etc.)
    """
    
    def __init__(
        self,
        knowledge_base: Optional[KnowledgeBase] = None,
        alpaca_client: Optional[AlpacaMarketData] = None,
        watchlist: Optional[List[str]] = None,
        sector_etfs: Optional[Dict[str, str]] = None,
        update_interval: int = 15,  # minutes
        market_hour_only: bool = True
    ):
        """
        Initialize the real-time data integration.
        
        Args:
            knowledge_base: Knowledge base instance for storing data
            alpaca_client: Pre-configured Alpaca client
            watchlist: List of symbols to track
            sector_etfs: Dictionary mapping sectors to representative ETFs
            update_interval: Data update interval in minutes (minimum 15 for free tier)
            market_hour_only: Whether to update only during market hours
        """
        self.knowledge_base = knowledge_base or KnowledgeBase()
        self.alpaca_client = alpaca_client or AlpacaMarketData()
        
        # Default watchlist of major ETFs if none provided
        self.watchlist = watchlist or [
            "SPY",  # S&P 500
            "QQQ",  # Nasdaq 100
            "DIA",  # Dow Jones
            "IWM",  # Russell 2000
            "GLD",  # Gold
            "SLV",  # Silver
            "USO",  # Oil
            "TLT",  # 20+ Year Treasury
            "VXX",  # Volatility Index
        ]
        
        # Default sector ETFs if none provided
        self.sector_etfs = sector_etfs or {
            "technology": "XLK",
            "healthcare": "XLV",
            "financials": "XLF",
            "consumer_discretionary": "XLY",
            "consumer_staples": "XLP",
            "industrials": "XLI",
            "energy": "XLE",
            "utilities": "XLU",
            "materials": "XLB",
            "real_estate": "XLRE",
            "communication_services": "XLC"
        }
        
        # Settings
        self.update_interval = max(15, update_interval)  # Minimum 15 minutes for free tier
        self.market_hour_only = market_hour_only
        
        # State tracking
        self.is_running = False
        self.last_update_time = None
        self.scheduler_thread = None
        self.historical_data = {}  # Cache for historical price data
        
        logger.info(f"Initialized AlpacaRealTimeIntegration with {len(self.watchlist)} symbols")
        
    def start(self):
        """Start the scheduled data collection."""
        if self.is_running:
            logger.warning("Real-time integration is already running")
            return
            
        # Schedule market data updates
        minutes_str = f"*/{self.update_interval}" if self.update_interval < 60 else f"{self.update_interval//60}"
        schedule.every(self.update_interval).minutes.do(self.update_market_data)
        
        # Also update sector performance daily
        schedule.every().day.at("16:30").do(self.update_sector_performance)
        
        # Start the scheduler in a background thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.is_running = True
        logger.info(f"Started real-time data integration (update interval: {self.update_interval} minutes)")
        
        # Perform an initial update
        self.update_market_data()
        self.update_sector_performance()
        
    def _run_scheduler(self):
        """Run the scheduler in a background thread."""
        while self.is_running:
            schedule.run_pending()
            time.sleep(1)
            
    def stop(self):
        """Stop the scheduled data collection."""
        self.is_running = False
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        schedule.clear()
        logger.info("Stopped real-time data integration")
        
    def update_market_data(self):
        """
        Update market data for all symbols in the watchlist.
        
        This method fetches current prices and calculates derived metrics 
        for each symbol in the watchlist, then stores the data in the knowledge base.
        """
        # Check if market is open (if market_hour_only is True)
        if self.market_hour_only:
            is_market_open = self._is_market_open()
            if not is_market_open:
                logger.info("Market is closed, skipping market data update")
                return
        
        logger.info(f"Updating market data for {len(self.watchlist)} symbols")
        current_time = datetime.now().isoformat()
        self.last_update_time = current_time
        
        for symbol in self.watchlist:
            try:
                # Get current price (with 15-min delay on free tier)
                price = self.alpaca_client.get_current_price(symbol)
                if price is None:
                    logger.warning(f"Could not get price for {symbol}, skipping")
                    continue
                
                # Get historical data for calculations
                historical_bars = self._get_cached_bars(symbol, timeframe="1Day", limit=30)
                
                if historical_bars.empty:
                    logger.warning(f"No historical data for {symbol}, limited metrics available")
                    # Create basic market data point
                    data_point = MarketDataPoint(
                        timestamp=current_time,
                        symbol=symbol,
                        price=price,
                        price_change=0.0,
                        price_change_percent=0.0,
                        source="alpaca"
                    )
                else:
                    # Calculate price change
                    if len(historical_bars) >= 2:
                        yesterday_close = historical_bars['close'].iloc[-2]
                        price_change = price - yesterday_close
                        price_change_percent = (price_change / yesterday_close) * 100
                    else:
                        price_change = 0.0
                        price_change_percent = 0.0
                    
                    # Calculate RSI if enough data
                    rsi_14d = self._calculate_rsi(historical_bars) if len(historical_bars) >= 15 else None
                    
                    # Calculate 30-day volatility
                    volatility_30d = self._calculate_volatility(historical_bars) if len(historical_bars) >= 10 else None
                    
                    # Get volume and check for unusual volume
                    latest_volume = historical_bars['volume'].iloc[-1] if not historical_bars.empty else None
                    unusual_volume = False
                    volume_change_percent = None
                    
                    if latest_volume is not None and len(historical_bars) >= 10:
                        avg_volume = historical_bars['volume'].iloc[-10:-1].mean()
                        if avg_volume > 0:
                            volume_change_percent = ((latest_volume - avg_volume) / avg_volume) * 100
                            unusual_volume = volume_change_percent > 100  # 2x average volume is unusual
                    
                    # Create market data point
                    data_point = MarketDataPoint(
                        timestamp=current_time,
                        symbol=symbol,
                        price=price,
                        price_change=price_change,
                        price_change_percent=price_change_percent,
                        volume=latest_volume,
                        volume_change_percent=volume_change_percent,
                        rsi_14d=rsi_14d,
                        volatility_30d=volatility_30d,
                        unusual_volume=unusual_volume,
                        source="alpaca"
                    )
                
                # Store in knowledge base
                self.knowledge_base.add_market_data_point(data_point)
                logger.debug(f"Added market data for {symbol}: ${price:.2f} ({price_change_percent:.2f}%)")
                
            except Exception as e:
                logger.error(f"Error updating market data for {symbol}: {str(e)}")
        
        logger.info(f"Completed market data update for {len(self.watchlist)} symbols")
        
    def update_sector_performance(self):
        """
        Update sector performance data using sector ETFs.
        
        This method calculates daily, weekly, and monthly returns for sector ETFs
        and stores the data in the knowledge base.
        """
        logger.info(f"Updating sector performance for {len(self.sector_etfs)} sectors")
        current_time = datetime.now().isoformat()
        
        for sector, etf in self.sector_etfs.items():
            try:
                # Get historical data for the sector ETF
                bars = self._get_cached_bars(etf, timeframe="1Day", limit=30)
                
                if bars.empty:
                    logger.warning(f"No historical data for sector ETF {etf}, skipping")
                    continue
                
                # Calculate returns
                prices = bars['close']
                
                # Daily return
                if len(prices) >= 2:
                    daily_return = ((prices.iloc[-1] / prices.iloc[-2]) - 1) * 100
                else:
                    daily_return = 0.0
                
                # Weekly return
                weekly_return = ((prices.iloc[-1] / prices.iloc[-5]) - 1) * 100 if len(prices) >= 6 else None
                
                # Monthly return
                monthly_return = ((prices.iloc[-1] / prices.iloc[-20]) - 1) * 100 if len(prices) >= 21 else None
                
                # YTD return (approximate using available data)
                first_day_idx = 0
                ytd_return = ((prices.iloc[-1] / prices.iloc[first_day_idx]) - 1) * 100
                
                # Get SPY for relative strength calculation
                spy_bars = self._get_cached_bars("SPY", timeframe="1Day", limit=30)
                relative_strength = None
                
                if not spy_bars.empty and len(spy_bars) >= 2:
                    spy_daily_return = ((spy_bars['close'].iloc[-1] / spy_bars['close'].iloc[-2]) - 1) * 100
                    # Relative strength = sector return / market return
                    if spy_daily_return != 0:
                        relative_strength = daily_return / spy_daily_return
                
                # Create sector performance object
                sector_performance = SectorPerformance(
                    timestamp=current_time,
                    sector=sector,
                    daily_return=daily_return,
                    weekly_return=weekly_return,
                    monthly_return=monthly_return,
                    ytd_return=ytd_return,
                    relative_strength=relative_strength,
                    source="alpaca"
                )
                
                # Store in knowledge base
                self.knowledge_base.add_sector_performance(sector_performance)
                logger.debug(f"Added performance for {sector}: daily: {daily_return:.2f}%, relative strength: {relative_strength:.2f}")
                
            except Exception as e:
                logger.error(f"Error updating sector performance for {sector} ({etf}): {str(e)}")
        
        logger.info(f"Completed sector performance update")
            
    def _get_cached_bars(self, symbol, timeframe="1Day", limit=30):
        """
        Get historical bars with caching to reduce API calls.
        
        Args:
            symbol: The stock symbol
            timeframe: Bar timeframe (e.g., "1Day", "1Hour")
            limit: Maximum number of bars to return
            
        Returns:
            DataFrame with historical bars
        """
        cache_key = f"{symbol}_{timeframe}"
        current_date = datetime.now().date()
        
        # Check if we have cached data from today
        if (cache_key in self.historical_data and 
            self.historical_data[cache_key]['date'] == current_date and
            len(self.historical_data[cache_key]['data']) >= limit):
            return self.historical_data[cache_key]['data']
        
        # Fetch new data
        try:
            end = datetime.now()
            if timeframe == "1Day":
                # For daily bars, get more than needed to ensure we have enough trading days
                start = end - timedelta(days=limit * 2)
            else:
                # For intraday bars, just get what we need
                if timeframe.endswith('Min'):
                    mins = int(timeframe.replace('Min', ''))
                    start = end - timedelta(minutes=mins * limit)
                elif timeframe.endswith('Hour'):
                    hours = int(timeframe.replace('Hour', ''))
                    start = end - timedelta(hours=hours * limit)
            
            bars = self.alpaca_client.get_historical_bars(
                symbol=symbol,
                timeframe=timeframe,
                start=start,
                end=end,
                limit=limit
            )
            
            # Cache the result
            self.historical_data[cache_key] = {
                'date': current_date,
                'data': bars
            }
            
            return bars
            
        except Exception as e:
            logger.error(f"Error fetching historical bars for {symbol}: {str(e)}")
            return pd.DataFrame()  # Return empty DataFrame on error
    
    def _calculate_rsi(self, prices_df, window=14):
        """
        Calculate the Relative Strength Index.
        
        Args:
            prices_df: DataFrame with price data
            window: RSI window (typically 14 days)
            
        Returns:
            RSI value or None if insufficient data
        """
        if len(prices_df) < window + 1:
            return None
            
        try:
            # Get close prices
            prices = prices_df['close']
            
            # Calculate price changes
            deltas = prices.diff()
            
            # Calculate gains and losses
            gain = deltas.copy()
            loss = deltas.copy()
            gain[gain < 0] = 0
            loss[loss > 0] = 0
            loss = -loss
            
            # Calculate average gain and loss
            avg_gain = gain.rolling(window=window).mean()
            avg_loss = loss.rolling(window=window).mean()
            
            # Calculate RS and RSI
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            # Return the most recent RSI value
            return rsi.iloc[-1]
            
        except Exception as e:
            logger.error(f"Error calculating RSI: {str(e)}")
            return None
    
    def _calculate_volatility(self, prices_df, window=30):
        """
        Calculate price volatility as annualized standard deviation of returns.
        
        Args:
            prices_df: DataFrame with price data
            window: Volatility window (typically 30 days)
            
        Returns:
            Annualized volatility percentage or None if insufficient data
        """
        if len(prices_df) < window // 2:
            return None
            
        try:
            # Get close prices
            prices = prices_df['close']
            
            # Calculate daily returns
            returns = prices.pct_change().dropna()
            
            # Calculate standard deviation of returns
            std_dev = returns.rolling(window=min(len(returns), window)).std().iloc[-1]
            
            # Annualize (multiply by sqrt of trading days per year)
            annualized_vol = std_dev * (252 ** 0.5) * 100
            
            return annualized_vol
            
        except Exception as e:
            logger.error(f"Error calculating volatility: {str(e)}")
            return None
    
    def _is_market_open(self):
        """
        Check if the market is currently open.
        
        Returns:
            Boolean indicating if market is open
        """
        # Get current time in US Eastern time
        now = datetime.now()
        
        # Check if it's a weekday
        if now.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
            return False
            
        # Check if it's between 9:30 AM and 4:00 PM Eastern
        hour = now.hour
        minute = now.minute
        
        # Simple approximation (doesn't account for holidays)
        market_open = (hour > 9 or (hour == 9 and minute >= 30)) and hour < 16
        
        return market_open
        
    def add_custom_symbol(self, symbol):
        """
        Add a custom symbol to the watchlist.
        
        Args:
            symbol: Stock symbol to add
        """
        if symbol not in self.watchlist:
            self.watchlist.append(symbol)
            logger.info(f"Added {symbol} to watchlist")
            
    def remove_symbol(self, symbol):
        """
        Remove a symbol from the watchlist.
        
        Args:
            symbol: Stock symbol to remove
        """
        if symbol in self.watchlist:
            self.watchlist.remove(symbol)
            logger.info(f"Removed {symbol} from watchlist") 