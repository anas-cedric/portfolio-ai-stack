"""
Document Parsing Pipeline for Financial Documents.

This module implements a comprehensive parsing pipeline for financial documents,
handling the document ingestion, processing, metadata extraction, and preparation
for embedding and storage.
"""

import os
import logging
import json
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path
from datetime import datetime

from src.document_processing.unstructured_processor import UnstructuredProcessor
from src.knowledge.embedding import get_embedding_client

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentParsingPipeline:
    """
    Pipeline for processing financial documents and extracting structured information.
    
    This pipeline manages the end-to-end process of:
    1. Document ingestion (PDF, DOCX, PPTX, etc.)
    2. Text extraction and preprocessing
    3. Financial metadata extraction
    4. Chunking for embedding
    5. Preparation for storage in vector database
    """
    
    def __init__(
        self,
        embedding_client_type: str = "voyage",
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        ocr_enabled: bool = True,
        extract_tables: bool = True
    ):
        """
        Initialize the document parsing pipeline.
        
        Args:
            embedding_client_type: Type of embedding client to use
            chunk_size: Size of text chunks for embedding
            chunk_overlap: Overlap between chunks
            ocr_enabled: Whether to use OCR for image-based documents
            extract_tables: Whether to extract tables from documents
        """
        # Initialize the document processor
        logger.info("Initializing Unstructured document processor")
        self.document_processor = UnstructuredProcessor(
            ocr_enabled=ocr_enabled,
            extract_tables=extract_tables,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Initialize embedding client
        self.embedding_client = get_embedding_client(embedding_client_type)
        
        # Track statistics
        self.stats = {
            "documents_processed": 0,
            "successful": 0,
            "failed": 0,
            "total_chunks": 0
        }
        
        logger.info(f"Initialized DocumentParsingPipeline with {embedding_client_type} embeddings")
    
    def process_document(
        self,
        file_path: Union[str, Path],
        document_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        category: Optional[str] = None,
        document_date: Optional[str] = None,
        financial_entity: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a single financial document through the pipeline.
        
        Args:
            file_path: Path to the document
            document_type: Type of financial document (e.g., "prospectus", "annual_report")
            metadata: Additional metadata to include
            category: Document category (e.g., "ETF", "Stock", "Market")
            document_date: Date of document publication (YYYY-MM-DD format)
            financial_entity: Entity associated with document (e.g., ticker or company)
            
        Returns:
            Dictionary with processed document data and metadata
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
        
        # Initialize metadata if None
        if metadata is None:
            metadata = {}
        
        # Add financial document metadata
        financial_metadata = {
            "document_type": document_type,
            "category": category,
            "document_date": document_date or datetime.now().strftime("%Y-%m-%d"),
            "financial_entity": financial_entity,
            "processing_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        metadata.update({k: v for k, v in financial_metadata.items() if v is not None})
        
        logger.info(f"Processing document: {file_path}")
        
        # Process the document using the selected processor
        processed_data = self.document_processor.process_file(
            file_path=file_path,
            metadata=metadata
        )
        
        # Update statistics
        self.stats["documents_processed"] += 1
        if processed_data["success"]:
            self.stats["successful"] += 1
            self.stats["total_chunks"] += len(processed_data.get("chunked_elements", []))
        else:
            self.stats["failed"] += 1
            return processed_data  # Return early if processing failed
        
        # Extract financial metrics from the document
        financial_metrics = self.document_processor.extract_financial_metrics(
            processed_data["elements"]
        )
        processed_data["financial_metrics"] = financial_metrics
        
        # Create embedding-ready chunks
        embedding_data = self._prepare_for_embedding(processed_data)
        processed_data["embedding_data"] = embedding_data
        
        return processed_data
    
    def process_directory(
        self,
        directory_path: Union[str, Path],
        recursive: bool = True,
        document_type: Optional[str] = None,
        category: Optional[str] = None,
        financial_entity: Optional[str] = None,
        file_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Process all financial documents in a directory.
        
        Args:
            directory_path: Path to the directory
            recursive: Whether to process subdirectories
            document_type: Type of financial documents (e.g., "prospectus")
            category: Document category (e.g., "ETF", "Stock", "Market")
            financial_entity: Entity associated with documents (e.g., ticker)
            file_types: List of file extensions to process
            
        Returns:
            List of processing results for each document
        """
        directory_path = Path(directory_path)
        if not directory_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory_path}")
        
        if file_types is None:
            file_types = ["pdf", "docx", "pptx", "txt", "html", "csv", "xlsx", "xls"]
        
        # Create base metadata for all documents in directory
        base_metadata = {
            "document_type": document_type,
            "category": category,
            "financial_entity": financial_entity,
            "source_directory": str(directory_path),
            "batch_id": f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        
        # Process all files in directory
        results = []
        file_paths = []
        
        # Get all files of specified types
        for file_type in file_types:
            if recursive:
                file_paths.extend(directory_path.glob(f"**/*.{file_type}"))
            else:
                file_paths.extend(directory_path.glob(f"*.{file_type}"))
        
        logger.info(f"Found {len(file_paths)} documents to process in {directory_path}")
        
        # Process each file
        for file_path in file_paths:
            try:
                # Infer document date from filename or modification date
                doc_date = self._infer_document_date(file_path)
                
                # Create document-specific metadata
                doc_metadata = base_metadata.copy()
                doc_metadata["relative_path"] = str(file_path.relative_to(directory_path))
                
                # Process the document
                result = self.process_document(
                    file_path=file_path,
                    document_type=document_type,
                    metadata=doc_metadata,
                    category=category,
                    document_date=doc_date,
                    financial_entity=financial_entity
                )
                
                results.append(result)
                logger.info(f"Processed {file_path}")
                
            except Exception as e:
                error_msg = f"Error processing {file_path}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                results.append({
                    "metadata": {
                        "file_name": file_path.name,
                        "file_path": str(file_path),
                        "error": error_msg
                    },
                    "success": False,
                    "error": error_msg
                })
        
        return results
    
    def _prepare_for_embedding(self, processed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Prepare document chunks for embedding.
        
        Args:
            processed_data: Processed document data
            
        Returns:
            List of embedding-ready chunks with metadata
        """
        embedding_data = []
        
        # Use chunked elements if available, otherwise use the full document
        chunks = processed_data.get("chunked_elements", [])
        
        if not chunks and processed_data.get("text"):
            # If no chunks but text exists, create a single chunk for the whole document
            chunks = [{
                "text": processed_data["text"],
                "type": "Document",
                "metadata": {"page_number": 1}
            }]
        
        # Base metadata for all chunks
        base_metadata = processed_data.get("metadata", {})
        
        # Process each chunk
        for i, chunk in enumerate(chunks):
            chunk_text = chunk.get("text", "")
            if not chunk_text.strip():
                continue  # Skip empty chunks
            
            # Create metadata for this chunk
            chunk_metadata = base_metadata.copy()
            
            # Add chunk-specific metadata
            chunk_metadata.update({
                "chunk_id": i,
                "total_chunks": len(chunks),
                "chunk_type": chunk.get("type", "Unknown"),
                "page_number": chunk.get("metadata", {}).get("page_number"),
                "element_id": chunk.get("element_id", f"chunk_{i}")
            })
            
            # Remove None values from metadata
            chunk_metadata = {k: v for k, v in chunk_metadata.items() if v is not None}
            
            # Add to embedding data
            embedding_data.append({
                "text": chunk_text,
                "metadata": chunk_metadata
            })
        
        return embedding_data
    
    def _infer_document_date(self, file_path: Path) -> Optional[str]:
        """
        Infer the document date from filename or modification date.
        
        Args:
            file_path: Path to the document
            
        Returns:
            Document date in YYYY-MM-DD format, or None if can't be inferred
        """
        # First try to extract date from filename (common patterns in financial docs)
        filename = file_path.stem
        
        # Look for common date patterns in financial document filenames
        # Examples: annual_report_2023.pdf, 10K_2023_03_15.pdf, Q1_2023.pdf
        
        # This is a simple implementation - in production would use more robust regex
        # or NLP techniques to extract dates from filenames
        
        # If date can't be extracted from filename, use file modification date
        mod_time = file_path.stat().st_mtime
        mod_date = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d")
        
        return mod_date
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get processing statistics.
        
        Returns:
            Dictionary of processing statistics
        """
        return self.stats 