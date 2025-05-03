# Knowledge Management System

This module implements a vector database using Pinecone to store and retrieve fund knowledge embeddings.

## Overview

The knowledge management system stores the following types of information:

- **Fund Knowledge**: Information about ETFs, index funds, their characteristics, etc.
- **Investment Principles**: Modern Portfolio Theory, factor investing, diversification strategies, etc.
- **Regulatory and Tax Rules**: Tax-loss harvesting guidelines, wash sale rules, tax efficiency, etc.
- **Historical Market Patterns**: Asset class correlations, market behaviors, etc.

## Architecture

The system uses Pinecone as a vector database to store embeddings of knowledge documents. The architecture follows these principles:

1. **Structured Knowledge**: All knowledge is categorized and stored with metadata for efficient retrieval
2. **Vector Representation**: Text is converted to embeddings for semantic search
3. **Extensible Design**: Easy to add new knowledge categories or embedding models

## Usage

### Basic Usage

```python
from src.knowledge import PineconeManager, KnowledgeCategory, FundKnowledge, generate_unique_id

# Initialize the manager
pinecone_mgr = PineconeManager()

# Create a knowledge item
fund_info = FundKnowledge(
    id=generate_unique_id("fund"),
    title="Vanguard Total Stock Market ETF",
    content="Detailed information about VTI...",
    category=KnowledgeCategory.FUND_KNOWLEDGE,
    fund_ticker="VTI"
)

# Generate an embedding (placeholder for now, will use Voyage AI later)
from src.knowledge import generate_placeholder_embedding
embedding = generate_placeholder_embedding()

# Store in Pinecone
pinecone_mgr.upsert_vectors(
    vectors=[embedding],
    ids=[fund_info.id],
    metadata=[fund_info.to_metadata()]
)

# Query similar documents
query_embedding = generate_placeholder_embedding()  # In production: from user question
results = pinecone_mgr.query(query_vector=query_embedding, top_k=3)
```

### Future Integration with Voyage AI

In the future, this system will be integrated with Voyage AI's finance-2 model for high-quality financial document embeddings:

```python
# Future implementation - not yet available
from voyage_embeddings import VoyageEmbeddings

# Initialize the Voyage AI client
voyage_client = VoyageEmbeddings(api_key="your-voyage-api-key")

# Generate embeddings
embedding = voyage_client.embed(text=fund_info.content, model="voyage-finance-2")

# Use the embeddings with Pinecone
pinecone_mgr.upsert_vectors(
    vectors=[embedding],
    ids=[fund_info.id],
    metadata=[fund_info.to_metadata()]
)
```

## Environment Setup

The following environment variables are required:

```
PINECONE_API_KEY=your-api-key
PINECONE_ENVIRONMENT=your-environment
PINECONE_INDEX_NAME=fund-knowledge
```

## Running the Example

An example script is provided to demonstrate the functionality:

```bash
python -m src.knowledge.example
``` 