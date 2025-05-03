"""
Embedding Generation Pipeline.

This module provides a pipeline for generating embeddings from documents
and preparing them for storage in vector databases.
"""

import os
import logging
import hashlib
import json
from typing import Dict, List, Any, Optional, Tuple, Union
import time
import numpy as np
from tqdm import tqdm

from src.knowledge.embedding import get_embedding_client, EmbeddingClient
from src.knowledge.vector_store import PineconeManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingPipeline:
    """
    Pipeline for generating and storing document embeddings.
    
    This pipeline handles:
    1. Processing documents into chunks suitable for embedding
    2. Generating embeddings using various embedding models
    3. Storing embeddings in vector databases with appropriate metadata
    4. Handling batch processing and retries for robustness
    """
    
    def __init__(
        self,
        embedding_model: str = "voyage",
        vector_db: Optional[PineconeManager] = None,
        chunk_size: int = 512,
        chunk_overlap: int = 100,
        batch_size: int = 10,
        max_retries: int = 3,
        retry_delay: int = 2
    ):
        """
        Initialize the embedding pipeline.
        
        Args:
            embedding_model: Model to use for generating embeddings ("voyage", "llama", etc.)
            vector_db: Optional vector database instance (creates one if not provided)
            chunk_size: The size of text chunks to embed
            chunk_overlap: The overlap between chunks
            batch_size: Number of items to process in a batch
            max_retries: Maximum number of retries for failed embedding generations
            retry_delay: Delay between retries in seconds
        """
        self.embedding_client = get_embedding_client(embedding_model)
        self.vector_db = vector_db or PineconeManager()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        logger.info(
            f"Initialized embedding pipeline with {embedding_model} model, "
            f"chunk_size={chunk_size}, chunk_overlap={chunk_overlap}, batch_size={batch_size}"
        )
    
    def process_documents(
        self,
        documents: List[Dict[str, Any]],
        namespace: str = ""
    ) -> Dict[str, Any]:
        """
        Process a list of documents through the embedding pipeline.
        
        Args:
            documents: List of document dictionaries with 'content' and 'metadata' fields
            namespace: Optional namespace for vector database
            
        Returns:
            Dictionary with processing statistics
        """
        start_time = time.time()
        logger.info(f"Processing {len(documents)} documents")
        
        # Chunk the documents
        chunks = []
        for doc in tqdm(documents, desc="Chunking documents"):
            doc_chunks = self._create_chunks(doc)
            chunks.extend(doc_chunks)
        
        logger.info(f"Created {len(chunks)} chunks from {len(documents)} documents")
        
        # Process chunks in batches
        total_chunks = len(chunks)
        total_processed = 0
        total_failed = 0
        
        # Lists to collect data for batch upload
        all_vectors = []
        all_ids = []
        all_metadata = []
        
        # Process in batches
        for i in range(0, total_chunks, self.batch_size):
            batch = chunks[i:i+self.batch_size]
            
            # Extract text and metadata
            texts = [item["text"] for item in batch]
            metadata_list = [item["metadata"] for item in batch]
            
            # Generate embeddings with retry logic
            vectors = []
            for j, text in enumerate(texts):
                embedding = self._generate_embedding_with_retry(text)
                if embedding is not None:
                    vector_id = self._generate_id(text, metadata_list[j])
                    
                    vectors.append(embedding)
                    all_vectors.append(embedding)
                    all_ids.append(vector_id)
                    all_metadata.append(metadata_list[j])
                    total_processed += 1
                else:
                    logger.warning(f"Failed to generate embedding for chunk after {self.max_retries} retries")
                    total_failed += 1
            
            # Provide progress update
            if (i + self.batch_size) % 50 == 0 or (i + self.batch_size) >= total_chunks:
                elapsed = time.time() - start_time
                logger.info(
                    f"Processed {i + len(batch)}/{total_chunks} chunks "
                    f"({total_processed} succeeded, {total_failed} failed) "
                    f"in {elapsed:.2f}s"
                )
        
        # Upload all embeddings to vector database
        if all_vectors:
            logger.info(f"Uploading {len(all_vectors)} vectors to vector database")
            success = self.vector_db.upsert_vectors(
                vectors=all_vectors,
                ids=all_ids,
                metadata=all_metadata
            )
            
            if success:
                logger.info(f"Successfully uploaded {len(all_vectors)} vectors")
            else:
                logger.error("Failed to upload vectors to vector database")
        
        # Compile statistics
        elapsed = time.time() - start_time
        stats = {
            "total_documents": len(documents),
            "total_chunks": total_chunks,
            "chunks_processed": total_processed,
            "chunks_failed": total_failed,
            "processing_time_seconds": elapsed,
            "vectors_uploaded": len(all_vectors)
        }
        
        logger.info(f"Embedding pipeline stats: {json.dumps(stats, indent=2)}")
        return stats
    
    def _create_chunks(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split a document into chunks suitable for embedding.
        
        Args:
            document: Document dictionary with 'content' and 'metadata' fields
            
        Returns:
            List of chunk dictionaries with 'text' and 'metadata' fields
        """
        content = document.get("content", "")
        metadata = document.get("metadata", {})
        
        if not content or not isinstance(content, str):
            logger.warning(f"Empty or invalid content in document: {metadata.get('source', 'unknown')}")
            return []
        
        # Split the text into chunks
        text_chunks = self._split_text(content, self.chunk_size, self.chunk_overlap)
        
        # Create chunk objects with metadata
        chunks = []
        for i, chunk_text in enumerate(text_chunks):
            # Create a copy of the metadata for each chunk
            chunk_metadata = metadata.copy()
            
            # Add chunk-specific metadata
            chunk_metadata["chunk_index"] = i
            chunk_metadata["chunk_count"] = len(text_chunks)
            chunk_metadata["content"] = chunk_text  # Include the chunk text in metadata
            
            chunks.append({
                "text": chunk_text,
                "metadata": chunk_metadata
            })
        
        return chunks
    
    def _split_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """
        Split text into chunks with overlap.
        
        Args:
            text: The text to split
            chunk_size: Maximum chunk size in characters
            overlap: Overlap between chunks in characters
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
            
        if len(text) <= chunk_size:
            return [text]
            
        chunks = []
        start = 0
        
        while start < len(text):
            # Get the chunk
            end = start + chunk_size
            if end > len(text):
                end = len(text)
                
            # Use sentence boundaries when possible
            if end < len(text) and text[end] not in ['.', '!', '?', '\n']:
                # Look for sentence boundary
                boundary = max(text.rfind('.', start, end), 
                               text.rfind('!', start, end),
                               text.rfind('?', start, end),
                               text.rfind('\n', start, end))
                
                if boundary != -1 and boundary > start + chunk_size // 2:
                    end = boundary + 1
            
            # Create the chunk
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
                
            # Move to next chunk with overlap
            start = end - overlap
            if start < 0:
                start = 0
                
        return chunks
    
    def _generate_embedding_with_retry(self, text: str) -> Optional[np.ndarray]:
        """
        Generate an embedding with retry logic.
        
        Args:
            text: The text to embed
            
        Returns:
            Embedding as numpy array or None if all retries fail
        """
        for attempt in range(self.max_retries):
            try:
                return self.embedding_client.embed_text(text)
            except Exception as e:
                logger.warning(f"Embedding generation failed (attempt {attempt+1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    
        return None
    
    def _generate_id(self, text: str, metadata: Dict[str, Any]) -> str:
        """
        Generate a deterministic ID for a text chunk.
        
        Args:
            text: The text chunk
            metadata: The chunk metadata
            
        Returns:
            A unique ID string
        """
        # Create a deterministic ID based on content and source
        source = metadata.get("source", "")
        chunk_index = metadata.get("chunk_index", 0)
        
        # Create a hash of the text and metadata
        hash_input = f"{source}:{chunk_index}:{text[:100]}"
        return hashlib.md5(hash_input.encode('utf-8')).hexdigest() 