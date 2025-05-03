# ETF Data Collection Module

This module provides tools for collecting, managing, and ingesting ETF (Exchange-Traded Fund) data into a knowledge base for retrieval-augmented generation (RAG) applications.

## Components

1. **ETF Registry** (`src/data/etf_registry.py`): Manages a database of ETFs with metadata, including tickers, names, asset classes, and providers.

2. **ETF Data Collector** (`src/data/etf_collector.py`): Collects ETF data from Alpaca, processes it, and prepares it for storage in the knowledge base.

3. **Knowledge Base Integration**: Adds ETF data to a Pinecone vector database for use in RAG systems.

## Scripts

- **`etf_registry_test.py`**: Tests the ETF Registry functionality for managing ETF metadata.
- **`etf_collector_test.py`**: Tests the ETF Data Collector for fetching data on specific ETFs.
- **`ingest_etf_knowledge.py`**: Bulk ingestion tool for adding multiple ETFs to the knowledge base.
- **`add_fund_knowledge.py`**: Helper module for adding ETF knowledge items to Pinecone.

## Usage

### Managing ETF Registry

```bash
# Seed initial ETF data
./etf_registry_test.py --seed

# List all ETFs in registry
./etf_registry_test.py --list

# Add a new ETF
./etf_registry_test.py --add-etf --ticker SPY --name "SPDR S&P 500 ETF Trust" --asset-class equity --provider "State Street"

# Export registry to JSON
./etf_registry_test.py --export etfs.json
```

### Collecting ETF Data

```bash
# Collect data for a specific ETF
./etf_collector_test.py --ticker SPY

# Collect data for multiple ETFs
./etf_collector_test.py --tickers "SPY,QQQ,IWM"

# Update all ETFs in registry
./etf_collector_test.py --update-all

# Convert to knowledge items
./etf_collector_test.py --ticker SPY --to-knowledge

# Save output to file
./etf_collector_test.py --ticker SPY --output spy_data.json
```

### Bulk Ingestion to Knowledge Base

```bash
# Ingest ETFs from a JSON file
./ingest_etf_knowledge.py --file etf_tickers.json

# Ingest all ETFs from registry
./ingest_etf_knowledge.py --all

# Limit the number of ETFs to ingest
./ingest_etf_knowledge.py --all --limit 10

# Dry run (don't actually add to knowledge base)
./ingest_etf_knowledge.py --all --dry-run

# Save collected data to file
./ingest_etf_knowledge.py --all --output collected_etfs.json
```

## Environment Variables

Required environment variables:

```
# Alpaca API credentials
ALPACA_DATA_API_KEY=your_api_key
ALPACA_DATA_API_SECRET=your_api_secret
ALPACA_BASE_URL=https://data.alpaca.markets/v2

# Pinecone vector database
PINECONE_API_KEY=your_api_key
PINECONE_ENVIRONMENT=your_environment
PINECONE_INDEX_NAME=your_index_name

# Optional: Supabase for registry storage
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
```

## Data Flow

1. ETF metadata is stored in the ETF Registry
2. ETF Data Collector fetches current data for ETFs
3. Data is processed and converted to knowledge items
4. Knowledge items are added to Pinecone vector database
5. RAG system queries knowledge base for ETF information 