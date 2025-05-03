"""
Unstructured document processor for financial documents.

This module implements integration with the Unstructured library for
processing financial documents including PDFs, Word documents, PowerPoint
presentations, and more.
"""

import os
import logging
import re
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path
import tempfile

# Try to import Unstructured components, handling potential import errors
try:
    from unstructured.partition.auto import partition
    from unstructured.partition.pdf import partition_pdf
    from unstructured.partition.docx import partition_docx
    from unstructured.partition.pptx import partition_pptx
    from unstructured.partition.html import partition_html
    from unstructured.staging.base import elements_to_json
    from unstructured.cleaners.core import clean_text, replace_unicode_quotes
    from unstructured.staging.huggingface import chunk_elements
except ImportError as e:
    logging.error(f"Error importing Unstructured components: {e}")
    logging.error("Make sure all Unstructured dependencies are installed:")
    logging.error("pip install unstructured unstructured-inference pdfminer.six pdf2image pytesseract python-docx python-pptx pi-heif")
    raise

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnstructuredProcessor:
    """
    Document processor using Unstructured for financial documents.
    
    This class provides methods to extract text and metadata from various financial
    document formats like PDFs, Word documents, PowerPoint presentations, etc.
    
    Features:
    - Automatic format detection
    - Document partitioning (splitting into logical elements)
    - Table extraction
    - Figure/chart detection
    - OCR for scanned documents
    - Text cleaning and normalization
    """
    
    def __init__(
        self,
        ocr_enabled: bool = True,
        extract_tables: bool = True,
        extract_images: bool = False,
        table_extraction_mode: str = "fast",
        chunk_size: int = 512,
        chunk_overlap: int = 50
    ):
        """
        Initialize the UnstructuredProcessor.
        
        Args:
            ocr_enabled: Whether to use OCR for image-based PDFs
            extract_tables: Whether to extract tables
            extract_images: Whether to extract images (requires more dependencies)
            table_extraction_mode: Mode for table extraction ('fast' or 'accurate')
            chunk_size: Default chunk size for text chunking
            chunk_overlap: Default overlap between chunks
        """
        self.ocr_enabled = ocr_enabled
        self.extract_tables = extract_tables
        self.extract_images = extract_images
        self.table_extraction_mode = table_extraction_mode
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Document type to partition function mapping
        self.partition_functions = {
            "pdf": partition_pdf,
            "docx": partition_docx,
            "pptx": partition_pptx,
            "html": partition_html,
        }
        
        logger.info(f"Initialized UnstructuredProcessor with OCR={ocr_enabled}, "
                  f"extract_tables={extract_tables}, chunk_size={chunk_size}")
    
    def process_file(
        self,
        file_path: Union[str, Path],
        metadata: Optional[Dict[str, Any]] = None,
        file_type: Optional[str] = None,
        chunk: bool = True
    ) -> Dict[str, Any]:
        """
        Process a document file and extract text and metadata.
        
        Args:
            file_path: Path to the document file
            metadata: Additional metadata to include
            file_type: Override file type detection
            chunk: Whether to chunk the text
            
        Returns:
            Dictionary containing extracted text, elements, and metadata
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine file type if not specified
        if file_type is None:
            file_type = file_path.suffix.lower().lstrip(".")
        
        logger.info(f"Processing {file_type} document: {file_path}")
        
        # Initialize metadata if None
        if metadata is None:
            metadata = {}
        
        # Add file metadata
        file_metadata = {
            "file_name": file_path.name,
            "file_path": str(file_path),
            "file_type": file_type,
            "file_size": file_path.stat().st_size,
            "processed_by": "unstructured",
        }
        metadata.update(file_metadata)
        
        try:
            # Choose partition function based on file type
            if file_type in self.partition_functions:
                partition_func = self.partition_functions[file_type]
                
                # Handle PDF-specific parameters
                if file_type == "pdf":
                    elements = partition_func(
                        str(file_path),
                        infer_table_structure=self.extract_tables,
                        extract_images=self.extract_images,
                        extract_image_text=self.ocr_enabled,
                        include_metadata=True
                    )
                else:
                    elements = partition_func(
                        str(file_path),
                        include_metadata=True
                    )
            else:
                # Use auto-detection for other file types
                elements = partition(
                    str(file_path),
                    include_metadata=True
                )
            
            logger.info(f"Extracted {len(elements)} elements from {file_path}")
            
            # Clean the text in each element
            for element in elements:
                if hasattr(element, "text"):
                    element.text = clean_text(element.text)
                    element.text = replace_unicode_quotes(element.text)
            
            # Chunk the elements if requested
            chunked_elements = []
            if chunk:
                chunked_elements = chunk_elements(
                    elements,
                    chunk_size=self.chunk_size,
                    overlap=self.chunk_overlap
                )
                logger.info(f"Chunked into {len(chunked_elements)} chunks")
            
            # Convert elements to dict for easier manipulation
            elements_json = elements_to_json(elements)
            chunked_elements_json = elements_to_json(chunked_elements) if chunked_elements else []
            
            # Extract plain text from elements
            full_text = "\n\n".join([elem.get("text", "") for elem in elements_json])
            
            # Create result dictionary
            result = {
                "metadata": metadata,
                "elements": elements_json,
                "chunked_elements": chunked_elements_json if chunk else [],
                "text": full_text,
                "success": True,
                "error": None
            }
            
            # Extract tables separately if present
            tables = [elem for elem in elements_json if elem.get("type") == "Table"]
            if tables:
                result["tables"] = tables
                logger.info(f"Extracted {len(tables)} tables")
            
            return result
            
        except Exception as e:
            error_msg = f"Error processing document {file_path}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "metadata": metadata,
                "elements": [],
                "chunked_elements": [],
                "text": "",
                "success": False,
                "error": error_msg
            }
    
    def process_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        chunk: bool = True
    ) -> Dict[str, Any]:
        """
        Process raw text directly.
        
        Args:
            text: The text to process
            metadata: Additional metadata to include
            chunk: Whether to chunk the text
            
        Returns:
            Dictionary containing processed text and metadata
        """
        if metadata is None:
            metadata = {}
        
        try:
            # Clean the text
            cleaned_text = clean_text(text)
            cleaned_text = replace_unicode_quotes(cleaned_text)
            
            # Create a temporary file to process with Unstructured
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as temp_file:
                temp_file.write(cleaned_text)
                temp_path = temp_file.name
            
            # Process the temporary file
            try:
                elements = partition(temp_path, include_metadata=True)
                
                # Chunk the elements if requested
                chunked_elements = []
                if chunk:
                    chunked_elements = chunk_elements(
                        elements,
                        chunk_size=self.chunk_size,
                        overlap=self.chunk_overlap
                    )
                
                # Convert elements to dict
                elements_json = elements_to_json(elements)
                chunked_elements_json = elements_to_json(chunked_elements) if chunked_elements else []
                
                return {
                    "metadata": metadata,
                    "elements": elements_json,
                    "chunked_elements": chunked_elements_json if chunk else [],
                    "text": cleaned_text,
                    "success": True,
                    "error": None
                }
            finally:
                # Clean up the temporary file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
        except Exception as e:
            error_msg = f"Error processing text: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "metadata": metadata,
                "elements": [],
                "chunked_elements": [],
                "text": text,  # Return original text on error
                "success": False,
                "error": error_msg
            }
    
    def extract_financial_metrics(self, elements_json: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract financial metrics from document elements.
        
        This is a simple implementation that looks for common financial metric patterns.
        For production use, this should be enhanced with a more sophisticated model.
        
        Args:
            elements_json: List of document elements in JSON format
            
        Returns:
            Dictionary of extracted financial metrics
        """
        metrics = {}
        # Simple regex-based extraction could be implemented here
        # In a production system, this would use a financial NER model
        
        # Simple example: look for revenue, profit, EPS mentions
        for element in elements_json:
            text = element.get("text", "")
            
            # Very simplistic pattern matching - would be more sophisticated in practice
            if "revenue" in text.lower() and "$" in text:
                # Simple extraction logic - in production this would be more robust
                metrics["revenue_mentioned"] = True
            
            if "profit" in text.lower() and "$" in text:
                metrics["profit_mentioned"] = True
                
            if "eps" in text.lower() or "earnings per share" in text.lower():
                metrics["eps_mentioned"] = True
        
        return metrics
    
    def batch_process_directory(
        self,
        directory_path: Union[str, Path],
        recursive: bool = False,
        file_types: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Process all documents in a directory.
        
        Args:
            directory_path: Path to the directory
            recursive: Whether to process subdirectories
            file_types: List of file extensions to process (e.g., ["pdf", "docx"])
            metadata: Additional metadata to include for all files
            
        Returns:
            List of processing results
        """
        directory_path = Path(directory_path)
        if not directory_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory_path}")
        
        if file_types is None:
            file_types = ["pdf", "docx", "pptx", "txt", "html"]
        
        if metadata is None:
            metadata = {}
        
        # Add directory info to metadata
        dir_metadata = {
            "source_directory": str(directory_path),
            "batch_processed": True
        }
        metadata.update(dir_metadata)
        
        results = []
        
        # Get file pattern based on whether to recurse
        if recursive:
            file_paths = []
            for file_type in file_types:
                file_paths.extend(directory_path.glob(f"**/*.{file_type}"))
        else:
            file_paths = []
            for file_type in file_types:
                file_paths.extend(directory_path.glob(f"*.{file_type}"))
        
        logger.info(f"Found {len(file_paths)} files to process in {directory_path}")
        
        # Process each file
        for file_path in file_paths:
            try:
                # Create file-specific metadata
                file_metadata = metadata.copy()
                file_metadata["relative_path"] = str(file_path.relative_to(directory_path))
                
                # Process the file
                result = self.process_file(
                    file_path=file_path,
                    metadata=file_metadata,
                    file_type=file_path.suffix.lower().lstrip(".")
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
                    "elements": [],
                    "chunked_elements": [],
                    "text": "",
                    "success": False,
                    "error": error_msg
                })
        
        return results 