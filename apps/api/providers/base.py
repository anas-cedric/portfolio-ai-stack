"""
Base provider interface for brokerage integrations
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

class Provider(ABC):
    """Abstract base class for brokerage providers"""
    
    @abstractmethod
    async def start_kyc(self, user_data: Dict[str, Any]) -> str:
        """
        Start KYC process for a user
        Returns: KYC application ID
        """
        pass
    
    @abstractmethod
    async def open_account(self, user_id: str) -> str:
        """
        Open a brokerage account
        Returns: External account ID
        """
        pass
    
    @abstractmethod
    async def create_deposit(
        self, 
        account_id: str, 
        amount_cents: int,
        funding_source_id: Optional[str] = None
    ) -> str:
        """
        Create a deposit transfer
        Returns: Transfer reference ID
        """
        pass
    
    @abstractmethod
    async def place_orders(self, orders: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Place multiple orders
        Args:
            orders: List of order dicts with symbol, side, qty, etc
        Returns: Dict mapping symbol to order ID
        """
        pass
    
    @abstractmethod
    async def fetch_positions(self, account_id: str) -> List[Dict[str, Any]]:
        """
        Fetch current positions for an account
        Returns: List of position dicts with symbol, qty, market_value, etc
        """
        pass
    
    @abstractmethod
    async def get_market_data(self, symbols: List[str]) -> Dict[str, float]:
        """
        Get current market prices for symbols
        Returns: Dict mapping symbol to current price
        """
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an open order
        Returns: True if successful
        """
        pass
    
    @abstractmethod
    async def get_account_status(self, account_id: str) -> Dict[str, Any]:
        """
        Get account status and details
        Returns: Account status dict
        """
        pass
    
    def validate_order(self, order: Dict[str, Any]) -> bool:
        """
        Validate order parameters
        """
        required_fields = ["symbol", "side", "qty"]
        if not all(field in order for field in required_fields):
            return False
        
        # Check instrument whitelist
        whitelist = ["VTI", "VEA", "VWO", "VSS", "VBR", "VUG", 
                    "BND", "BNDX", "VNQ", "VNQI", "VTIP", "BIL", 
                    "SCHP", "VXUS"]
        if order["symbol"] not in whitelist:
            return False
        
        # Check min order size ($50)
        if order.get("notional", 0) < 50 and order.get("qty", 0) == 0:
            return False
        
        return True
    
    def calculate_commission(self, order: Dict[str, Any]) -> float:
        """
        Calculate commission for an order
        Default: $0 for ETFs
        """
        return 0.0