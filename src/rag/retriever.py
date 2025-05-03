"""
Enhanced Retrieval Module for RAG System.

This module is responsible for:
1. Text chunking for longer documents
2. Metadata filtering based on query type
3. Hybrid retrieval (semantic + keyword)
"""

import os
import re
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from dotenv import load_dotenv

from src.knowledge.embedding import get_embedding_client
from src.knowledge.vector_store import PineconeManager

load_dotenv()

class Retriever:
    """
    Enhanced retrieval component for the RAG system.
    
    Features:
    - Text chunking for longer documents
    - Metadata filtering based on query type
    - Hybrid retrieval (semantic + keyword)
    """
    
    def __init__(self, embedding_client_type: str = "voyage"):
        """
        Initialize the retriever with the specified embedding client.
        
        Args:
            embedding_client_type: Type of embedding client to use ('voyage', 'llama', etc.)
        """
        self.embedding_client = get_embedding_client(embedding_client_type)
        self.vector_db = PineconeManager()
        
        # Maximum context size for response generation
        self.max_context_size = 4000 
        
        # Chunk size and overlap for text chunking
        self.chunk_size = 512
        self.chunk_overlap = 100
        
        # Score thresholds for relevance filtering
        self.semantic_threshold = 0.0  # Lower threshold to include more results
    
    def retrieve(
        self, 
        query: str, 
        processed_query: Dict[str, Any],
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Retrieve relevant knowledge based on the processed query.
        
        Args:
            query: The original query string
            processed_query: The processed query from QueryProcessor
            top_k: Number of results to retrieve
            
        Returns:
            Dict containing:
            - contexts: List of retrieved text contexts
            - sources: List of source information
            - relevance_scores: List of relevance scores
        """
        # Use the expanded query for better retrieval
        expanded_query = processed_query.get("expanded_query", query)
        
        # Get metadata filters from processed query
        metadata_filters = processed_query.get("metadata_filters")
        
        print(f"DEBUG - expanded_query: {expanded_query}")
        print(f"DEBUG - metadata_filters: {metadata_filters}")
        
        # Retrieve documents using semantic search
        semantic_results = self._semantic_search(
            expanded_query, 
            top_k=top_k * 2,  # Get more results initially for re-ranking
            filters=metadata_filters
        )
        
        print(f"DEBUG - semantic_results count: {len(semantic_results)}")
        for i, result in enumerate(semantic_results):
            print(f"DEBUG - semantic result {i+1}:")
            print(f"DEBUG -   ID: {result['id']}")
            print(f"DEBUG -   Score: {result['score']}")
            print(f"DEBUG -   Content: {result['content'][:50]}...")
        
        # Add keyword search results (simple implementation)
        # In a production system, this would use a more sophisticated BM25 or similar algorithm
        keyword_results = self._keyword_search(
            query,
            semantic_results,
            processed_query.get("entities", {})
        )
        
        print(f"DEBUG - keyword_results count: {len(keyword_results)}")
        
        # Combine and re-rank results
        combined_results = self._combine_and_rerank(
            semantic_results,
            keyword_results,
            top_k=top_k
        )
        
        print(f"DEBUG - combined_results count: {len(combined_results)}")
        
        # Format the results for the response generator
        contexts = [item["content"] for item in combined_results]
        sources = [self._format_source(item["metadata"]) for item in combined_results]
        relevance_scores = [item["score"] for item in combined_results]
        
        # Apply chunking if needed
        if sum(len(context) for context in contexts) > self.max_context_size:
            contexts, sources, relevance_scores = self._chunk_and_select(
                contexts, sources, relevance_scores
            )
        
        return {
            "contexts": contexts,
            "sources": sources,
            "relevance_scores": relevance_scores,
            "raw_results": combined_results  # Include raw results for debugging
        }
    
    def _semantic_search(
        self, 
        query: str, 
        top_k: int = 10, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using vector embeddings.
        
        Args:
            query: The query string
            top_k: Number of results to retrieve
            filters: Optional metadata filters
            
        Returns:
            List of result dictionaries with content, metadata, and score
        """
        # Generate embedding for the query
        query_embedding = self.embedding_client.embed_text(query)
        
        print(f"DEBUG - _semantic_search - query: {query}")
        print(f"DEBUG - _semantic_search - embedding dimension: {len(query_embedding)}")
        print(f"DEBUG - _semantic_search - filters: {filters}")
        
        # Query the vector database
        try:
            results = self.vector_db.query(
                query_vector=query_embedding,
                top_k=top_k,
                filter=filters
            )
            
            print(f"DEBUG - _semantic_search - raw results count: {len(results)}")
            for i, result in enumerate(results):
                print(f"DEBUG - _semantic_search - raw result {i+1}:")
                print(f"DEBUG -   ID: {result.id if hasattr(result, 'id') else 'No ID'}")
                print(f"DEBUG -   Score: {result.score if hasattr(result, 'score') else 'No score'}")
                if hasattr(result, 'metadata'):
                    print(f"DEBUG -   Metadata keys: {result.metadata.keys()}")
                    if 'fund_ticker' in result.metadata:
                        print(f"DEBUG -   fund_ticker: {result.metadata['fund_ticker']}")
            
            # If we got no results with the filter, try without it
            if len(results) == 0 and filters is not None:
                print(f"DEBUG - _semantic_search - No results with filter, trying without filter")
                results_without_filter = self.vector_db.query(
                    query_vector=query_embedding,
                    top_k=top_k,
                    filter=None
                )
                
                print(f"DEBUG - _semantic_search - raw results without filter count: {len(results_without_filter)}")
                for i, result in enumerate(results_without_filter):
                    print(f"DEBUG - _semantic_search - raw result without filter {i+1}:")
                    print(f"DEBUG -   ID: {result.id if hasattr(result, 'id') else 'No ID'}")
                    print(f"DEBUG -   Score: {result.score if hasattr(result, 'score') else 'No score'}")
                    if hasattr(result, 'metadata'):
                        print(f"DEBUG -   Metadata keys: {result.metadata.keys()}")
                        if 'fund_ticker' in result.metadata:
                            print(f"DEBUG -   fund_ticker: {result.metadata['fund_ticker']}")
                
                # If the filter was looking for a specific ticker, try to find it in the unfiltered results
                if filters and 'fund_ticker' in filters:
                    ticker = filters['fund_ticker']
                    print(f"DEBUG - _semantic_search - Looking for ticker {ticker} in unfiltered results")
                    
                    # Filter the results manually
                    ticker_results = []
                    for result in results_without_filter:
                        if hasattr(result, 'metadata') and 'fund_ticker' in result.metadata:
                            if result.metadata['fund_ticker'] == ticker:
                                ticker_results.append(result)
                                print(f"DEBUG - _semantic_search - Found match for ticker {ticker}: {result.id}")
                    
                    # Use these results if we found any
                    if ticker_results:
                        print(f"DEBUG - _semantic_search - Using {len(ticker_results)} manually filtered results for ticker {ticker}")
                        results = ticker_results
        except Exception as e:
            print(f"DEBUG - _semantic_search - Error querying vector database: {e}")
            return []
        
        # Transform results to a standardized format
        formatted_results = []
        for item in results:
            # For cosine similarity, we should compare absolute values since scores can be negative
            # -1 is the worst score, 0 is neutral, 1 is the best
            if hasattr(item, 'score'):
                score_abs = abs(item.score) 
                # Skip if absolute value is below threshold, meaning very weak correlation
                if score_abs < self.semantic_threshold:
                    print(f"DEBUG - _semantic_search - Skipping result with abs score {score_abs} below threshold {self.semantic_threshold}")
                    continue  # Skip results below the similarity threshold
            
            # Extract content from metadata - check multiple possible fields
            content = ""
            if hasattr(item, 'metadata'):
                if "content" in item.metadata:
                    content = item.metadata["content"]
                elif "description" in item.metadata:
                    content = item.metadata["description"]
                
                # If we have both investment_thesis and investment_highlights, combine them
                if "investment_thesis" in item.metadata:
                    if content:
                        content += "\n\n" + item.metadata["investment_thesis"]
                    else:
                        content = item.metadata["investment_thesis"]
                
                if "investment_highlights" in item.metadata:
                    if content:
                        content += "\n\n" + item.metadata["investment_highlights"]
                    else:
                        content = item.metadata["investment_highlights"]
                
                # Add investment_risks if available
                if "investment_risks" in item.metadata:
                    if content:
                        content += "\n\n" + "Risks: " + item.metadata["investment_risks"]
                    else:
                        content = "Risks: " + item.metadata["investment_risks"]
                
            formatted_results.append({
                "id": item.id,
                "content": content,
                "metadata": item.metadata if hasattr(item, 'metadata') else {},
                "score": item.score if hasattr(item, 'score') else 0.0,
                "source": "semantic"
            })
        
        print(f"DEBUG - _semantic_search - formatted_results count: {len(formatted_results)}")
        return formatted_results
    
    def _keyword_search(
        self, 
        query: str, 
        semantic_results: List[Dict[str, Any]],
        entities: Dict[str, List[str]]
    ) -> List[Dict[str, Any]]:
        """
        Perform keyword search to complement semantic search.
        
        Simple implementation that checks for keyword presence in the semantic results.
        A production system would use a proper inverted index (Elasticsearch, etc.)
        
        Args:
            query: The query string
            semantic_results: Results from semantic search
            entities: Extracted entities from the query
            
        Returns:
            List of result dictionaries with keyword match scores
        """
        # Extract keywords from query
        keywords = set(re.findall(r'\b\w+\b', query.lower()))
        
        # Add extracted entities as high-importance keywords
        for entity_list in entities.values():
            for entity in entity_list:
                keywords.update(re.findall(r'\b\w+\b', entity.lower()))
        
        # Filter out common words
        stopwords = {"the", "and", "or", "a", "an", "in", "on", "at", "to", "for", "with", "by", "about"}
        keywords = keywords - stopwords
        
        # Score the semantic results based on keyword presence
        keyword_results = []
        for item in semantic_results:
            content = item["content"].lower()
            
            # Count keyword matches
            match_count = sum(1 for keyword in keywords if keyword in content)
            
            # Calculate a keyword score
            if len(keywords) > 0:
                keyword_score = match_count / len(keywords)
            else:
                keyword_score = 0
                
            # Clone the item and add keyword score
            result = dict(item)
            result["keyword_score"] = keyword_score
            result["source"] = "keyword"
            keyword_results.append(result)
        
        return keyword_results
    
    def _combine_and_rerank(
        self, 
        semantic_results: List[Dict[str, Any]], 
        keyword_results: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Combine semantic and keyword results and rerank them.
        
        Args:
            semantic_results: Results from semantic search
            keyword_results: Results from keyword search
            top_k: Number of results to return
            
        Returns:
            Combined and reranked list of results
        """
        # Create a unified result set
        id_to_result = {}
        
        # Add semantic results
        for item in semantic_results:
            id_to_result[item["id"]] = {
                "id": item["id"],
                "content": item["content"],
                "metadata": item["metadata"],
                "semantic_score": item["score"],
                "keyword_score": 0,
                "score": item["score"]  # Initial score is just the semantic score
            }
        
        # Update with keyword scores
        for item in keyword_results:
            if item["id"] in id_to_result:
                result = id_to_result[item["id"]]
                result["keyword_score"] = item["keyword_score"]
                
                # Combine scores (0.7 * semantic + 0.3 * keyword)
                result["score"] = 0.7 * result["semantic_score"] + 0.3 * item["keyword_score"]
            else:
                # This shouldn't happen given our implementation, but just in case
                id_to_result[item["id"]] = {
                    "id": item["id"],
                    "content": item["content"],
                    "metadata": item["metadata"],
                    "semantic_score": 0,
                    "keyword_score": item["keyword_score"],
                    "score": 0.3 * item["keyword_score"]  # Only keyword score
                }
        
        # Convert to list and sort by combined score
        results = list(id_to_result.values())
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # Return top_k results
        return results[:top_k]
    
    def _chunk_and_select(
        self, 
        contexts: List[str], 
        sources: List[str], 
        scores: List[float]
    ) -> Tuple[List[str], List[str], List[float]]:
        """
        Chunk longer texts and select the most relevant chunks to fit within max context size.
        
        Args:
            contexts: List of context texts
            sources: List of source information
            scores: List of relevance scores
            
        Returns:
            Tuple of (chunked_contexts, chunked_sources, chunked_scores)
        """
        chunked_contexts = []
        chunked_sources = []
        chunked_scores = []
        
        for context, source, score in zip(contexts, sources, scores):
            # If the context is short, keep it as is
            if len(context) < self.chunk_size:
                chunked_contexts.append(context)
                chunked_sources.append(source)
                chunked_scores.append(score)
                continue
            
            # Split into chunks
            chunks = self._split_text(context, self.chunk_size, self.chunk_overlap)
            
            # Add each chunk with its source and a slightly decreasing score
            # This ensures earlier chunks from higher-scored documents are prioritized
            for i, chunk in enumerate(chunks):
                chunk_score = score * (0.98 ** i)  # Slightly decrease score for later chunks
                chunked_contexts.append(chunk)
                chunked_sources.append(f"{source} (part {i+1}/{len(chunks)})")
                chunked_scores.append(chunk_score)
        
        # Sort by score and select chunks to fit within max context size
        sorted_items = sorted(
            zip(chunked_contexts, chunked_sources, chunked_scores),
            key=lambda x: x[2],
            reverse=True
        )
        
        # Select chunks to fit within max context size
        selected_contexts = []
        selected_sources = []
        selected_scores = []
        total_size = 0
        
        for context, source, score in sorted_items:
            if total_size + len(context) <= self.max_context_size:
                selected_contexts.append(context)
                selected_sources.append(source)
                selected_scores.append(score)
                total_size += len(context)
            else:
                break
        
        return selected_contexts, selected_sources, selected_scores
    
    def _split_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """
        Split text into chunks with overlap.
        
        Args:
            text: The text to split
            chunk_size: Maximum size of each chunk
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of text chunks
        """
        # Simple character-based chunking
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            
            # Try to end at a sentence boundary or period
            if end < len(text):
                # Look for the last sentence boundary within the chunk
                last_period = text.rfind(".", start, end)
                if last_period > start + chunk_size // 2:
                    end = last_period + 1
            
            # Extract the chunk
            chunk = text[start:end]
            chunks.append(chunk)
            
            # Move to the next chunk with overlap
            start = end - overlap
        
        return chunks
    
    def _format_source(self, metadata: Dict[str, Any]) -> str:
        """
        Format source information from metadata.
        
        Args:
            metadata: The metadata dictionary
            
        Returns:
            Formatted source string
        """
        title = metadata.get("title", "Unnamed Source")
        
        # Add category-specific information
        category = metadata.get("category", "")
        
        if category == "fund_knowledge":
            fund_ticker = metadata.get("fund_ticker", "")
            fund_provider = metadata.get("fund_provider", "")
            if fund_ticker and fund_provider:
                return f"{title} ({fund_provider}, {fund_ticker})"
            elif fund_ticker:
                return f"{title} ({fund_ticker})"
            else:
                return title
                
        elif category == "regulatory_tax":
            jurisdiction = metadata.get("jurisdiction", "")
            year = metadata.get("applicable_year", "")
            if jurisdiction and year:
                return f"{title} ({jurisdiction}, {year})"
            else:
                return title
                
        elif category == "market_patterns":
            timeframe = metadata.get("timeframe", "")
            if timeframe:
                return f"{title} ({timeframe})"
            else:
                return title
                
        else:
            return title 