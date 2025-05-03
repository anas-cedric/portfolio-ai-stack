"""
Examples for using the document processing modules.

This file demonstrates how to use the various document processing components:
1. TabularFormatter - Format financial data in tabular format
2. CompactNumberFormatter - Format numbers in compact financial notation
3. DocumentSummarizer - Create summaries of financial documents
4. VolatilityAwareRetriever - Adjust retrieval based on market volatility
"""

import os
import sys
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from typing import Dict, List, Any

# Add the project root to the path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Import our document processing modules
from src.document_processing.formatting import TabularFormatter, CompactNumberFormatter
from src.document_processing.summarization import DocumentSummarizer
from src.document_processing.market_aware import VolatilityAwareRetriever

# Sample data for demonstrations
SAMPLE_FINANCIAL_TEXT = """
Apple Inc. (AAPL) Financial Highlights - Q2 2023

Revenue: $94.84 billion, down 2.5% year-over-year
Earnings Per Share (EPS): $1.52, compared to $1.43 in the year-ago quarter
iPhone Revenue: $51.33 billion, down 1.5% year-over-year
Services Revenue: $20.91 billion, up 5.5% year-over-year
Gross Margin: 44.3%, up from 43.7% in the year-ago quarter
Operating Cash Flow: $28.6 billion
Share Repurchases: $23 billion
Dividend: Increased by 4% to $0.24 per share

Regional Performance:
- Americas: $38.9 billion, down 3.1%
- Europe: $23.9 billion, down 0.7%
- Greater China: $17.8 billion, down 3.0%
- Japan: $7.2 billion, down 4.8%
- Rest of Asia Pacific: $7.0 billion, down 1.4%

The company's board of directors has authorized an additional $90 billion for share repurchases, 
maintaining Apple's position as one of the largest dividend payers globally.

Apple's services business reached an all-time revenue record with double-digit growth in cloud services. 
The installed base of active devices reached an all-time high across all products and geographic segments.

For the third fiscal quarter, Apple expects revenues to be similar to the year-ago quarter, with services 
continuing to grow but facing macroeconomic uncertainties. Gross margin is expected to be between 44% and 44.5%.
"""

SAMPLE_HOLDINGS_DATA = {
    'holdings': [
        {'ticker': 'AAPL', 'name': 'Apple Inc.', 'weight': 0.0712, 'value': 18543000000, 'sector': 'Technology'},
        {'ticker': 'MSFT', 'name': 'Microsoft Corp', 'weight': 0.0625, 'value': 16275000000, 'sector': 'Technology'},
        {'ticker': 'AMZN', 'name': 'Amazon.com Inc', 'weight': 0.0351, 'value': 9126000000, 'sector': 'Consumer Discretionary'},
        {'ticker': 'NVDA', 'name': 'NVIDIA Corp', 'weight': 0.0341, 'value': 8866000000, 'sector': 'Technology'},
        {'ticker': 'GOOGL', 'name': 'Alphabet Inc Class A', 'weight': 0.0208, 'value': 5408000000, 'sector': 'Communication Services'},
        {'ticker': 'GOOG', 'name': 'Alphabet Inc Class C', 'weight': 0.0183, 'value': 4758000000, 'sector': 'Communication Services'},
        {'ticker': 'TSLA', 'name': 'Tesla Inc', 'weight': 0.0171, 'value': 4446000000, 'sector': 'Consumer Discretionary'},
        {'ticker': 'META', 'name': 'Meta Platforms Inc', 'weight': 0.0165, 'value': 4290000000, 'sector': 'Communication Services'},
        {'ticker': 'UNH', 'name': 'UnitedHealth Group Inc', 'weight': 0.0127, 'value': 3302000000, 'sector': 'Healthcare'},
        {'ticker': 'XOM', 'name': 'Exxon Mobil Corp', 'weight': 0.0122, 'value': 3172000000, 'sector': 'Energy'}
    ]
}

SAMPLE_PERFORMANCE_DATA = {
    'performance': {
        'returns': {
            '1M': 0.0235,
            '3M': 0.0712,
            '6M': 0.1247,
            'YTD': 0.1432,
            '1Y': 0.1837,
            '3Y': 0.4329,
            '5Y': 0.6712,
            '10Y': 1.1425,
            'Since Inception': 1.9873
        },
        'volatility': {
            '1Y': 0.1327,
            '3Y': 0.1556,
            '5Y': 0.1489,
            '10Y': 0.1375
        },
        'sharpe_ratio': {
            '1Y': 1.27,
            '3Y': 1.13,
            '5Y': 1.22,
            '10Y': 1.31
        },
        'max_drawdown': {
            '1Y': -0.1123,
            '3Y': -0.2456,
            '5Y': -0.2618,
            '10Y': -0.2618
        }
    }
}

