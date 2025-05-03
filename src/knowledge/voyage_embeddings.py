"""
Enhanced Voyage Finance embeddings client with improved error handling and batch processing.

This module provides a robust implementation of the Voyage finance-2 embedding model,
suitable for production use with financial documents.
"""

import os
import time
import json
import logging
import requests
import numpy as np
from typing import List, Dict, Any, Optional, Union
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class VoyageFinanceEmbeddings:
    """
    Production-ready client for Voyage AI's finance-2 embedding model.
    
    Features:
    - Robust error handling with retries
    - Efficient batch processing
    - Rate limiting support
    - Custom preprocessing for financial documents
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        model: str = "voyage-finance-2",
        max_retries: int = 3,
        retry_delay: float = 1.0,
        batch_size: int = 10
    ):
        """
        Initialize the Voyage Finance embeddings client.
        
        Args:
            api_key: API key for Voyage AI (defaults to VOYAGE_API_KEY env var)
            model: Model name to use (default is voyage-finance-2)
            max_retries: Maximum number of retries for failed API calls
            retry_delay: Delay between retries in seconds
            batch_size: Maximum batch size for embedding requests
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
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.batch_size = batch_size
        
        logger.info(f"Initialized Voyage Finance embeddings client with model: {model}")
    
    def embed_text(self, text: str, input_type: str = "document") -> np.ndarray:
        """
        Generate an embedding for a single text.
        
        Args:
            text: The text to embed
            input_type: Input type ('document' or 'query')
            
        Returns:
            The embedding as a numpy array
        """
        payload = {
            "model": self.model,
            "input": text,
            "input_type": input_type
        }
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.api_url, 
                    headers=self.headers, 
                    json=payload,
                    timeout=30  # Set a reasonable timeout
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Extract embedding from the response
                if "data" in data and len(data["data"]) > 0 and "embedding" in data["data"][0]:
                    embedding = np.array(data["data"][0]["embedding"])
                elif "embeddings" in data:
                    embedding = np.array(data["embeddings"][0])
                elif "embedding" in data:
                    embedding = np.array(data["embedding"])
                else:
                    raise KeyError("Could not find embeddings in API response")
                
                return embedding
                
            except (requests.RequestException, KeyError) as e:
                logger.warning(f"Embed attempt {attempt+1}/{self.max_retries} failed: {str(e)}")
                if attempt < self.max_retries - 1:
                    # Calculate backoff time with some jitter to avoid thundering herd
                    backoff = self.retry_delay * (2 ** attempt) * (0.9 + 0.2 * np.random.random())
                    logger.info(f"Retrying in {backoff:.2f} seconds...")
                    time.sleep(backoff)
                else:
                    logger.error(f"Failed to embed text after {self.max_retries} attempts")
                    raise
    
    def embed_batch(
        self, 
        texts: List[str], 
        input_type: str = "document"
    ) -> List[np.ndarray]:
        """
        Generate embeddings for a batch of texts.
        
        Handles automatic batching to respect API limits.
        
        Args:
            texts: The texts to embed
            input_type: Input type ('document' or 'query')
            
        Returns:
            A list of embeddings as numpy arrays
        """
        all_embeddings = []
        
        # Process in batches to avoid API limits
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i+self.batch_size]
            batch_size = len(batch)
            
            logger.info(f"Processing batch {i//self.batch_size + 1} with {batch_size} texts")
            
            payload = {
                "model": self.model,
                "input": batch,
                "input_type": input_type
            }
            
            for attempt in range(self.max_retries):
                try:
                    response = requests.post(
                        self.api_url, 
                        headers=self.headers, 
                        json=payload,
                        timeout=60  # Longer timeout for batch processing
                    )
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    # Extract embeddings from the response
                    if "data" in data:
                        batch_embeddings = [np.array(item["embedding"]) for item in data["data"]]
                    elif "embeddings" in data:
                        batch_embeddings = [np.array(emb) for emb in data["embeddings"]]
                    else:
                        raise KeyError("Could not find embeddings in API response")
                    
                    all_embeddings.extend(batch_embeddings)
                    
                    # Add a small delay between batches to avoid rate limiting
                    if i + self.batch_size < len(texts):
                        time.sleep(0.5)
                    
                    break  # Success, exit retry loop
                    
                except (requests.RequestException, KeyError) as e:
                    logger.warning(f"Batch embed attempt {attempt+1}/{self.max_retries} failed: {str(e)}")
                    if attempt < self.max_retries - 1:
                        # Calculate backoff time with some jitter
                        backoff = self.retry_delay * (2 ** attempt) * (0.9 + 0.2 * np.random.random())
                        logger.info(f"Retrying batch in {backoff:.2f} seconds...")
                        time.sleep(backoff)
                    else:
                        logger.error(f"Failed to embed batch after {self.max_retries} attempts")
                        raise
        
        return all_embeddings
    
    def preprocess_financial_document(self, text: str) -> str:
        """
        Preprocess a financial document for better embedding quality.
        
        This function:
        1. Handles common financial abbreviations
        2. Normalizes financial metrics notation
        3. Removes irrelevant boilerplate content
        
        Args:
            text: The raw document text
            
        Returns:
            Preprocessed text ready for embedding
        """
        # Remove irrelevant boilerplate content often found in financial documents
        # This is a simplified example - real implementation would be more comprehensive
        lines = text.split('\n')
        
        # Filter out common boilerplate lines
        filtered_lines = []
        for line in lines:
            # Skip empty lines and common footer/header content
            if not line.strip():
                continue
            if "confidential" in line.lower() and len(line) < 100:
                continue
            if "page" in line.lower() and "of" in line.lower() and len(line) < 20:
                continue
                
            filtered_lines.append(line)
        
        cleaned_text = '\n'.join(filtered_lines)
        
        # Normalize financial abbreviations and metrics
        replacements = {
            "EPS": "Earnings Per Share",
            "P/E": "Price to Earnings",
            "ROI": "Return on Investment",
            "ROE": "Return on Equity",
            "EBITDA": "Earnings Before Interest, Taxes, Depreciation, and Amortization"
            # Add more financial abbreviations as needed
        }
        
        for abbr, full in replacements.items():
            # Replace only standalone abbreviations with word boundaries
            cleaned_text = cleaned_text.replace(f" {abbr} ", f" {full} ")
        
        return cleaned_text 