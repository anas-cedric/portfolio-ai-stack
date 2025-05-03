#!/usr/bin/env python3
"""
Simple script to check the implemented document processing modules.
"""

import os
import sys

# Add the current directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_modules():
    """Check all implemented document processing modules."""
    modules = [
        "src.document_processing",
        "src.document_processing.formatting",
        "src.document_processing.formatting.tabular_formatter",
        "src.document_processing.formatting.number_formatter",
        "src.document_processing.summarization",
        "src.document_processing.summarization.document_summarizer",
        "src.document_processing.market_aware",
        "src.document_processing.market_aware.volatility_aware_retriever"
    ]
    
    print("Checking document processing modules:")
    print("="*50)
    
    for module_name in modules:
        try:
            module = __import__(module_name, fromlist=[""])
            print(f"✅ Successfully imported: {module_name}")
            
            # If it's a main component, show the class names
            if module_name.endswith("tabular_formatter"):
                print(f"   - Contains: TabularFormatter")
            elif module_name.endswith("number_formatter"):
                print(f"   - Contains: CompactNumberFormatter")
            elif module_name.endswith("document_summarizer"):
                print(f"   - Contains: DocumentSummarizer")
            elif module_name.endswith("volatility_aware_retriever"):
                print(f"   - Contains: VolatilityAwareRetriever")
                
        except ImportError as e:
            print(f"❌ Failed to import: {module_name}")
            print(f"   Error: {str(e)}")
    
    print("\nFile Structure:")
    print("="*50)
    os.system('find src/document_processing -type f | sort')
    
    print("\nREADME Content:")
    print("="*50)
    readme_path = "src/document_processing/README.md"
    if os.path.exists(readme_path):
        with open(readme_path, "r") as f:
            readme_content = f.read()
            # Print first 10 lines
            print("\n".join(readme_content.split("\n")[:10]))
            print("... (see complete README at src/document_processing/README.md) ...")
    else:
        print("README file not found")

if __name__ == "__main__":
    check_modules() 