SAMPLE_METRICS = {
    'fund_expense_ratio': 0.0045,
    'pe_ratio': 24.7,
    'dividend_yield': 0.0152,
    'assets_under_management': 456000000000,
    'beta': 1.04,
    'turnover_ratio': 0.08,
    'average_market_cap': 485200000000
}


def demo_tabular_formatter():
    """
    Demonstrate the TabularFormatter for financial data.
    """
    print("\n" + "="*80)
    print("TABULAR FORMATTER DEMONSTRATION")
    print("="*80)
    
    # Initialize the formatter
    formatter = TabularFormatter(max_width=80, precision=2)
    
    # Example 1: Format holdings data
    print("\nExample 1: Format Holdings Data")
    print("-" * 40)
    
    # Create a pandas DataFrame from the holdings data
    holdings_df = pd.DataFrame(SAMPLE_HOLDINGS_DATA['holdings'])
    
    # Format the holdings as a table
    holdings_table = formatter.format_dataframe(holdings_df)
    print(holdings_table)
    
    # Example 2: Format performance data
    print("\nExample 2: Format Performance Data")
    print("-" * 40)
    
    # Extract and pivot the performance data
    returns_df = pd.DataFrame(list(SAMPLE_PERFORMANCE_DATA['performance']['returns'].items()),
                              columns=['Period', 'Return'])
    returns_df['Type'] = 'Return'
    
    volatility_df = pd.DataFrame(list(SAMPLE_PERFORMANCE_DATA['performance']['volatility'].items()),
                                 columns=['Period', 'Return'])
    volatility_df['Type'] = 'Volatility'
    
    # Combine the data
    performance_df = pd.concat([returns_df, volatility_df])
    
    # Format the performance data as a table
    performance_table = formatter.format_dataframe(performance_df)
    print(performance_table)
    
    # Example 3: Format dictionary data
    print("\nExample 3: Format Dictionary Data")
    print("-" * 40)
    metrics_table = formatter.format_dict(SAMPLE_METRICS)
    print(metrics_table)


def demo_number_formatter():
    """
    Demonstrate the CompactNumberFormatter for financial figures.
    """
    print("\n" + "="*80)
    print("COMPACT NUMBER FORMATTER DEMONSTRATION")
    print("="*80)
    
    # Initialize the formatter
    formatter = CompactNumberFormatter(precision=2)
    
    # Example 1: Format individual financial values
    print("\nExample 1: Format Individual Values")
    print("-" * 40)
    print(f"Original: 1234567890, Formatted: {formatter.format_number(1234567890, 'currency')}")
    print(f"Original: 0.0712, Formatted: {formatter.format_number(0.0712, 'percentage')}")
    print(f"Original: 24.7, Formatted: {formatter.format_number(24.7, 'ratio')}")
    print(f"Original: 0.0045, Formatted: {formatter.format_number(0.0045, 'decimal')}")
    
    # Example 2: Format a set of financial metrics
    print("\nExample 2: Format Financial Metrics")
    print("-" * 40)
    
    # Define the type of each metric
    metric_types = {
        'fund_expense_ratio': 'percentage',
        'pe_ratio': 'ratio',
        'dividend_yield': 'percentage',
        'assets_under_management': 'currency',
        'beta': 'decimal',
        'turnover_ratio': 'percentage',
        'average_market_cap': 'currency'
    }
    
    formatted_metrics = formatter.format_financial_metrics(SAMPLE_METRICS, metric_types)
    
    for key, value in formatted_metrics.items():
        print(f"{key}: {value}")


