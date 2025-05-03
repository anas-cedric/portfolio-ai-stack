#!/usr/bin/env python3
"""
Initialization script for the Portfolio Advisor Chatbot

This script prepares the environment for the portfolio advisor chatbot:
1. Ensures the Comprehensive_Allocation_Table.csv is available to the API
2. Validates the structure of the data
3. Provides instructions for starting the application
"""

import os
import shutil
import pandas as pd
import argparse
import json
from pathlib import Path

def init_chatbot():
    """Initialize the portfolio advisor chatbot environment"""
    print("Initializing Portfolio Advisor Chatbot...")
    
    # Check for the allocation table
    root_dir = Path(__file__).parent.absolute()
    csv_source = root_dir / "Comprehensive_Allocation_Table.csv"
    api_dir = root_dir / "src" / "api"
    data_dir = root_dir / "data"
    
    if not csv_source.exists():
        print(f"ERROR: Could not find {csv_source}")
        print("Please ensure the Comprehensive_Allocation_Table.csv is in the project root directory")
        return False
    
    # Create data directory if it doesn't exist
    data_dir.mkdir(exist_ok=True)
    
    # Copy the CSV to appropriate locations
    data_csv = data_dir / "comprehensive_allocation_table.csv"
    api_csv = api_dir / "comprehensive_allocation_table.csv"
    
    print(f"Copying allocation table to data directory: {data_csv}")
    shutil.copy(csv_source, data_csv)
    
    if api_dir.exists():
        print(f"Copying allocation table to API directory: {api_csv}")
        shutil.copy(csv_source, api_csv)

    # Validate the CSV structure
    try:
        df = pd.read_csv(csv_source)
        required_columns = [
            'Age', 'RiskTolerance', 'InvestmentHorizon', 
            'Equity%', 'Bond%', 
            'VTI%', 'VB%', 'VEA%', 'VSS%', 'VWO%', 
            'BND%', 'BNDX%'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"WARNING: The allocation table is missing these columns: {', '.join(missing_columns)}")
            return False
            
        print(f"CSV validation successful: {len(df)} allocation profiles available")
        
        # Generate ETF metadata for the chatbot
        etf_metadata = {
            "VTI": {
                "name": "Vanguard Total Stock Market ETF",
                "description": "Provides broad exposure to the US stock market, including large, mid, and small-cap equity.",
                "type": "Equity",
                "region": "US"
            },
            "VB": {
                "name": "Vanguard Small-Cap ETF",
                "description": "Focuses on smaller US companies with growth potential.",
                "type": "Equity",
                "region": "US"
            },
            "VEA": {
                "name": "Vanguard Developed Markets ETF",
                "description": "Covers stocks from developed markets outside the US.",
                "type": "Equity",
                "region": "International"
            },
            "VSS": {
                "name": "Vanguard FTSE All-World ex-US Small-Cap ETF",
                "description": "Provides international small cap exposure.",
                "type": "Equity",
                "region": "International"
            },
            "VWO": {
                "name": "Vanguard Emerging Markets ETF",
                "description": "Provides exposure to stocks in emerging economies.",
                "type": "Equity",
                "region": "Emerging Markets"
            },
            "BND": {
                "name": "Vanguard Total Bond Market ETF",
                "description": "Broad exposure to US investment-grade bonds, including government and corporate bonds.",
                "type": "Bond",
                "region": "US"
            },
            "BNDX": {
                "name": "Vanguard Total International Bond ETF",
                "description": "Hedged exposure to investment-grade bonds issued outside the US.",
                "type": "Bond",
                "region": "International"
            }
        }
        
        # Save ETF metadata
        etf_file = data_dir / "etf_metadata.json"
        with open(etf_file, 'w') as f:
            json.dump(etf_metadata, f, indent=2)
            
        print(f"Created ETF metadata file: {etf_file}")
        
    except Exception as e:
        print(f"ERROR validating CSV: {str(e)}")
        return False
    
    # Success message with next steps
    print("\n=== Initialization Complete ===")
    print("\nNext steps:")
    print("1. Start the API server:        python start_api.py")
    print("2. Navigate to frontend:        cd frontend/portfolio-advisor")
    print("3. Install frontend deps:       npm install")
    print("4. Start the frontend:          npm run dev")
    print("\nThe chatbot will be available at: http://localhost:3000\n")
    
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize the Portfolio Advisor Chatbot")
    args = parser.parse_args()
    
    success = init_chatbot()
    exit(0 if success else 1) 