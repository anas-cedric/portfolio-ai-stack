# Financial Document Processing System

## Overview

The Financial Document Processing System is a comprehensive pipeline for extracting structured information from financial documents, including prospectuses, annual reports, fact sheets, and more. The system uses the Unstructured library to process various document formats and provides a unified interface for document ingestion, processing, and embedding generation.

## Architecture

The system consists of several key components:

### Document Processor

**Unstructured Processor**
- Based on the Unstructured library
- Extracts text, tables, and metadata from various document formats
- OCR capabilities for image-based documents
- Text chunking for embedding generation
- Table extraction
- Automatic format detection

### Parsing Pipeline

The `DocumentParsingPipeline` orchestrates the document processing workflow:
- Document ingestion from various formats
- Text extraction and preprocessing
- Financial metadata extraction
- Chunking for embedding generation
- Preparation for storage in vector database

### Metadata Extraction

The `FinancialMetadataExtractor` identifies and extracts specific financial metadata:
- Financial entities (companies, funds, tickers)
- Financial metrics (AUM, expense ratios, returns)
- Date and time period identification
- Regulatory filing types (10-K, 10-Q, prospectus)

## Setup

### Prerequisites

Install the required dependencies:

```bash
pip install unstructured unstructured-inference pdfminer.six pdf2image pytesseract python-docx python-pptx pi-heif
```

For OCR support, make sure Tesseract is installed:
- On macOS: `brew install tesseract`
- On Ubuntu: `apt-get install tesseract-ocr`
- On Windows: Download and install from [tesseract-ocr](https://github.com/UB-Mannheim/tesseract/wiki)

## Usage

### Basic Usage

```python
from src.document_processing.parsing_pipeline import DocumentParsingPipeline

# Initialize the pipeline
pipeline = DocumentParsingPipeline()

# Process a single document
result = pipeline.process_document(
    file_path="path/to/document.pdf",
    document_type="prospectus",
    category="ETF",
    financial_entity="SPY"
)

# Process a directory of documents
results = pipeline.process_directory(
    directory_path="path/to/documents/",
    recursive=True,
    document_type="annual_report"
)
```

### Command-Line Demo Tool

The system includes a command-line tool for demonstrating document processing:

```bash
# Process a single document
python src/scripts/demo_document_processing.py --file path/to/document.pdf

# Process all documents in a directory
python src/scripts/demo_document_processing.py --directory path/to/documents/ --recursive
```

## Output Format

The document processing results include:

```json
{
  "metadata": {
    "file_name": "example.pdf",
    "document_type": "prospectus",
    "category": "ETF",
    "financial_entity": "SPY",
    "processed_by": "unstructured"
  },
  "elements": [
    {
      "type": "Text",
      "text": "Example text content",
      "metadata": {
        "page_number": 1
      }
    },
    {
      "type": "Table",
      "text": "Example table content",
      "metadata": {
        "page_number": 2,
        "rows": 5,
        "columns": 3
      }
    }
  ],
  "chunked_elements": [...],
  "text": "Full document text...",
  "tables": [...],
  "financial_metrics": {
    "expense_ratio": 0.09,
    "aum": 500000000000,
    "returns": {
      "value": 10.5,
      "period": "1-year"
    }
  },
  "embedding_data": [...],
  "success": true,
  "error": null
}
```

## Features

### Document Format Support
- PDF files
- Word documents (DOCX)
- PowerPoint presentations (PPTX)
- HTML files
- Plain text files
- Excel spreadsheets (limited support)

### Processing Capabilities
- Text extraction with structural awareness
- Table extraction and formatting
- OCR for scanned documents
- Text chunking for efficient embedding
- Basic financial metric identification
- Document metadata extraction
- Error handling and recovery

## Integration with RAG System

The document processing system integrates with the RAG (Retrieval Augmented Generation) system:

1. Documents are processed and chunked
2. Embedding data is generated for each chunk
3. Embeddings are stored in Pinecone vector database
4. RAG retrieval system uses these embeddings for context retrieval

## Error Handling

The processor includes robust error handling:
- File not found errors
- Processing failures
- Invalid document formats
- OCR failures

Errors are captured in the result with detailed error messages.

## Performance Considerations

- **Large Documents**: Documents over 100 pages may need special handling
- **Memory Usage**: Processing large batches may require significant memory
- **OCR Processing**: OCR significantly increases processing time

## Future Improvements

- Add document classification to automatically determine document type
- Implement more sophisticated financial metric extraction
- Add support for more financial document types
- Implement caching for processed documents
- Enhance table extraction accuracy
- Improve OCR capabilities for financial statements 