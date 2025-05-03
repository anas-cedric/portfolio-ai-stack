"""
Utility functions for working with knowledge embeddings.
"""

import uuid
import numpy as np
from typing import Dict, List, Any, Optional

from src.knowledge.schema import KnowledgeItem


def generate_placeholder_embedding(dimension: int = 1024) -> np.ndarray:
    """
    Generate a placeholder random embedding for testing purposes.
    
    In production, this would be replaced with actual embeddings from Llama Text Embed v2
    or another embedding model.
    
    Args:
        dimension: Vector dimension (default is 1024 to match our Pinecone index)
        
    Returns:
        A normalized random vector
    """
    # Create a random vector
    vector = np.random.randn(dimension)
    # Normalize it to unit length for cosine similarity
    vector = vector / np.linalg.norm(vector)
    return vector


def generate_unique_id(prefix: str = "know") -> str:
    """
    Generate a unique ID for knowledge items.
    
    Args:
        prefix: Optional prefix for the ID
        
    Returns:
        Unique ID string
    """
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def knowledge_to_pinecone_format(
    knowledge_item: KnowledgeItem,
    embedding: Optional[np.ndarray] = None
) -> Dict[str, Any]:
    """
    Convert a knowledge item to the format expected by Pinecone.
    
    Args:
        knowledge_item: The knowledge item to convert
        embedding: Optional embedding vector (if None, a placeholder is generated)
        
    Returns:
        Dictionary with id, metadata, and vector
    """
    if embedding is None:
        embedding = generate_placeholder_embedding()
    
    return {
        "id": knowledge_item.id,
        "metadata": knowledge_item.to_metadata(),
        "vector": embedding
    }


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split a large text into smaller chunks for embedding.
    
    Args:
        text: The text to split
        chunk_size: Maximum characters per chunk
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    while start < len(text):
        # Find a good break point (end of sentence or paragraph)
        end = min(start + chunk_size, len(text))
        if end < len(text):
            # Try to find sentence boundaries
            for delim in ['\n\n', '\n', '. ', ', ']:
                last_delim = text[start:end].rfind(delim)
                if last_delim != -1:
                    end = start + last_delim + len(delim)
                    break
        
        chunks.append(text[start:end])
        start = end - overlap if end - overlap > start else end
    
    return chunks 