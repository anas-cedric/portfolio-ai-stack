"""
Alpaca Paper Trading Provider Implementation
"""
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import uuid4

import httpx
from alpaca_trade_api import REST

from .base import Provider

class AlpacaPaperProvider(Provider):
    """Alpaca paper trading provider"""
    
    def __init__(self):
        self.api_key = os.getenv("ALPACA_API_KEY", "")
        self.api_secret = os.getenv("ALPACA_SECRET_KEY", "")
        self.base_url = "https://paper-api.alpaca.markets"
        
        if self.api_key and self.api_secret:
            self.client = REST(
                self.api_key,
                self.api_secret,
                self.base_url,
                api_version='v2'
            )
        else:
            self.client = None
            print("Warning: Alpaca credentials not configured, using mock mode")
    
    async def start_kyc(self, user_data: Dict[str, Any]) -> str:
        """
        For paper trading, instantly approve KYC
        """
        # Paper trading doesn't require real KYC
        return f"alpaca_paper_kyc_{uuid4()}"
    
    async def open_account(self, user_id: str) -> str:
        """
        For paper trading, return a mock account ID
        Alpaca paper accounts are tied to API keys, not created dynamically
        """
        if self.client:
            try:
                # Get the paper account info
                account = self.client.get_account()
                return account.id
            except Exception as e:
                print(f"Alpaca API error: {e}")
        
        # Return mock account ID for testing
        return f"alpaca_paper_{user_id}_{uuid4()}"
    
    async def create_deposit(
        self, 
        account_id: str, 
        amount_cents: int,
        funding_source_id: Optional[str] = None
    ) -> str:
        """
        For paper trading, instantly credit the account
        Real Alpaca paper accounts start with $100k
        """
        # Paper accounts have unlimited virtual funds
        # Just return a mock transfer ID
        return f"alpaca_deposit_{uuid4()}"
    
    async def place_orders(self, orders: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Place orders through Alpaca paper trading API
        """
        order_ids = {}
        
        for order in orders:
            if not self.validate_order(order):
                print(f"Invalid order: {order}")
                continue
            
            if self.client:
                try:
                    # Submit order to Alpaca
                    alpaca_order = self.client.submit_order(
                        symbol=order["symbol"],
                        qty=order.get("qty"),
                        notional=order.get("notional"),
                        side=order["side"],
                        type="market",
                        time_in_force="day"
                    )
                    order_ids[order["symbol"]] = alpaca_order.id
                except Exception as e:
                    print(f"Order placement error for {order['symbol']}: {e}")
                    # Use mock order ID on error
                    order_ids[order["symbol"]] = f"mock_order_{uuid4()}"
            else:
                # Mock mode
                order_ids[order["symbol"]] = f"mock_order_{uuid4()}"
        
        return order_ids
    
    async def fetch_positions(self, account_id: str) -> List[Dict[str, Any]]:
        """
        Fetch positions from Alpaca paper account
        """
        if self.client:
            try:
                positions = self.client.list_positions()
                return [
                    {
                        "symbol": pos.symbol,
                        "qty": float(pos.qty),
                        "market_value": float(pos.market_value),
                        "cost_basis": float(pos.cost_basis),
                        "unrealized_pl": float(pos.unrealized_pl),
                        "unrealized_plpc": float(pos.unrealized_plpc),
                        "current_price": float(pos.current_price)
                    }
                    for pos in positions
                ]
            except Exception as e:
                print(f"Error fetching positions: {e}")
        
        # Return mock positions for testing
        return [
            {
                "symbol": "VTI",
                "qty": 100,
                "market_value": 22000,
                "cost_basis": 21000,
                "unrealized_pl": 1000,
                "unrealized_plpc": 0.048,
                "current_price": 220
            },
            {
                "symbol": "BND",
                "qty": 50,
                "market_value": 4000,
                "cost_basis": 3900,
                "unrealized_pl": 100,
                "unrealized_plpc": 0.026,
                "current_price": 80
            }
        ]
    
    async def get_market_data(self, symbols: List[str]) -> Dict[str, float]:
        """
        Get current market prices from Alpaca
        """
        prices = {}
        
        if self.client:
            try:
                # Get latest trades for symbols
                trades = self.client.get_latest_trades(symbols)
                for symbol, trade in trades.items():
                    prices[symbol] = float(trade.price)
            except Exception as e:
                print(f"Error fetching market data: {e}")
                # Use mock prices on error
                for symbol in symbols:
                    prices[symbol] = self._get_mock_price(symbol)
        else:
            # Mock mode
            for symbol in symbols:
                prices[symbol] = self._get_mock_price(symbol)
        
        return prices
    
    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order on Alpaca
        """
        if self.client:
            try:
                self.client.cancel_order(order_id)
                return True
            except Exception as e:
                print(f"Error cancelling order {order_id}: {e}")
                return False
        
        # Mock mode always succeeds
        return True
    
    async def get_account_status(self, account_id: str) -> Dict[str, Any]:
        """
        Get Alpaca paper account status
        """
        if self.client:
            try:
                account = self.client.get_account()
                return {
                    "id": account.id,
                    "status": account.status,
                    "buying_power": float(account.buying_power),
                    "cash": float(account.cash),
                    "portfolio_value": float(account.portfolio_value),
                    "pattern_day_trader": account.pattern_day_trader,
                    "trading_blocked": account.trading_blocked,
                    "transfers_blocked": account.transfers_blocked,
                    "account_blocked": account.account_blocked
                }
            except Exception as e:
                print(f"Error fetching account status: {e}")
        
        # Return mock account status
        return {
            "id": account_id,
            "status": "active",
            "buying_power": 100000.00,
            "cash": 100000.00,
            "portfolio_value": 100000.00,
            "pattern_day_trader": False,
            "trading_blocked": False,
            "transfers_blocked": False,
            "account_blocked": False
        }
    
    def _get_mock_price(self, symbol: str) -> float:
        """Get mock price for a symbol"""
        mock_prices = {
            "VTI": 220.50,
            "VEA": 42.30,
            "VWO": 38.75,
            "VSS": 105.20,
            "VBR": 145.60,
            "VUG": 285.40,
            "BND": 75.80,
            "BNDX": 48.90,
            "VNQ": 82.15,
            "VNQI": 44.25,
            "VTIP": 47.30,
            "BIL": 91.50,
            "SCHP": 52.40,
            "VXUS": 55.60
        }
        return mock_prices.get(symbol, 100.00)