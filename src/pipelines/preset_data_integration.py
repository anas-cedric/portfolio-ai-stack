"""
Preset Data Integration Module.

This module provides utilities for integrating preset financial data
with the RAG system, replacing the need for actual document processing
while maintaining compatibility with the existing interfaces.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple

from src.data.preset_financial_data import PresetFinancialData
from src.knowledge.vector_store import PineconeManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PresetDataIntegration:
    """
    Integrates preset financial data with the RAG system.
    
    This class provides methods to load preset data and populate
    the vector database with mock embeddings, simulating a full
    document processing pipeline.
    """
    
    def __init__(
        self,
        vector_db: Optional[PineconeManager] = None,
        data_path: Optional[str] = None,
        namespace: str = "financial_knowledge"
    ):
        """
        Initialize the preset data integration.
        
        Args:
            vector_db: Optional PineconeManager instance
            data_path: Optional path to preset data files
            namespace: Namespace to use in vector database
        """
        self.preset_data = PresetFinancialData(data_path=data_path)
        self.vector_db = vector_db or PineconeManager()
        self.namespace = namespace
        logger.info(f"Initialized preset data integration with {len(self.preset_data.preset_data)} documents")
        
    def load_data_to_vector_db(
        self,
        categories: Optional[List[str]] = None,
        batch_size: int = 100,
        dimension: int = 1024
    ) -> Dict[str, Any]:
        """
        Load preset data to vector database.
        
        Args:
            categories: Optional list of categories to load
            batch_size: Batch size for vector upload
            dimension: Dimension of embeddings
            
        Returns:
            Dictionary with operation statistics
        """
        # Get documents to load
        if categories:
            documents = []
            for category in categories:
                documents.extend(self.preset_data.get_documents(category=category))
        else:
            documents = self.preset_data.preset_data
            
        logger.info(f"Loading {len(documents)} documents to vector database")
        
        # Prepare stats
        stats = {
            "total_documents": len(documents),
            "vectors_uploaded": 0,
            "batches_processed": 0,
            "errors": 0
        }
        
        # Process in batches
        batch_count = (len(documents) + batch_size - 1) // batch_size
        for i in range(batch_count):
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, len(documents))
            batch = documents[start_idx:end_idx]
            
            # Prepare batch vectors
            vectors = []
            for doc in batch:
                # Generate mock embedding for document content
                embedding = self.preset_data.get_mock_embedding(doc["content"], dim=dimension)
                
                # Prepare metadata
                metadata = doc.get("metadata", {})
                metadata["id"] = doc.get("id", f"doc_{hash(doc['content']) % (2**32)}")
                metadata["text"] = doc["content"][:1000]  # Store first 1000 chars for faster retrieval
                
                # Create vector entry
                vectors.append({
                    "id": metadata["id"],
                    "values": embedding,
                    "metadata": metadata
                })
            
            # Upload batch to vector database
            try:
                self.vector_db.add_vectors(vectors, namespace=self.namespace)
                stats["vectors_uploaded"] += len(vectors)
            except Exception as e:
                logger.error(f"Error uploading batch {i+1}/{batch_count}: {str(e)}")
                stats["errors"] += 1
                
            stats["batches_processed"] += 1
            
            # Log progress
            if (i + 1) % 5 == 0 or (i + 1) == batch_count:
                logger.info(f"Processed {i+1}/{batch_count} batches ({stats['vectors_uploaded']} vectors uploaded)")
                
        return stats
    
    def search_similar_documents(
        self,
        query: str,
        namespace: Optional[str] = None,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents using mock embeddings.
        
        Args:
            query: Query text
            namespace: Optional namespace (defaults to self.namespace)
            top_k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of similar documents with scores
        """
        # Generate mock embedding for query
        query_embedding = self.preset_data.get_mock_embedding(query)
        
        # Search vector database
        namespace = namespace or self.namespace
        results = self.vector_db.search_vectors(
            query_vector=query_embedding,
            namespace=namespace,
            top_k=top_k,
            filters=filters
        )
        
        return results
    
    def create_sample_data_structure(self) -> None:
        """
        Create directory structure and save sample data to file.
        
        This is useful for setting up a new development environment
        or for saving the preset data for later use.
        """
        # Create data directories
        os.makedirs("data", exist_ok=True)
        os.makedirs("data/preset", exist_ok=True)
        
        # Save preset data
        self.preset_data.save_preset_data("data/preset/financial_data.json")
        
        logger.info("Created sample data structure in data/preset/")


# Example usage
if __name__ == "__main__":
    # Initialize integration
    integration = PresetDataIntegration()
    
    # Create sample data structure
    integration.create_sample_data_structure()
    
    # Load fund knowledge documents to vector database
    stats = integration.load_data_to_vector_db(categories=["fund_knowledge"])
    print(f"Loaded {stats['vectors_uploaded']} vectors to vector database")
    
    # Test searching
    results = integration.search_similar_documents(
        query="What is the S&P 500 index?",
        top_k=3
    )
    
    print("\nSearch results:")
    for i, result in enumerate(results):
        print(f"{i+1}. {result['metadata'].get('title')} (Score: {result['score']:.4f})") 