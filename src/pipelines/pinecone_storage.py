"""
Pinecone Storage Pipeline.

This module provides utilities for managing the storage of embeddings in Pinecone,
including batch uploading, index management, and data migration.
"""

import os
import logging
import json
import time
from typing import Dict, List, Any, Optional, Tuple, Union
from tqdm import tqdm
import numpy as np

from src.knowledge.vector_store import PineconeManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PineconeStoragePipeline:
    """
    Pipeline for managing storage of embeddings in Pinecone.
    
    This pipeline handles:
    1. Efficient batch uploading of vectors
    2. Index management and statistics
    3. Data migration and namespace management
    4. Error handling and recovery
    """
    
    def __init__(
        self,
        vector_db: Optional[PineconeManager] = None,
        batch_size: int = 100,
        max_retries: int = 3,
        retry_delay: int = 5
    ):
        """
        Initialize the Pinecone storage pipeline.
        
        Args:
            vector_db: Optional vector database instance (creates one if not provided)
            batch_size: Number of vectors to upload in a batch
            max_retries: Maximum number of retries for failed operations
            retry_delay: Delay between retries in seconds
        """
        self.vector_db = vector_db or PineconeManager()
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Validate connection to Pinecone
        self._validate_connection()
        
        logger.info(
            f"Initialized Pinecone storage pipeline with "
            f"batch_size={batch_size}, max_retries={max_retries}"
        )
    
    def _validate_connection(self) -> None:
        """Validate connection to Pinecone and log index statistics."""
        try:
            stats = self.vector_db.get_stats()
            if stats:
                total_vectors = stats.get("total_vector_count", 0)
                namespaces = stats.get("namespaces", {})
                
                logger.info(f"Connected to Pinecone index with {total_vectors} total vectors")
                if namespaces:
                    logger.info(f"Namespaces: {', '.join(namespaces.keys())}")
            else:
                logger.warning("Connected to Pinecone but couldn't retrieve index statistics")
        except Exception as e:
            logger.error(f"Failed to connect to Pinecone: {str(e)}")
            logger.warning("Continuing with limited functionality - vector storage will likely fail")
    
    def store_vectors(
        self,
        vectors: List[np.ndarray],
        ids: List[str],
        metadata: List[Dict[str, Any]],
        namespace: str = ""
    ) -> Dict[str, Any]:
        """
        Store vectors in Pinecone with efficient batching.
        
        Args:
            vectors: List of vector embeddings
            ids: List of unique IDs for each vector
            metadata: List of metadata dictionaries for each vector
            namespace: Optional namespace for the vectors
            
        Returns:
            Dictionary with storage statistics
        """
        start_time = time.time()
        
        if len(vectors) != len(ids) or len(vectors) != len(metadata):
            raise ValueError("Vectors, IDs, and metadata lists must be the same length")
        
        total_vectors = len(vectors)
        logger.info(f"Storing {total_vectors} vectors in Pinecone" + 
                   (f" namespace '{namespace}'" if namespace else ""))
        
        # Track statistics
        successful = 0
        failed = 0
        
        # Process in batches
        for i in range(0, total_vectors, self.batch_size):
            batch_end = min(i + self.batch_size, total_vectors)
            batch_vectors = vectors[i:batch_end]
            batch_ids = ids[i:batch_end]
            batch_metadata = metadata[i:batch_end]
            
            # Store with retry logic
            success = self._store_batch_with_retry(
                vectors=batch_vectors,
                ids=batch_ids,
                metadata=batch_metadata,
                namespace=namespace
            )
            
            if success:
                successful += len(batch_vectors)
            else:
                failed += len(batch_vectors)
            
            # Log progress
            if (i + self.batch_size) % 500 == 0 or batch_end == total_vectors:
                elapsed = time.time() - start_time
                progress = (batch_end / total_vectors) * 100
                logger.info(
                    f"Progress: {batch_end}/{total_vectors} vectors "
                    f"({progress:.1f}%) in {elapsed:.2f}s - "
                    f"{successful} successful, {failed} failed"
                )
        
        # Get final statistics
        elapsed = time.time() - start_time
        
        # Verify vector count in index
        try:
            stats = self.vector_db.get_stats()
            if namespace and stats and "namespaces" in stats:
                if namespace in stats["namespaces"]:
                    namespace_count = stats["namespaces"][namespace].get("vector_count", 0)
                    logger.info(f"Namespace '{namespace}' now contains {namespace_count} vectors")
            elif stats:
                total_count = stats.get("total_vector_count", 0)
                logger.info(f"Index now contains {total_count} total vectors")
        except Exception as e:
            logger.warning(f"Failed to get final vector count: {str(e)}")
        
        # Return statistics
        result = {
            "total_vectors": total_vectors,
            "successful": successful,
            "failed": failed,
            "processing_time_seconds": elapsed,
            "vectors_per_second": successful / elapsed if elapsed > 0 else 0
        }
        
        logger.info(f"Vector storage complete: {json.dumps(result, indent=2)}")
        return result
    
    def _store_batch_with_retry(
        self,
        vectors: List[np.ndarray],
        ids: List[str],
        metadata: List[Dict[str, Any]],
        namespace: str = ""
    ) -> bool:
        """
        Store a batch of vectors with retry logic.
        
        Args:
            vectors: Batch of vector embeddings
            ids: Batch of unique IDs
            metadata: Batch of metadata dictionaries
            namespace: Optional namespace
            
        Returns:
            True if successful, False otherwise
        """
        for attempt in range(self.max_retries):
            try:
                success = self.vector_db.upsert_vectors(
                    vectors=vectors,
                    ids=ids,
                    metadata=metadata
                )
                
                if success:
                    return True
                
                logger.warning(f"Vector storage failed (attempt {attempt+1}/{self.max_retries})")
                
            except Exception as e:
                logger.warning(f"Error storing vectors (attempt {attempt+1}/{self.max_retries}): {str(e)}")
            
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay)
        
        return False
    
    def delete_vectors(self, ids: List[str], namespace: str = "") -> Dict[str, Any]:
        """
        Delete vectors from Pinecone.
        
        Args:
            ids: List of vector IDs to delete
            namespace: Optional namespace
            
        Returns:
            Dictionary with deletion statistics
        """
        start_time = time.time()
        total_ids = len(ids)
        
        logger.info(f"Deleting {total_ids} vectors from Pinecone" + 
                   (f" namespace '{namespace}'" if namespace else ""))
        
        # Process in batches to avoid API limits
        successful = 0
        failed = 0
        
        for i in range(0, total_ids, self.batch_size):
            batch_ids = ids[i:min(i + self.batch_size, total_ids)]
            
            # Delete with retry logic
            success = self._delete_batch_with_retry(batch_ids, namespace)
            
            if success:
                successful += len(batch_ids)
            else:
                failed += len(batch_ids)
        
        elapsed = time.time() - start_time
        
        # Return statistics
        result = {
            "total_vectors": total_ids,
            "successful": successful,
            "failed": failed,
            "processing_time_seconds": elapsed
        }
        
        logger.info(f"Vector deletion complete: {json.dumps(result, indent=2)}")
        return result
    
    def _delete_batch_with_retry(self, ids: List[str], namespace: str = "") -> bool:
        """
        Delete a batch of vectors with retry logic.
        
        Args:
            ids: Batch of vector IDs to delete
            namespace: Optional namespace
            
        Returns:
            True if successful, False otherwise
        """
        for attempt in range(self.max_retries):
            try:
                success = self.vector_db.delete_vectors(ids=ids, namespace=namespace)
                
                if success:
                    return True
                
                logger.warning(f"Vector deletion failed (attempt {attempt+1}/{self.max_retries})")
                
            except Exception as e:
                logger.warning(f"Error deleting vectors (attempt {attempt+1}/{self.max_retries}): {str(e)}")
            
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay)
        
        return False
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the Pinecone index.
        
        Returns:
            Dictionary with index statistics
        """
        try:
            stats = self.vector_db.get_stats()
            if not stats:
                logger.warning("Failed to get index statistics")
                return {}
            
            # Add some formatted information for easier consumption
            total_vectors = stats.get("total_vector_count", 0)
            namespaces = stats.get("namespaces", {})
            
            formatted_stats = {
                "total_vectors": total_vectors,
                "namespace_count": len(namespaces),
                "namespaces": {}
            }
            
            # Process namespace information
            for ns_name, ns_data in namespaces.items():
                formatted_stats["namespaces"][ns_name] = {
                    "vector_count": ns_data.get("vector_count", 0)
                }
            
            return formatted_stats
            
        except Exception as e:
            logger.error(f"Error getting index stats: {str(e)}")
            return {} 