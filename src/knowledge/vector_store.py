"""
Vector database integration using Pinecone for storing and retrieving fund knowledge embeddings.
"""

import os
import json
import numpy as np
from typing import Dict, List, Optional, Any, Union
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class PineconeManager:
    """
    Manager class for Pinecone vector database operations.
    
    Handles storing and retrieving embeddings for:
    - Fund knowledge
    - Investment principles and strategies
    - Regulatory and tax rule information
    - Historical market patterns and correlations
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        environment: Optional[str] = None,
        index_name: Optional[str] = None
    ):
        """
        Initialize the Pinecone manager.
        
        Args:
            api_key: Optional Pinecone API key (defaults to PINECONE_API_KEY env var)
            environment: Optional Pinecone environment (defaults to PINECONE_ENVIRONMENT env var)
            index_name: Optional Pinecone index name (defaults to PINECONE_INDEX_NAME env var)
        """
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        self.environment = environment or os.getenv("PINECONE_ENVIRONMENT")
        self.index_name = index_name or os.getenv("PINECONE_INDEX_NAME")
        
        if not all([self.api_key, self.index_name]):
            raise ValueError(
                "Missing required Pinecone configuration. "
                "Please set PINECONE_API_KEY and PINECONE_INDEX_NAME "
                "environment variables or provide them as arguments."
            )
        
        try:
            # Import Pinecone using the new API format
            from pinecone import Pinecone
            
            # Initialize the Pinecone client
            pc = Pinecone(api_key=self.api_key)
            
            # Connect to the index
            try:
                self.index = pc.Index(self.index_name)
                logger.info(f"Connected to Pinecone index: {self.index_name}")
            except Exception as e:
                logger.error(f"Failed to connect to Pinecone index: {str(e)}")
                self.index = None
                
        except Exception as e:
            logger.error(f"Failed to connect to Pinecone: {str(e)}")
            # Fallback to in-memory index
            self.index = None
            logger.warning("Using in-memory index as fallback")
    
    def upsert_vectors(
        self, 
        vectors: List[np.ndarray], 
        ids: List[str], 
        metadata: List[Dict[str, Any]]
    ) -> bool:
        """
        Upload vector embeddings to Pinecone.
        
        Args:
            vectors: List of vector embeddings as numpy arrays
            ids: List of unique IDs for each vector
            metadata: List of metadata dictionaries for each vector
            
        Returns:
            bool: Success status
        """
        if not self.index:
            print("Warning: Pinecone index not available. Skipping upsert.")
            return False
            
        if len(vectors) != len(ids) or len(vectors) != len(metadata):
            raise ValueError("Vectors, IDs, and metadata lists must be the same length")
        
        # Convert to the format expected by the new Pinecone API
        vector_objects = [
            {
                "id": ids[i],
                "values": vectors[i].tolist() if isinstance(vectors[i], np.ndarray) else vectors[i],
                "metadata": metadata[i]
            }
            for i in range(len(vectors))
        ]
        
        # Batch upsert to Pinecone using the new API format
        self.index.upsert(vectors=vector_objects)
        return True
    
    def query(
        self, 
        query_vector: np.ndarray, 
        top_k: int = 5, 
        filter: Optional[Dict[str, Any]] = None,
        namespace: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Query Pinecone for similar vectors.
        
        Args:
            query_vector: The query vector embedding
            top_k: Number of results to return
            filter: Optional metadata filters
            namespace: Optional namespace
            
        Returns:
            List of matches with scores and metadata
        """
        if not self.index:
            print("Warning: Pinecone index not available. Returning empty results.")
            return []
            
        # Convert numpy array to list for serialization
        if isinstance(query_vector, np.ndarray):
            query_vector = query_vector.tolist()
        
        # Query the index using the new API format
        results = self.index.query(
            namespace=namespace,
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
            filter=filter
        )
        
        # Format results - the new API returns a Response object with matches
        return results.matches
    
    def delete_vectors(self, ids: List[str], namespace: str = "") -> bool:
        """
        Delete vectors from the index.
        
        Args:
            ids: List of vector IDs to delete
            namespace: Optional namespace
            
        Returns:
            bool: Success status
        """
        if not self.index:
            print("Warning: Pinecone index not available. Skipping delete.")
            return False
            
        self.index.delete(ids=ids, namespace=namespace)
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the Pinecone index.
        
        Returns:
            Dict with index statistics
        """
        if not self.index:
            print("Warning: Pinecone index not available. Returning empty stats.")
            return {}
            
        return self.index.describe_index_stats()
    
    def close(self) -> None:
        """Close the Pinecone connection."""
        # No explicit close method in Pinecone client
        pass 