def demo_document_summarizer():
    """
    Demonstrate the DocumentSummarizer for financial texts.
    """
    print("\n" + "="*80)
    print("DOCUMENT SUMMARIZER DEMONSTRATION")
    print("="*80)
    
    # Skip if ANTHROPIC_API_KEY is not set
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Skipping summarizer demo - ANTHROPIC_API_KEY not set")
        return
    
    # Initialize the summarizer
    try:
        summarizer = DocumentSummarizer()
        
        # Example 1: Generate a brief summary
        print("\nExample 1: Brief Summary")
        print("-" * 40)
        brief_summary = summarizer.summarize(
            SAMPLE_FINANCIAL_TEXT,
            target_length="brief",
            document_type="earnings_report"
        )
        print(brief_summary)
        
        # Example 2: Extract key points
        print("\nExample 2: Key Points")
        print("-" * 40)
        key_points = summarizer.extract_key_points(
            SAMPLE_FINANCIAL_TEXT,
            max_points=5,
            document_type="earnings_report"
        )
        for i, point in enumerate(key_points, 1):
            print(f"{i}. {point}")
        
        # Example 3: Structured summary
        print("\nExample 3: Structured Summary")
        print("-" * 40)
        structure = ["overview", "financial_results", "outlook"]
        structured_summary = summarizer.summarize_with_structure(
            SAMPLE_FINANCIAL_TEXT,
            structure=structure,
            document_type="earnings_report"
        )
        
        for section, content in structured_summary.items():
            print(f"\n{section.upper()}")
            print("-" * len(section))
            print(content)
            
    except Exception as e:
        print(f"Error in document summarizer demo: {str(e)}")


def demo_volatility_aware_retriever():
    """
    Demonstrate the VolatilityAwareRetriever.
    """
    print("\n" + "="*80)
    print("VOLATILITY-AWARE RETRIEVER DEMONSTRATION")
    print("="*80)
    
    # Initialize the retriever
    retriever = VolatilityAwareRetriever(
        base_document_count=3,
        max_document_count=8,
        volatility_threshold=1.5
    )
    
    # Create a mock base retriever for demonstration
    class MockRetriever:
        def search(self, query, k=None, **kwargs):
            # Simulate returning k documents
            return [f"Document {i+1} for query: {query}" for i in range(k)]
    
    mock_retriever = MockRetriever()
    
    # Example 1: Retrieve with default volatility
    print("\nExample 1: Retrieve with Current Market Volatility")
    print("-" * 40)
    
    # Get the current volatility context
    market_context = retriever.get_market_context()
    print(f"Current market context: {market_context['context_message']}")
    print(f"Volatility value: {market_context['volatility']:.2f}")
    print(f"Is high volatility: {market_context['is_high_volatility']}")
    
    # Perform retrieval
    results = retriever.retrieve(
        query="financial impact of rising interest rates",
        base_retriever=mock_retriever
    )
    
    print(f"\nRetrieved {len(results)} documents:")
    for doc in results:
        print(f"- {doc}")
    
    # Example 2: Demonstrate prompt adjustment
    print("\nExample 2: Volatility-Adjusted Prompt")
    print("-" * 40)
    
    original_prompt = "Analyze the current market conditions and provide investment recommendations."
    adjusted_prompt = retriever.adjust_prompt_for_volatility(original_prompt)
    
    print("Original Prompt:")
    print(original_prompt)
    print("\nAdjusted Prompt:")
    print(adjusted_prompt)
    
    # Example 3: Force high and low volatility scenarios
    print("\nExample 3: Simulated High vs. Low Volatility Scenarios")
    print("-" * 40)
    
    # Create retrievers with forced volatility scenarios
    class LowVolatilityRetriever(VolatilityAwareRetriever):
        def _calculate_sample_volatility(self, window_days):
            return 1.0  # Always low
            
    class HighVolatilityRetriever(VolatilityAwareRetriever):
        def _calculate_sample_volatility(self, window_days):
            return 2.5  # Always high
    
    low_vol_retriever = LowVolatilityRetriever(base_document_count=3, max_document_count=8)
    high_vol_retriever = HighVolatilityRetriever(base_document_count=3, max_document_count=8)
    
    # Compare retrieval counts
    low_vol_results = low_vol_retriever.retrieve(
        query="market impact of inflation",
        base_retriever=mock_retriever
    )
    
    high_vol_results = high_vol_retriever.retrieve(
        query="market impact of inflation",
        base_retriever=mock_retriever
    )
    
    print(f"Low volatility scenario: Retrieved {len(low_vol_results)} documents")
    print(f"High volatility scenario: Retrieved {len(high_vol_results)} documents")


if __name__ == "__main__":
    # Run all demonstrations
    demo_tabular_formatter()
    demo_number_formatter()
    demo_document_summarizer()
    demo_volatility_aware_retriever()
    
    print("\nAll demonstrations completed!") 