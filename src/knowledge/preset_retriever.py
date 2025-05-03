"""
Preset Knowledge Retriever Module.

This module provides retrieval capabilities using the preset financial data,
acting as a replacement for more complex document processing pipelines while
maintaining the same interface expected by the RAG system.
"""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple

from src.data.preset_financial_data import PresetFinancialData
from src.knowledge.vector_store import PineconeManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PresetKnowledgeRetriever:
    """
    Knowledge retriever using preset financial data.
    
    This class provides methods to retrieve context for queries
    using preset financial data with mock embeddings, simulating
    a more complex semantic search pipeline.
    """
    
    def __init__(
        self,
        vector_db: Optional[PineconeManager] = None,
        namespace: str = "financial_knowledge",
        top_k: int = 5,
        data_path: Optional[str] = None
    ):
        """
        Initialize the preset knowledge retriever.
        
        Args:
            vector_db: Optional PineconeManager instance
            namespace: Namespace to use in vector database
            top_k: Default number of results to return
            data_path: Optional path to preset data files
        """
        self.preset_data = PresetFinancialData(data_path=data_path)
        self.vector_db = vector_db or PineconeManager()
        self.namespace = namespace
        self.top_k = top_k
        
        # Check if namespace exists, if not, create it
        self._ensure_namespace_initialized()
        
        logger.info(f"Initialized preset knowledge retriever for namespace: {namespace}")
        
    def _ensure_namespace_initialized(self) -> None:
        """Ensure the namespace is initialized with data."""
        # Check if namespace exists and has data
        stats = self.vector_db.get_stats()
        namespaces = stats.get("namespaces", {})
        
        # If namespace doesn't exist or is empty, populate it
        if self.namespace not in namespaces or namespaces.get(self.namespace, 0) == 0:
            logger.info(f"Namespace '{self.namespace}' empty or not found. Initializing with preset data...")
            self._initialize_namespace()
        else:
            logger.info(f"Namespace '{self.namespace}' already contains {namespaces.get(self.namespace, 0)} vectors")
    
    def _initialize_namespace(self) -> None:
        """Initialize the namespace with preset data."""
        from src.pipelines.preset_data_integration import PresetDataIntegration
        
        # Create integration and load data
        integration = PresetDataIntegration(
            vector_db=self.vector_db,
            data_path=self.preset_data.data_path,
            namespace=self.namespace
        )
        
        # Load data to vector database
        stats = integration.load_data_to_vector_db(batch_size=10)
        logger.info(f"Initialized namespace '{self.namespace}' with {stats['vectors_uploaded']} vectors")
    
    def semantic_search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: Optional[int] = None,
        namespace: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using the preset financial data.
        
        Args:
            query: Query string
            filters: Optional metadata filters
            top_k: Optional number of results to return
            namespace: Optional namespace to search in
            
        Returns:
            List of search results with scores and metadata
        """
        start_time = time.time()
        
        # Generate embedding for query
        query_embedding = self.preset_data.get_mock_embedding(query)
        
        # Set defaults
        namespace = namespace or self.namespace
        top_k = top_k or self.top_k
        
        # Search vector database
        results = self.vector_db.search_vectors(
            query_vector=query_embedding,
            namespace=namespace,
            top_k=top_k,
            filters=filters
        )
        
        # Log performance
        elapsed_time = time.time() - start_time
        logger.info(f"Semantic search completed in {elapsed_time:.2f}s, found {len(results)} results")
        
        # Format results if needed
        formatted_results = []
        for result in results:
            # Extract metadata
            metadata = result.get("metadata", {})
            
            # Format each result
            formatted_results.append({
                "id": result.get("id", ""),
                "score": result.get("score", 0.0),
                "content": metadata.get("text", ""),
                "metadata": metadata
            })
            
        return formatted_results
    
    def hybrid_search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: Optional[int] = None,
        namespace: Optional[str] = None,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search (semantic + keyword) using preset data.
        
        This is a simplified implementation that primarily relies on
        semantic search with some minimal keyword boosting.
        
        Args:
            query: Query string
            filters: Optional metadata filters
            top_k: Optional number of results to return
            namespace: Optional namespace to search in
            semantic_weight: Weight for semantic search results
            keyword_weight: Weight for keyword search results
            
        Returns:
            List of search results with scores and metadata
        """
        # For simplicity, just use semantic search for now
        # A real implementation would combine semantic and keyword search
        results = self.semantic_search(
            query=query,
            filters=filters,
            top_k=top_k,
            namespace=namespace
        )
        
        # Log the approach
        logger.info(f"Using simplified hybrid search with semantic_weight={semantic_weight}, keyword_weight={keyword_weight}")
        
        return results
    
    def get_context_for_query(
        self,
        query: str,
        query_type: str = "general",
        filters: Optional[Dict[str, Any]] = None,
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get context for a query, with adjustments based on query type.
        
        Args:
            query: Query string
            query_type: Type of query (e.g., "fund_info", "investment_strategy")
            filters: Optional metadata filters
            top_k: Optional number of results to return
            
        Returns:
            List of context items with scores and metadata
        """
        # Adjust filters based on query type
        if not filters:
            filters = {}
            
        if query_type == "fund_info":
            # For fund info queries, prioritize fund knowledge
            filters["category"] = "fund_knowledge"
        elif query_type == "investment_strategy":
            # For investment strategy queries, prioritize investment principles
            filters["category"] = "investment_principles"
        
        # Use hybrid search for best results
        results = self.hybrid_search(
            query=query,
            filters=filters,
            top_k=top_k
        )
        
        return results


# Example usage
if __name__ == "__main__":
    # Initialize retriever
    retriever = PresetKnowledgeRetriever()
    
    # Test query
    test_query = "What is the S&P 500 index and how can I invest in it?"
    
    # Get context for query
    results = retriever.get_context_for_query(
        query=test_query,
        query_type="fund_info",
        top_k=3
    )
    
    # Print results
    print(f"\nResults for query: '{test_query}'")
    for i, result in enumerate(results):
        print(f"\n{i+1}. {result['metadata'].get('title')} (Score: {result['score']:.4f})")
        print(f"   Content: {result['content'][:200]}...") 