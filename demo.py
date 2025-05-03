#!/usr/bin/env python3
"""
Financial Analysis Demo.

This script demonstrates a complete workflow using all components 
of the financial analysis system.
"""

import os
import sys
import json
import logging
import argparse
import pandas as pd
from typing import Dict, Any, Optional, List

# Add the current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("financial_demo")

# Import our components
from src.data_integration.financial_dataset_loader import FinancialDatasetLoader
from src.document_processing.formatting import TabularFormatter, CompactNumberFormatter
from src.document_processing.summarization import DocumentSummarizer
from src.document_processing.market_aware import VolatilityAwareRetriever
from src.workflow.financial_analysis_flow import FinancialAnalysisWorkflow


def prepare_sample_dataset(output_dir: str):
    """
    Create a sample financial dataset for demonstration.
    
    Args:
        output_dir: Directory to save the sample dataset
    """
    logger.info("Creating sample financial dataset")
    
    # Create directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a sample financial statements dataset
    financial_data = []
    
    # Generate some quarterly financial data for Apple
    quarters = ["2022-Q1", "2022-Q2", "2022-Q3", "2022-Q4", "2023-Q1", "2023-Q2"]
    
    # Base values
    revenue_base = 90000  # $90B
    net_income_base = 25000  # $25B
    
    # Generate data with some growth
    for i, quarter in enumerate(quarters):
        # Add some growth and quarterly variation
        revenue = revenue_base * (1 + 0.02 * i + (0.05 if i % 2 == 0 else -0.02))
        net_income = net_income_base * (1 + 0.015 * i + (0.03 if i % 2 == 0 else -0.01))
        
        financial_data.append({
            "company": "Apple Inc.",
            "ticker": "AAPL",
            "period": quarter,
            "date": f"2022-{(i%4)*3+1:02d}-01" if i < 4 else f"2023-{(i%4)*3+1:02d}-01",
            "revenue": revenue,
            "cost_of_revenue": revenue * 0.62,
            "gross_profit": revenue * 0.38,
            "operating_expenses": revenue * 0.15,
            "operating_income": revenue * 0.23,
            "net_income": net_income,
            "eps": net_income / 16000,  # Assume 16B shares outstanding
            "shares_outstanding": 16000,
            "cash": 50000 + net_income * 0.4 * i,
            "total_assets": 350000 + net_income * i,
            "total_liabilities": 250000 + (net_income * 0.1 * i),
            "total_equity": 100000 + (net_income * 0.9 * i),
        })
    
    # Convert to dataframe and save
    df = pd.DataFrame(financial_data)
    output_path = os.path.join(output_dir, "apple_financials.csv")
    df.to_csv(output_path, index=False)
    
    logger.info(f"Sample dataset created at: {output_path}")
    return output_path


def run_analysis_demo(dataset_path: str, query: str):
    """
    Run a complete financial analysis workflow.
    
    Args:
        dataset_path: Path to the dataset
        query: Analysis query
    """
    logger.info("Starting financial analysis demo")
    
    # Step 1: Initialize components
    logger.info("Initializing components...")
    
    dataset_loader = FinancialDatasetLoader(
        dataset_dir=os.path.dirname(dataset_path)
    )
    
    tabular_formatter = TabularFormatter(max_width=120, precision=2)
    number_formatter = CompactNumberFormatter(precision=2)
    
    # Step 2: Load and preprocess dataset
    logger.info("Loading dataset...")
    dataset_name = os.path.splitext(os.path.basename(dataset_path))[0]
    
    try:
        data = dataset_loader.load_dataset(
            dataset_name=dataset_name,
            dataset_type="financial_statements",
            preprocessed=True
        )
        logger.info(f"Loaded dataset with {len(data)} records")
        
        # Step 3: Format the data
        logger.info("Formatting financial data...")
        formatted_data = tabular_formatter.format_dataframe(data)
        print("\nFORMATTED FINANCIAL DATA:")
        print("="*80)
        print(formatted_data)
        
        # Step 4: Calculate and format some metrics
        metrics = calculate_financial_metrics(data)
        formatted_metrics = tabular_formatter.format_dict(metrics)
        print("\nFINANCIAL METRICS:")
        print("="*80)
        print(formatted_metrics)
        
        # Step 5: Check market volatility
        logger.info("Checking market volatility...")
        retriever = VolatilityAwareRetriever()
        market_context = retriever.get_market_context()
        
        print("\nMARKET CONTEXT:")
        print("="*80)
        print(f"Current volatility: {market_context['volatility']:.2f}")
        print(f"Is high volatility: {market_context['is_high_volatility']}")
        print(f"Context message: {market_context['context_message']}")
        
        # Step 6: Run the complete workflow
        logger.info("Running complete analysis workflow...")
        workflow = FinancialAnalysisWorkflow()
        
        result = workflow.execute(
            query=query,
            dataset_name=dataset_name,
            dataset_type="financial_statements"
        )
        
        # Step 7: Display results
        print("\nANALYSIS RESULT:")
        print("="*80)
        if result.get("error"):
            print(f"Error: {result['error']}")
        else:
            print(result["analysis_result"])
        
        logger.info("Analysis demo completed")
        
    except Exception as e:
        logger.error(f"Error in analysis demo: {str(e)}")
        print(f"ERROR: {str(e)}")


def calculate_financial_metrics(data: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate financial metrics from the dataset.
    
    Args:
        data: Financial statements data
        
    Returns:
        Dictionary of financial metrics
    """
    # Sort by date
    data = data.sort_values(by='date')
    
    # Calculate growth rates
    revenue_growth = (data['revenue'].iloc[-1] / data['revenue'].iloc[0]) - 1
    net_income_growth = (data['net_income'].iloc[-1] / data['net_income'].iloc[0]) - 1
    
    # Calculate margins
    gross_margin = data['gross_profit'].mean() / data['revenue'].mean()
    operating_margin = data['operating_income'].mean() / data['revenue'].mean()
    net_margin = data['net_income'].mean() / data['revenue'].mean()
    
    # Calculate average quarterly growth
    revenue_qoq = []
    for i in range(1, len(data)):
        qoq = (data['revenue'].iloc[i] / data['revenue'].iloc[i-1]) - 1
        revenue_qoq.append(qoq)
    
    avg_qoq_growth = sum(revenue_qoq) / len(revenue_qoq) if revenue_qoq else 0
    
    return {
        'revenue_growth': revenue_growth,
        'net_income_growth': net_income_growth,
        'gross_margin': gross_margin,
        'operating_margin': operating_margin,
        'net_margin': net_margin,
        'avg_quarterly_growth': avg_qoq_growth,
        'latest_revenue': data['revenue'].iloc[-1],
        'latest_net_income': data['net_income'].iloc[-1],
        'latest_eps': data['eps'].iloc[-1]
    }


def main():
    """Run the demo."""
    parser = argparse.ArgumentParser(description="Financial Analysis Demo")
    parser.add_argument("--query", default="Analyze Apple's financial performance and growth trends.", 
                       help="Analysis query")
    parser.add_argument("--dataset", help="Path to existing dataset (if not provided, sample will be created)")
    args = parser.parse_args()
    
    # Create a sample dataset if not provided
    dataset_path = args.dataset
    if not dataset_path:
        data_dir = os.path.join("data", "datasets", "financial_statements")
        dataset_path = prepare_sample_dataset(data_dir)
    
    # Run the analysis
    run_analysis_demo(dataset_path, args.query)


if __name__ == "__main__":
    main() 