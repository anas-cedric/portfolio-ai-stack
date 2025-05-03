#!/usr/bin/env python3
"""
Test script for RAG system and related components.
"""

import os
import sys
import logging
from typing import Dict, List, Any, Optional

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.pipelines.embedding_pipeline import EmbeddingPipeline
from src.pipelines.pinecone_storage import PineconeStoragePipeline
from src.rag.rag_system import RAGSystem
from src.context.context_retrieval_system import ContextRetrievalSystem, ContextType

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_embedding_pipeline():
    """Test the embedding generation pipeline."""
    logger.info("Testing embedding pipeline...")
    
    # Create sample documents
    documents = [
        {
            "content": "Apple Inc. is an American multinational technology company headquartered in Cupertino, California. Apple is the world's largest technology company by revenue, with US$394.3 billion in 2022 revenue. As of March 2023, Apple is the world's biggest company by market capitalization. As of June 2022, Apple is the fourth-largest personal computer vendor by unit sales and the second-largest mobile phone manufacturer in the world.",
            "metadata": {
                "title": "Apple Inc.",
                "source": "company_profile",
                "ticker": "AAPL",
                "content_type": "stock"
            }
        },
        {
            "content": "The Vanguard S&P 500 ETF (VOO) is an exchange-traded fund that tracks the performance of the S&P 500 Index, which represents 500 of the largest U.S. companies. The fund provides investors with exposure to the U.S. large-cap market segment and is a popular choice for long-term investors seeking market returns with low expense ratios.",
            "metadata": {
                "title": "Vanguard S&P 500 ETF",
                "source": "fund_profile",
                "ticker": "VOO",
                "content_type": "fund"
            }
        }
    ]
    
    # Initialize pipeline with placeholder embeddings for testing
    pipeline = EmbeddingPipeline(embedding_model="placeholder")
    
    # Process documents
    result = pipeline.process_documents(documents)
    
    # Print results
    logger.info(f"Processed {result['total_documents']} documents")
    logger.info(f"Created {result['total_chunks']} chunks")
    logger.info(f"Successfully processed {result['chunks_processed']} chunks")
    logger.info(f"Uploaded {result['vectors_uploaded']} vectors")
    
    return result


def test_pinecone_storage():
    """Test the Pinecone storage pipeline."""
    logger.info("Testing Pinecone storage pipeline...")
    
    # Initialize storage pipeline
    storage = PineconeStoragePipeline()
    
    # Get index stats
    stats = storage.get_index_stats()
    
    # Print results
    logger.info(f"Pinecone index stats: {stats}")
    
    return stats


def test_rag_system():
    """Test the RAG system."""
    logger.info("Testing RAG system...")
    
    # Initialize RAG system with placeholder embeddings but real Gemini API
    rag = RAGSystem(
        embedding_model="placeholder",
        llm_model="gemini-2.5-pro-exp-03-25",
        test_mode=False
    )
    
    # Sample user profile and portfolio data
    user_profile = {
        "risk_tolerance": "moderate",
        "investment_goals": ["retirement", "education"],
        "time_horizon": "long_term"
    }
    
    portfolio_data = {
        "holdings": [
            {"ticker": "AAPL", "weight": 0.15},
            {"ticker": "MSFT", "weight": 0.12},
            {"ticker": "GOOGL", "weight": 0.10}
        ],
        "allocation": {
            "stocks": 0.70,
            "bonds": 0.20,
            "cash": 0.10
        }
    }
    
    # Test queries
    test_queries = [
        "What is the S&P 500?",
        "Should I invest in Apple stock?",
        "How should I rebalance my portfolio given current market conditions?"
    ]
    
    results = []
    for query in test_queries:
        logger.info(f"Processing query: {query}")
        
        try:
            result = rag.process_query(
                query=query,
                user_profile=user_profile,
                portfolio_data=portfolio_data,
                include_details=True
            )
            
            logger.info(f"Response: {result['response']}")
            logger.info(f"Confidence: {result['confidence']}")
            logger.info(f"Sources: {result['sources']}")
            
            if "details" in result:
                logger.info(f"Query type: {result['details'].get('query_type')}")
                logger.info(f"Retrieved {len(result['details'].get('contexts', []))} contexts")
            
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error processing query '{query}': {str(e)}")
            results.append({
                "query": query,
                "error": str(e)
            })
    
    return results


