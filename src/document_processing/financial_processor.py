"""
Financial document processor for batch processing and embedding.

This module handles:
1. Loading various financial document formats
2. Preprocessing documents for embedding
3. Chunking large documents into appropriate segments
4. Managing metadata extraction from documents
"""

import os
import re
import json
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Union, Tuple
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from src.knowledge.voyage_embeddings import VoyageFinanceEmbeddings
from src.knowledge.vector_store import PineconeManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinancialDocumentProcessor:
    """
    Processes financial documents for embedding and storage in the vector database.
    
    Features:
    - Multi-format document loading (txt, csv, json, excel)
    - Smart chunking of large documents
    - Metadata extraction and enrichment
    - Parallel processing for improved performance
    - Duplicate detection and handling
    """
    
    def __init__(
        self,
        embedding_client: Optional[VoyageFinanceEmbeddings] = None,
        vector_store: Optional[PineconeManager] = None,
        chunk_size: int = 1024,
        chunk_overlap: int = 128,
        max_workers: int = 5
    ):
        """
        Initialize the financial document processor.
        
        Args:
            embedding_client: The embedding client to use
            vector_store: The vector store to use
            chunk_size: Maximum chunk size in characters
            chunk_overlap: Overlap between chunks in characters
            max_workers: Maximum number of parallel workers
        """
        self.embedding_client = embedding_client or VoyageFinanceEmbeddings()
        self.vector_store = vector_store or PineconeManager()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_workers = max_workers
        
        logger.info(f"Initialized FinancialDocumentProcessor with chunk_size={chunk_size}")
    
    def process_directory(self, directory_path: str, recursive: bool = True) -> Dict[str, Any]:
        """
        Process all supported documents in a directory.
        
        Args:
            directory_path: Path to the directory containing documents
            recursive: Whether to search directories recursively
            
        Returns:
            Statistics about the processing run
        """
        path = Path(directory_path)
        
        if not path.exists() or not path.is_dir():
            raise ValueError(f"Directory {directory_path} does not exist or is not a directory")
        
        # Find all files with supported extensions
        supported_extensions = ['.txt', '.csv', '.json', '.xlsx', '.xls', '.md', '.pdf']
        
        if recursive:
            all_files = []
            for ext in supported_extensions:
                all_files.extend(list(path.glob(f"**/*{ext}")))
        else:
            all_files = []
            for ext in supported_extensions:
                all_files.extend(list(path.glob(f"*{ext}")))
        
        logger.info(f"Found {len(all_files)} documents to process in {directory_path}")
        
        # Process files in parallel
        stats = {
            "total_files": len(all_files),
            "successfully_processed": 0,
            "failed": 0,
            "chunks_created": 0,
            "total_tokens": 0,
            "failures": []
        }
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(self.process_file, str(file_path)): file_path 
                for file_path in all_files
            }
            
            # Process results as they complete
            for future in future_to_file:
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    stats["successfully_processed"] += 1
                    stats["chunks_created"] += result["chunks_created"]
                    stats["total_tokens"] += result["total_tokens"]
                    logger.info(f"Successfully processed {file_path.name}")
                except Exception as e:
                    stats["failed"] += 1
                    error_info = {
                        "file": str(file_path),
                        "error": str(e)
                    }
                    stats["failures"].append(error_info)
                    logger.error(f"Failed to process {file_path.name}: {str(e)}")
        
        logger.info(f"Processing complete. Success: {stats['successfully_processed']}, Failed: {stats['failed']}")
        return stats
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process a single file for embedding and storage.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            Statistics about the processing
        """
        path = Path(file_path)
        
        if not path.exists() or not path.is_file():
            raise ValueError(f"File {file_path} does not exist or is not a file")
        
        # Load and preprocess the document based on its type
        content, metadata = self._load_document(file_path)
        
        # Preprocess the content
        preprocessed_content = self.embedding_client.preprocess_financial_document(content)
        
        # Chunk the content if necessary
        chunks = self._chunk_text(preprocessed_content)
        
        # Generate unique IDs for the chunks
        base_id = self._generate_document_id(file_path, metadata)
        chunk_ids = [f"{base_id}_chunk_{i}" for i in range(len(chunks))]
        
        # Create metadata for each chunk
        chunk_metadata = []
        for i, chunk in enumerate(chunks):
            chunk_meta = metadata.copy()
            chunk_meta.update({
                "chunk_id": i,
                "total_chunks": len(chunks),
                "content": chunk,
                "source_file": file_path,
                "document_id": base_id
            })
            chunk_metadata.append(chunk_meta)
        
        # Generate embeddings for the chunks
        embeddings = self.embedding_client.embed_batch(chunks)
        
        # Store in vector database
        self.vector_store.upsert_vectors(
            vectors=embeddings,
            ids=chunk_ids,
            metadata=chunk_metadata
        )
        
        # Calculate approximate token count (rough estimate)
        total_tokens = sum(len(chunk.split()) * 1.3 for chunk in chunks)
        
        return {
            "file_path": file_path,
            "chunks_created": len(chunks),
            "total_tokens": int(total_tokens),
            "document_id": base_id
        }
    
    def _load_document(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """
        Load a document and extract its content and metadata.
        
        Args:
            file_path: Path to the document
            
        Returns:
            Tuple of (content, metadata)
        """
        path = Path(file_path)
        extension = path.suffix.lower()
        
        # Extract basic metadata
        metadata = {
            "filename": path.name,
            "file_type": extension,
            "file_size_bytes": path.stat().st_size,
            "last_modified": path.stat().st_mtime
        }
        
        # Load content based on file type
        if extension == '.txt' or extension == '.md':
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
        elif extension == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Handle different JSON formats
            if isinstance(data, dict):
                # Extract content from common fields
                content_fields = ['content', 'text', 'description', 'body']
                content = ""
                for field in content_fields:
                    if field in data:
                        content += str(data[field]) + "\n\n"
                
                # Use all fields if no content was found
                if not content:
                    content = json.dumps(data, indent=2)
                
                # Extract additional metadata
                metadata_fields = ['title', 'author', 'date', 'category', 'tags']
                for field in metadata_fields:
                    if field in data:
                        metadata[field] = data[field]
            else:
                # For array data, convert to a formatted string
                content = json.dumps(data, indent=2)
        
        elif extension == '.csv':
            # For CSV files, load as dataframe and convert to formatted string
            df = pd.read_csv(file_path)
            metadata['num_rows'] = len(df)
            metadata['num_columns'] = len(df.columns)
            metadata['columns'] = list(df.columns)
            
            # Generate a readable representation of the CSV data
            content = f"CSV Data with {metadata['num_rows']} rows and {metadata['num_columns']} columns.\n\n"
            content += f"Columns: {', '.join(metadata['columns'])}\n\n"
            
            # Add sample data (first few rows)
            sample_rows = min(5, len(df))
            content += df.head(sample_rows).to_string(index=False) + "\n\n"
            
            # Add summary statistics for numerical columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if not numeric_cols.empty:
                content += "Summary statistics for numerical columns:\n"
                content += df[numeric_cols].describe().to_string() + "\n"
        
        elif extension in ['.xlsx', '.xls']:
            # For Excel files, load as dataframe and convert to formatted string
            xls = pd.ExcelFile(file_path)
            sheet_names = xls.sheet_names
            metadata['sheet_names'] = sheet_names
            
            content = f"Excel file with {len(sheet_names)} sheets: {', '.join(sheet_names)}\n\n"
            
            # Process each sheet
            for sheet in sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet)
                content += f"Sheet: {sheet}\n"
                content += f"Dimensions: {len(df)} rows × {len(df.columns)} columns\n"
                content += f"Columns: {', '.join(df.columns)}\n\n"
                
                # Add sample data
                sample_rows = min(5, len(df))
                if sample_rows > 0:
                    content += df.head(sample_rows).to_string(index=False) + "\n\n"
        
        else:
            # For unsupported file types
            content = f"Unsupported file type: {extension}"
            metadata['error'] = "Unsupported file type"
        
        # Try to extract financial entities from the content
        financial_entities = self._extract_financial_entities(content)
        if financial_entities:
            metadata['financial_entities'] = financial_entities
        
        return content, metadata
    
    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks of specified size with overlap.
        
        Uses smart chunking to avoid splitting in the middle of sentences.
        
        Args:
            text: The text to chunk
            
        Returns:
            List of text chunks
        """
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            # Get a chunk of text
            end = min(start + self.chunk_size, len(text))
            
            # Extend to avoid splitting sentences
            if end < len(text) and not text[end].isspace() and text[end-1] not in ['.', '!', '?', '\n']:
                # Find the next sentence boundary
                next_period = text.find('.', end)
                next_excl = text.find('!', end)
                next_quest = text.find('?', end)
                next_newline = text.find('\n', end)
                
                # Find the closest sentence boundary
                candidates = [pos for pos in [next_period, next_excl, next_quest, next_newline] if pos != -1]
                if candidates:
                    end = min(candidates) + 1
                    # Don't allow chunks to get too large
                    end = min(end, start + self.chunk_size + 200)
            
            # Extract the chunk
            chunk = text[start:end]
            chunks.append(chunk)
            
            # Move to the next chunk with overlap
            start = end - self.chunk_overlap
        
        return chunks
    
    def _generate_document_id(self, file_path: str, metadata: Dict[str, Any]) -> str:
        """
        Generate a unique identifier for a document.
        
        Args:
            file_path: Path to the document
            metadata: Document metadata
            
        Returns:
            Unique document identifier
        """
        import hashlib
        
        # Generate a deterministic hash based on file path and modification time
        file_info = f"{file_path}_{metadata.get('last_modified', '')}"
        hasher = hashlib.md5(file_info.encode('utf-8'))
        
        # Include some metadata in the ID for easier debugging
        filename = Path(file_path).stem
        safe_filename = re.sub(r'[^a-zA-Z0-9_-]', '_', filename)
        
        # Create the ID
        doc_id = f"{safe_filename}_{hasher.hexdigest()[:10]}"
        
        return doc_id
    
    def _extract_financial_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract financial entities from text.
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary of financial entity types and their instances
        """
        entities = {
            "tickers": [],
            "companies": [],
            "metrics": [],
            "indices": []
        }
        
        # Extract stock tickers (simple regex approach)
        ticker_pattern = r'\b[A-Z]{1,5}\b'  # Simple pattern for stock tickers
        potential_tickers = re.findall(ticker_pattern, text)
        
        # Filter out common words that match the pattern
        common_words = {"I", "A", "AN", "THE", "AND", "OR", "TO", "FOR"}
        entities["tickers"] = [ticker for ticker in potential_tickers if ticker not in common_words]
        
        # Extract market indices
        indices_pattern = r'\b(?:S&P 500|Dow Jones|NASDAQ|Russell 2000|NYSE)\b'
        entities["indices"] = re.findall(indices_pattern, text)
        
        # Extract financial metrics (simplified)
        metrics_pattern = r'\b(?:EPS|P/E|ROI|ROE|EBITDA|revenue|profit margin)\b'
        entities["metrics"] = re.findall(metrics_pattern, text.lower())
        
        return entities 