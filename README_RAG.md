# Fund Knowledge RAG System

A Retrieval Augmented Generation (RAG) system for answering questions about funds, investment strategies, tax implications, and more, built with Claude 3.7 and Pinecone.

## Features

- **Query Understanding**: Automatically classifies different types of investment questions
- **Enhanced Retrieval**: Uses hybrid retrieval combining semantic and keyword search
- **Intelligent Chunking**: Optimizes context handling for long documents
- **Claude 3.7 Integration**: Generates high-quality responses with source attribution
- **CLI Interface**: Simple command-line tool for asking questions

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set up environment variables in `.env`:
   ```
   PINECONE_API_KEY=your_pinecone_api_key
   PINECONE_ENVIRONMENT=your_pinecone_environment
   PINECONE_INDEX_NAME=fund-knowledge
   VOYAGE_API_KEY=your_voyage_api_key  # For embeddings
   ANTHROPIC_API_KEY=your_anthropic_api_key  # For Claude 3.7
   ```

3. Make sure you have populated the Pinecone vector database with fund knowledge. You can use the `add_fund_knowledge.py` script for this.

## Usage

### Command-line Interface

To ask a question from the command line:

```bash
python fund_rag.py "What is the expense ratio for VOO?"
```

For interactive mode (continuous Q&A session):

```bash
python fund_rag.py -i
```

For verbose output (showing query processing details):

```bash
python fund_rag.py -v "Compare VOO and SPY"
```

### Query Examples

- Fund information: "What is VOO and what's its expense ratio?"
- Fund comparison: "Compare VOO and SPY in terms of performance and fees"
- Tax questions: "How are ETF distributions taxed in the US?"
- Investment strategies: "What is dollar-cost averaging and why is it recommended?"
- Market trends: "What typically happens to bonds when interest rates rise?"

## Architecture

The system consists of three main components:

1. **Query Processor**: Analyzes and enhances user queries
   - Query classification (fund info, comparison, tax, strategy, market)
   - Entity extraction (tickers, time periods, asset classes)
   - Query expansion for better retrieval

2. **Retriever**: Finds relevant information from the knowledge base
   - Metadata filtering based on query type
   - Hybrid retrieval (semantic + keyword)
   - Document chunking and selection

3. **Response Generator**: Creates high-quality answers using Claude 3.7
   - Specialized prompts for different query types
   - Context structuring with source attribution
   - Answer formatting with relevant financial disclaimers

## Feedback and Logging

The system logs all interactions to the `logs/` directory, including:
- Original query
- Processed query details (type, entities, filters)
- Retrieved sources and relevance scores
- Generated response and token usage

In interactive mode, the system also collects user feedback on response quality.

## Development

To extend the system:
- Add new query types in `query_processor.py`
- Enhance retrieval strategies in `retriever.py`
- Improve prompt templates in `response_generator.py`
- Add new feedback mechanisms in `cli.py` 