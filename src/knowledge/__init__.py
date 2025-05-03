"""
Knowledge management module for storing and retrieving financial information.

This package provides tools for:
- Embedding generation for text data
- Vector storage and retrieval
- Knowledge base operations

Components:
- Embedding clients: VoyageEmbeddingClient, LlamaEmbeddingClient
- Vector stores: PineconeManager 
- Knowledge base: KnowledgeBase
"""

from src.knowledge.embedding import (
    EmbeddingClient,
    VoyageEmbeddingClient,
    LlamaEmbeddingClient,
    PlaceholderEmbeddingClient,
    get_embedding_client
)
from src.knowledge.vector_store import PineconeManager
from src.knowledge.knowledge_base import KnowledgeBase

__all__ = [
    'EmbeddingClient',
    'VoyageEmbeddingClient',
    'LlamaEmbeddingClient',
    'PlaceholderEmbeddingClient',
    'get_embedding_client',
    'PineconeManager',
    'KnowledgeBase'
]

# This file marks the directory as a Python package 