"""
Example script demonstrating how to use the Pinecone knowledge management system.
"""

import numpy as np
from dotenv import load_dotenv
import os

from src.knowledge import (
    PineconeManager,
    KnowledgeCategory,
    FundKnowledge,
    InvestmentPrinciple,
    RegulatoryTaxInfo,
    MarketPattern,
    generate_unique_id,
    get_embedding_client
)

load_dotenv()

def main():
    """Run example of Pinecone knowledge management."""
    print("Initializing Pinecone knowledge management system...")
    
    # Debug API key
    api_key = os.getenv("PINECONE_API_KEY")
    print(f"Using Pinecone API key: {api_key[:5]}...{api_key[-5:]} (masked for security)")
    print(f"Pinecone Environment: {os.getenv('PINECONE_ENVIRONMENT')}")
    
    # Also debug Voyage API key
    voyage_api_key = os.getenv("VOYAGE_API_KEY")
    print(f"Using Voyage API key: {voyage_api_key[:5]}...{voyage_api_key[-5:]} (masked for security)")
    
    # Initialize Pinecone manager
    pinecone_mgr = PineconeManager()
    
    # Initialize embedding client - now using Voyage!
    print("\nInitializing Voyage embedding client...")
    embedding_client = get_embedding_client("voyage")
    
    # Create example knowledge items
    
    # Fund knowledge example
    fund_knowledge = FundKnowledge(
        id=generate_unique_id("fund"),
        title="Vanguard Total Stock Market ETF (VTI)",
        content=(
            "The Vanguard Total Stock Market ETF (VTI) provides investors with exposure to the entire U.S. equity market, "
            "including small-, mid-, and large-cap growth and value stocks. The fund's goal is to track the performance of "
            "the CRSP US Total Market Index. It has a very low expense ratio of 0.03% and is highly liquid."
        ),
        category=KnowledgeCategory.FUND_KNOWLEDGE,
        source="Vanguard",
        tags=["ETF", "US Equity", "Total Market", "Low Cost"],
        fund_ticker="VTI",
        fund_provider="Vanguard",
        fund_type="Equity ETF"
    )
    
    # Investment principle example
    investment_principle = InvestmentPrinciple(
        id=generate_unique_id("prin"),
        title="Modern Portfolio Theory: Diversification",
        content=(
            "Diversification is a key principle of Modern Portfolio Theory (MPT). By investing in a variety of asset "
            "classes with different correlation patterns, investors can reduce portfolio volatility without necessarily "
            "sacrificing returns. The goal is to create an 'efficient portfolio' that maximizes returns for a given level of risk."
        ),
        category=KnowledgeCategory.INVESTMENT_PRINCIPLES,
        source="Academic Finance Literature",
        tags=["MPT", "Diversification", "Risk Management"],
        principle_type="Portfolio Construction",
        risk_level="All",
        time_horizon="Long-term"
    )
    
    # Regulatory tax info example
    tax_info = RegulatoryTaxInfo(
        id=generate_unique_id("tax"),
        title="Tax-Loss Harvesting: Wash Sale Rule",
        content=(
            "The wash sale rule prohibits selling an investment for a loss and replacing it with the same or a 'substantially "
            "identical' investment 30 days before or after the sale. If a wash sale occurs, the IRS will disallow the loss "
            "deduction and add the disallowed loss to the cost basis of the replacement shares."
        ),
        category=KnowledgeCategory.REGULATORY_TAX,
        source="IRS Publication 550",
        tags=["Tax-Loss Harvesting", "Wash Sale", "IRS Rules"],
        jurisdiction="United States",
        applicable_year=2023,
        tax_entity_type="Individual"
    )
    
    # Market pattern example
    market_pattern = MarketPattern(
        id=generate_unique_id("pattern"),
        title="Equity-Bond Correlation During Market Stress",
        content=(
            "Historically, U.S. Treasury bonds have often exhibited negative correlation with equities during periods of "
            "market stress. This relationship has made Treasuries an effective hedge against equity drawdowns. However, "
            "this correlation is not constant and can vary depending on inflation expectations and central bank policies."
        ),
        category=KnowledgeCategory.MARKET_PATTERNS,
        source="Historical Market Analysis",
        tags=["Correlations", "Safe Haven", "Market Stress"],
        timeframe="1990-2023",
        asset_classes=["US Equities", "US Treasury Bonds"],
        market_conditions=["Market Stress", "Flight to Quality"]
    )
    
    # Generate embeddings for these items using our Voyage client
    print("Generating embeddings with Voyage AI...")
    try:
        fund_embedding = embedding_client.embed_text(fund_knowledge.content)
        print("✅ Successfully generated fund knowledge embedding")
        principle_embedding = embedding_client.embed_text(investment_principle.content)
        print("✅ Successfully generated investment principle embedding")
        
        # Store items in Pinecone
        print("\nStoring knowledge items in Pinecone...")
        
        pinecone_mgr.upsert_vectors(
            vectors=[
                fund_embedding,
                principle_embedding
            ],
            ids=[
                fund_knowledge.id,
                investment_principle.id
            ],
            metadata=[
                fund_knowledge.to_metadata(),
                investment_principle.to_metadata()
            ]
        )
        print("✅ Successfully stored items in Pinecone")
        
        # Query example - we'll create a query embedding from a user question
        user_query = "How can I build a diversified investment portfolio?"
        print(f"\nUser query: '{user_query}'")
        query_embedding = embedding_client.embed_text(user_query)
        print("✅ Successfully generated query embedding")
        
        # Query Pinecone
        print("Querying Pinecone for similar items...")
        results = pinecone_mgr.query(
            query_vector=query_embedding,
            top_k=3
        )
        
        # Display results
        print(f"\nFound {len(results)} similar items:")
        for i, match in enumerate(results):
            print(f"Match {i+1}:")
            print(f"  ID: {match.id}")
            print(f"  Score: {match.score}")
            print(f"  Title: {match.metadata.get('title', 'N/A')}")
            print(f"  Category: {match.metadata.get('category', 'N/A')}")
            print("")
        
        # Get statistics
        stats = pinecone_mgr.get_stats()
        print(f"Index Statistics:")
        print(f"  Total vectors: {stats.get('total_vector_count', 0)}")
        print(f"  Dimensions: {stats.get('dimension', 0)}")
        
        print("\nExample completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main() 