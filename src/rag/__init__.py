"""
RAG (Retrieval Augmented Generation) System for fund knowledge.

This package contains:
- Query processing for understanding different question types
- Enhanced retrieval with hybrid search capabilities
- Response generation using Claude 3.7
- A CLI tool for interacting with the system
"""

from src.rag.query_processor import QueryProcessor, QueryType
from src.rag.retriever import Retriever
from src.rag.response_generator import ResponseGenerator
from src.rag.cli import FundRagCLI

__all__ = [
    'QueryProcessor',
    'QueryType',
    'Retriever',
    'ResponseGenerator',
    'FundRagCLI'
] 