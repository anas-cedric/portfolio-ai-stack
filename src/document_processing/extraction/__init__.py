"""
Extraction module for financial documents.

This module contains components for extracting structured information from financial documents,
including text extraction, table extraction, and entity recognition.
"""

from src.document_processing.extraction.document_extractor import DocumentExtractor
from src.document_processing.extraction.table_extractor import TableExtractor

__all__ = ["DocumentExtractor", "TableExtractor"] 