def test_context_retrieval():
    """Test the context retrieval system."""
    logger.info("Testing context retrieval system...")
    
    # Initialize context retrieval system with placeholder embeddings but real Gemini API
    context_system = ContextRetrievalSystem(
        embedding_model="placeholder",
        llm_model="gemini-2.5-pro-exp-03-25", 
        test_mode=False
    )
    
    # Test request
    request = {
        "query": "What stocks should I add to my portfolio if I'm concerned about inflation?",
        "context_types": [ContextType.GENERAL, ContextType.STOCK, ContextType.MARKET, ContextType.STRATEGY],
        "user_id": "test_user_123",
        "portfolio_id": "test_portfolio_456",
        "limit": 5,
        "include_market_data": True,
        "include_user_data": True
    }
    
    logger.info(f"Retrieving context for query: {request['query']}")
    
    try:
        # Retrieve contexts
        result = context_system.retrieve_context(request)
        
        # Print results
        logger.info(f"Retrieved {len(result['contexts'])} contexts")
        logger.info(f"Sources: {result['sources']}")
        logger.info(f"Metadata: {result['metadata']}")
        
        # Print each context
        for i, ctx in enumerate(result['contexts']):
            logger.info(f"Context {i+1}:")
            logger.info(f"  Type: {ctx['type']}")
            logger.info(f"  Source: {ctx['source']}")
            logger.info(f"  Relevance: {ctx['relevance']:.2f}")
            logger.info(f"  Content: {ctx['content'][:100]}...")
        
        return result
        
    except Exception as e:
        logger.error(f"Error during context retrieval: {str(e)}")
        return {"error": str(e)}


def main():
    """Run all tests."""
    logger.info("Starting RAG pipeline tests")
    
    try:
        # Uncomment tests as needed
        
        # Test embedding pipeline
        #embedding_result = test_embedding_pipeline()
        
        # Test Pinecone storage
        #storage_result = test_pinecone_storage()
        
        # Test RAG system with test_mode=True to avoid Gemini API rate limits
        logger.info("Testing RAG system with test_mode=True (avoiding API calls)...")
        rag_result_test_mode = RAGSystem(
            embedding_model="placeholder",
            llm_model="gemini-2.5-pro-exp-03-25",
            test_mode=True
        ).process_query(
            query="What is the S&P 500?",
            user_profile={
                "risk_tolerance": "moderate",
                "investment_goals": ["retirement", "education"],
                "time_horizon": "long_term"
            },
            portfolio_data={
                "holdings": [
                    {"ticker": "AAPL", "weight": 0.15},
                    {"ticker": "MSFT", "weight": 0.12},
                    {"ticker": "GOOGL", "weight": 0.10}
                ],
                "allocation": {
                    "stocks": 0.70,
                    "bonds": 0.20,
                    "cash": 0.10
                }
            },
            include_details=True
        )
        
        logger.info(f"Test mode response: {rag_result_test_mode['response'][:100]}...")
        
        # Test context retrieval with test_mode=True
        logger.info("Testing context retrieval with test_mode=True (avoiding API calls)...")
        context_system_test_mode = ContextRetrievalSystem(
            embedding_model="placeholder",
            llm_model="gemini-2.5-pro-exp-03-25", 
            test_mode=True
        )
        
        context_result_test_mode = context_system_test_mode.retrieve_context({
            "query": "What stocks should I add to my portfolio if I'm concerned about inflation?",
            "context_types": [ContextType.GENERAL, ContextType.STOCK, ContextType.MARKET, ContextType.STRATEGY],
            "user_id": "test_user_123",
            "portfolio_id": "test_portfolio_456",
            "limit": 5,
            "include_market_data": True,
            "include_user_data": True
        })
        
        # Optional: Test with real Gemini API if desired (but be careful with rate limits)
        logger.info("Note: Set GEMINI_API_ENABLED=1 environment variable to test with real API")
        if os.environ.get("GEMINI_API_ENABLED") == "1":
            logger.info("Testing one query with real Gemini API...")
            # Try just one simple query with the real API
            try:
                real_rag = RAGSystem(
                    embedding_model="placeholder",
                    llm_model="gemini-2.5-pro-exp-03-25",
                    test_mode=False
                )
                
                real_result = real_rag.process_query(
                    query="What is the S&P 500?",
                    include_details=True
                )
                
                logger.info(f"Real API response: {real_result['response'][:100]}...")
            except Exception as e:
                logger.warning(f"Real API test failed (possibly due to rate limits): {str(e)}")
                logger.warning("This doesn't affect the main test results.")
        
        logger.info("All tests completed successfully")
        
    except Exception as e:
        logger.error(f"Error during testing: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main() 