#!/usr/bin/env python3
"""
Setup script for initializing preset financial data.

This script:
1. Creates the necessary directory structure
2. Generates and saves preset financial data
3. Uploads the data to the vector database
4. Runs a test query to verify everything works

Usage:
  python scripts/setup_preset_data.py
"""

import os
import sys
import argparse
import logging
from typing import Dict, List, Any, Optional

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.preset_financial_data import PresetFinancialData
from src.pipelines.preset_data_integration import PresetDataIntegration
from src.knowledge.vector_store import PineconeManager
from src.rag.rag_system import RAGSystem

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_directory_structure():
    """Set up the directory structure for preset data."""
    dirs = [
        "data",
        "data/preset",
        "data/cache",
        "data/vectors"
    ]
    
    for directory in dirs:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")


def generate_preset_data():
    """Generate and save preset financial data."""
    preset_data = PresetFinancialData()
    preset_data.save_preset_data("data/preset/financial_data.json")
    logger.info(f"Generated and saved preset data with {len(preset_data.preset_data)} documents")
    return preset_data


def load_data_to_vector_db(
    categories: Optional[List[str]] = None,
    namespace: str = "financial_knowledge",
    clear_existing: bool = False
):
    """Load preset data to vector database."""
    # Initialize vector database
    vector_db = PineconeManager()
    
    # Clear existing data if requested
    if clear_existing:
        logger.info(f"Clearing existing data in namespace: {namespace}")
        vector_db.delete_namespace(namespace)
    
    # Initialize preset data integration
    integration = PresetDataIntegration(vector_db=vector_db, namespace=namespace)
    
    # Load data
    categories = categories or ["fund_knowledge", "investment_principles"]
    stats = integration.load_data_to_vector_db(categories=categories)
    
    logger.info(f"Loaded {stats['vectors_uploaded']}/{stats['total_documents']} documents to vector database")
    logger.info(f"Processed {stats['batches_processed']} batches with {stats['errors']} errors")
    
    return stats


def test_rag_system():
    """Test the RAG system with preset data."""
    # Initialize RAG system
    rag = RAGSystem(embedding_model="placeholder", test_mode=True)
    
    # Test query
    test_query = "What is the S&P 500 and how can I invest in it?"
    
    logger.info(f"Testing RAG system with query: '{test_query}'")
    
    result = rag.process_query(query=test_query, include_details=True)
    
    logger.info(f"Response: {result['response'][:200]}...")
    logger.info(f"Confidence: {result['confidence']}")
    logger.info(f"Sources: {result['sources']}")
    
    if "details" in result:
        logger.info(f"Query type: {result['details'].get('query_type')}")
        logger.info(f"Retrieved {len(result['details'].get('contexts', []))} contexts")
    
    return result


def main():
    """Run the preset data setup."""
    parser = argparse.ArgumentParser(description="Setup preset financial data")
    parser.add_argument("--clear", action="store_true", help="Clear existing data")
    parser.add_argument("--namespace", default="financial_knowledge", help="Vector DB namespace")
    parser.add_argument("--categories", nargs="+", help="Categories to load")
    parser.add_argument("--skip-test", action="store_true", help="Skip RAG system test")
    
    args = parser.parse_args()
    
    logger.info("Starting preset data setup...")
    
    # Setup directory structure
    setup_directory_structure()
    
    # Generate preset data
    generate_preset_data()
    
    # Load data to vector database
    load_data_to_vector_db(
        categories=args.categories,
        namespace=args.namespace,
        clear_existing=args.clear
    )
    
    # Test RAG system
    if not args.skip_test:
        test_rag_system()
    
    logger.info("Preset data setup completed successfully!")


if __name__ == "__main__":
    main() 