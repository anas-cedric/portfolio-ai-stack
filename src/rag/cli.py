"""
Command-line interface for the RAG system.

This module provides a simple CLI tool for asking investment questions
and getting answers based on the fund knowledge base.
"""

import os
import sys
import json
import argparse
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

from src.rag.query_processor import QueryProcessor
from src.rag.retriever import Retriever
from src.rag.response_generator import ResponseGenerator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class FundRagCLI:
    """CLI tool for the fund knowledge RAG system."""
    
    def __init__(self, log_dir: str = "logs"):
        """
        Initialize the CLI tool.
        
        Args:
            log_dir: Directory to store query logs
        """
        self.query_processor = QueryProcessor()
        self.retriever = Retriever(embedding_client_type="voyage")
        self.response_generator = ResponseGenerator()
        
        # Set up logging directory
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
    
    def process_query(self, query: str, verbose: bool = False) -> Dict[str, Any]:
        """
        Process a query and return the response.
        
        Args:
            query: The user query
            verbose: Whether to print verbose debug output
            
        Returns:
            Response dictionary with answer and metadata
        """
        logger.info(f"Processing query: {query}")
        
        try:
            # Process the query
            processed_query = self.query_processor.process_query(query)
            
            # Log the processed query
            if verbose:
                logger.info(f"Processed query: {json.dumps(processed_query, indent=2)}")
                print(f"\nQuery type: {processed_query['query_type']}")
                if processed_query.get('metadata_filters'):
                    print(f"Metadata filters: {processed_query['metadata_filters']}")
                print(f"Entities: {processed_query['entities']}")
                print(f"Expanded query: {processed_query['expanded_query']}\n")
            
            # Retrieve relevant knowledge
            retrieval_results = self.retriever.retrieve(
                query, 
                processed_query,
                top_k=5
            )
            
            # Log retrieved contexts
            if verbose:
                logger.info(f"Retrieved {len(retrieval_results['contexts'])} contexts")
                print("\nRetrieved sources:")
                for i, source in enumerate(retrieval_results['sources']):
                    print(f"  {i+1}. {source} (score: {retrieval_results['relevance_scores'][i]:.3f})")
                print()
            
            # Generate response
            response = self.response_generator.generate_response(
                query,
                processed_query,
                retrieval_results
            )
            
            # Log the response
            self._log_interaction(query, processed_query, retrieval_results, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            return {"answer": f"Error: {str(e)}", "error": str(e)}
    
    def _log_interaction(
        self, 
        query: str, 
        processed_query: Dict[str, Any],
        retrieval_results: Dict[str, Any],
        response: Dict[str, Any]
    ) -> None:
        """
        Log the interaction to a file.
        
        Args:
            query: The original query
            processed_query: The processed query
            retrieval_results: Results from retrieval
            response: The generated response
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(self.log_dir, f"query_{timestamp}.json")
        
        # Prepare the log data
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "processed_query": {
                "query_type": processed_query.get("query_type", "").value,
                "entities": processed_query.get("entities", {}),
                "metadata_filters": processed_query.get("metadata_filters", {})
            },
            "retrieval": {
                "sources": retrieval_results.get("sources", []),
                "relevance_scores": retrieval_results.get("relevance_scores", [])
            },
            "response": {
                "answer": response.get("answer", ""),
                "model": response.get("model", ""),
                "token_usage": response.get("token_usage", {})
            }
        }
        
        # Write to file
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
            
        logger.info(f"Interaction logged to {log_file}")

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Fund Knowledge RAG System")
    parser.add_argument("query", nargs="*", help="The query to process")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")
    args = parser.parse_args()
    
    cli = FundRagCLI()
    
    if args.interactive:
        print("Fund Knowledge RAG System")
        print("Type 'exit' to quit")
        print("-" * 50)
        
        while True:
            query = input("\nEnter your question: ")
            if query.lower() in ["exit", "quit"]:
                break
                
            response = cli.process_query(query, verbose=args.verbose)
            print("\n" + "=" * 50)
            print(response["answer"])
            print("=" * 50)
            
            # Ask for feedback
            feedback = input("\nWas this response helpful? (y/n): ")
            if feedback.lower() == 'n':
                improvement = input("How could the response be improved? ")
                # In a production system, this feedback would be stored
                print("Thank you for your feedback!")
    else:
        if not args.query:
            parser.print_help()
            return
            
        query = " ".join(args.query)
        response = cli.process_query(query, verbose=args.verbose)
        print(response["answer"])

if __name__ == "__main__":
    main() 