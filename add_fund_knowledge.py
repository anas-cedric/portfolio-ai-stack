"""
Helper module to add ETF knowledge to the Pinecone knowledge base.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def add_knowledge_to_pinecone(
    id: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Add knowledge item to Pinecone index.
    
    Args:
        id: Unique ID for the knowledge item
        content: Text content of the knowledge item
        metadata: Optional metadata for the knowledge item
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from src.knowledge.knowledge_base import KnowledgeBase
        
        # Initialize the knowledge base
        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        pinecone_environment = os.getenv("PINECONE_ENVIRONMENT")
        pinecone_index_name = os.getenv("PINECONE_INDEX_NAME")
        
        if not pinecone_api_key or not pinecone_environment or not pinecone_index_name:
            logger.error("Missing Pinecone environment variables")
            return False
        
        knowledge_base = KnowledgeBase(
            api_key=pinecone_api_key,
            environment=pinecone_environment,
            index_name=pinecone_index_name
        )
        
        # Add the knowledge item
        metadata = metadata or {}
        metadata["source"] = "etf_data_collector"
        metadata["type"] = "etf"
        
        knowledge_base.add_knowledge(
            id=id,
            content=content,
            metadata=metadata
        )
        
        logger.info(f"Added knowledge item: {id}")
        return True
    
    except Exception as e:
        logger.error(f"Error adding knowledge item: {e}")
        return False


if __name__ == "__main__":
    # Test functionality
    test_id = "test_etf_001"
    test_content = "This is a test ETF knowledge item."
    test_metadata = {
        "ticker": "TEST",
        "name": "Test ETF",
        "asset_class": "Equity",
        "provider": "Test Provider"
    }
    
    success = add_knowledge_to_pinecone(
        id=test_id,
        content=test_content,
        metadata=test_metadata
    )
    
    if success:
        print("Test successful!")
    else:
        print("Test failed.") 