#!/usr/bin/env python3
"""
Batch Processing Script for Financial Documents

This script processes financial documents from specified directories,
generates embeddings using the Voyage finance-2 model, and stores them
in the vector database for retrieval.

Usage:
    python batch_embed_financial_docs.py --data-dir /path/to/financial/docs
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.knowledge.voyage_embeddings import VoyageFinanceEmbeddings
from src.knowledge.vector_store import PineconeManager
from src.document_processing.financial_processor import FinancialDocumentProcessor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/batch_embed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Batch process financial documents for vector database storage"
    )
    
    parser.add_argument(
        "--data-dir", 
        type=str, 
        default="data/financial_documents",
        help="Directory containing financial documents to process"
    )
    
    parser.add_argument(
        "--recursive", 
        action="store_true",
        help="Process directories recursively"
    )
    
    parser.add_argument(
        "--chunk-size", 
        type=int, 
        default=1024,
        help="Maximum chunk size in characters"
    )
    
    parser.add_argument(
        "--chunk-overlap", 
        type=int, 
        default=128,
        help="Overlap between chunks in characters"
    )
    
    parser.add_argument(
        "--max-workers", 
        type=int, 
        default=4,
        help="Maximum number of parallel workers"
    )
    
    parser.add_argument(
        "--log-level", 
        type=str, 
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level"
    )
    
    parser.add_argument(
        "--output", 
        type=str, 
        default="",
        help="Output file for processing statistics (JSON format)"
    )
    
    return parser.parse_args()


def ensure_dir_exists(path):
    """Ensure a directory exists, creating it if necessary."""
    Path(path).mkdir(parents=True, exist_ok=True)


def main():
    """Main entry point for the script."""
    args = parse_arguments()
    
    # Set log level from arguments
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Ensure logs directory exists
    ensure_dir_exists("logs")
    
    # Log script start
    logger.info(f"Starting batch document processing with args: {args}")
    
    try:
        # Initialize components with proper error handling
        try:
            logger.info("Initializing Voyage Finance embeddings client...")
            embedding_client = VoyageFinanceEmbeddings(
                max_retries=3, 
                retry_delay=1.0, 
                batch_size=10
            )
        except Exception as e:
            logger.error(f"Failed to initialize embeddings client: {e}")
            return 1
        
        try:
            logger.info("Initializing Pinecone vector store...")
            vector_store = PineconeManager()
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            return 1
        
        # Initialize document processor
        processor = FinancialDocumentProcessor(
            embedding_client=embedding_client,
            vector_store=vector_store,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            max_workers=args.max_workers
        )
        
        # Process documents
        start_time = datetime.now()
        logger.info(f"Starting processing of documents in {args.data_dir}...")
        
        try:
            stats = processor.process_directory(
                directory_path=args.data_dir,
                recursive=args.recursive
            )
            
            # Add additional stats
            stats["processing_time_seconds"] = (datetime.now() - start_time).total_seconds()
            stats["processing_date"] = datetime.now().isoformat()
            stats["arguments"] = vars(args)
            
            # Summarize processing results
            logger.info(f"Processing completed in {stats['processing_time_seconds']:.2f} seconds")
            logger.info(f"Files processed: {stats['successfully_processed']}/{stats['total_files']}")
            logger.info(f"Chunks created: {stats['chunks_created']}")
            logger.info(f"Total tokens: {stats['total_tokens']}")
            
            # Check for failures
            if stats["failed"] > 0:
                logger.warning(f"Failed to process {stats['failed']} files")
                for failure in stats["failures"]:
                    logger.warning(f"  - {failure['file']}: {failure['error']}")
            
            # Write stats to output file if specified
            if args.output:
                output_path = args.output
                ensure_dir_exists(os.path.dirname(output_path))
                with open(output_path, "w") as f:
                    json.dump(stats, f, indent=2)
                logger.info(f"Wrote processing statistics to {output_path}")
            
            return 0
            
        except Exception as e:
            logger.error(f"Error during document processing: {e}", exc_info=True)
            return 1
            
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main()) 