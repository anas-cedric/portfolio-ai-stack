#!/usr/bin/env python
"""
Demo script for the document processing pipeline.

This script demonstrates how to use the document processing pipeline
with the Unstructured processor for financial documents.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from pprint import pprint

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.document_processing.parsing_pipeline import DocumentParsingPipeline
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def demo_processor(file_path: str, output_file: str = None):
    """
    Demo the Unstructured processor on a document.
    
    Args:
        file_path: Path to the document to process
        output_file: Optional file to save the results
    """
    logger.info("=== Demo: Unstructured Document Processor ===")
    
    # Initialize pipeline with Unstructured processor
    pipeline = DocumentParsingPipeline()
    
    # Process the document
    logger.info(f"Processing document: {file_path}")
    result = pipeline.process_document(
        file_path=file_path,
        document_type="demo",
        category="test",
        financial_entity="DEMO"
    )
    
    # Print summary of results
    print("\nDocument Processing Results:")
    print(f"Success: {result['success']}")
    print(f"Number of elements: {len(result.get('elements', []))}")
    print(f"Number of chunks: {len(result.get('chunked_elements', []))}")
    print(f"Text length: {len(result.get('text', ''))}")
    print(f"Number of tables: {len(result.get('tables', [])) if result.get('tables') else 0}")
    
    # Print financial metrics if found
    if 'financial_metrics' in result and result['financial_metrics']:
        print("\nExtracted Financial Metrics:")
        pprint(result['financial_metrics'])
    
    # Print the first few elements to show structure
    if result.get('elements') and len(result['elements']) > 0:
        print("\nSample Elements:")
        for i, elem in enumerate(result['elements'][:3]):  # Show first 3 elements
            print(f"\nElement {i+1} (Type: {elem.get('type', 'Unknown')}):")
            if 'text' in elem:
                print(f"Text: {elem['text'][:100]}..." if len(elem['text']) > 100 else f"Text: {elem['text']}")
            if 'metadata' in elem:
                print(f"Metadata: {elem['metadata']}")
    
    # Save results if output file specified
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Results saved to: {output_file}")

def process_directory(directory_path: str, output_dir: str = None, recursive: bool = False):
    """
    Process all documents in a directory.
    
    Args:
        directory_path: Path to the directory containing documents
        output_dir: Directory to save the results
        recursive: Whether to process subdirectories
    """
    logger.info(f"=== Processing Directory: {directory_path} ===")
    
    # Initialize pipeline
    pipeline = DocumentParsingPipeline()
    
    # Process the directory
    results = pipeline.process_directory(
        directory_path=directory_path,
        recursive=recursive,
        document_type="batch_demo",
        category="test_batch"
    )
    
    # Print summary
    print(f"\nProcessed {len(results)} documents")
    successful = sum(1 for r in results if r.get('success', False))
    print(f"Successful: {successful}, Failed: {len(results) - successful}")
    
    # Save results if output directory specified
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True, parents=True)
        
        for i, result in enumerate(results):
            file_name = result.get('metadata', {}).get('file_name', f"document_{i}")
            output_file = output_path / f"{file_name}_processed.json"
            
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
        
        logger.info(f"Results saved to directory: {output_dir}")

def main():
    """Main function to run the demo."""
    parser = argparse.ArgumentParser(description="Demo the document processing pipeline")
    
    # Create mutually exclusive group for file or directory
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", "-f", help="Path to a document to process")
    group.add_argument("--directory", "-d", help="Path to a directory of documents to process")
    
    # Add other arguments
    parser.add_argument("--output", "-o", help="File or directory to save the results")
    parser.add_argument("--recursive", "-r", action="store_true", help="Process subdirectories recursively")
    
    args = parser.parse_args()
    
    # Process a single file
    if args.file:
        # Validate file exists
        if not Path(args.file).exists():
            parser.error(f"File not found: {args.file}")
        
        demo_processor(args.file, args.output)
    
    # Process a directory
    elif args.directory:
        # Validate directory exists
        if not Path(args.directory).is_dir():
            parser.error(f"Directory not found: {args.directory}")
        
        process_directory(args.directory, args.output, args.recursive)

if __name__ == "__main__":
    main() 