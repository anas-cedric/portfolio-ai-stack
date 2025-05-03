# Financial AI Analysis Stack

A comprehensive stack for financial analysis using LangGraph, Claude, and pre-labeled datasets.

## 🚀 Features

- **Document Processing** - Optimize financial data for LLM context
  - Tabular data formatting
  - Compact number representation
  - Document summarization
  - Market-aware retrieval

- **Financial Dataset Integration** - Work with pre-labeled financial datasets
  - Automatic dataset type detection
  - Preprocessing and normalization
  - Dataset splitting (train/validation)

- **LangGraph Workflow** - Intelligent financial analysis pipeline
  - Market volatility-aware processing
  - Dynamic context adjustment
  - Comprehensive prompt engineering
  - LangSmith integration for tracking and prompt versioning

- **FastAPI Interface** - Simple API for interacting with the system
  - Dataset management
  - Market condition monitoring
  - Financial analysis queries

## 🛠️ Setup

### Prerequisites

- Python 3.9+
- [Anthropic API key](https://console.anthropic.com/) for Claude
- [LangSmith API key](https://smith.langchain.com/) (optional, for tracking and prompt versioning)

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/financial-ai-stack.git
   cd financial-ai-stack
   ```

2. Create a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install requirements
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables
   ```bash
   cp .env.example .env
   # Edit .env file to add your ANTHROPIC_API_KEY and optional LANGCHAIN_API_KEY
   ```

### Dataset Setup

1. Create directories for your datasets
   ```bash
   mkdir -p data/datasets/financial_statements
   mkdir -p data/datasets/market_data
   mkdir -p data/datasets/sentiment_labeled
   ```

2. Add your pre-labeled datasets to these directories
   - Supported formats: CSV, JSON, Parquet, Excel
   - Datasets will be auto-detected based on file structure and content

## 🔍 Usage

### Running the API

```bash
# Start the API server
cd src/api
python financial_analysis_api.py
```

The API will be available at http://localhost:8000 with interactive documentation at http://localhost:8000/docs.

### Using the Client

```bash
# List available datasets
python src/api/client_example.py datasets

# Check market conditions
python src/api/client_example.py market

# Analyze financial data
python src/api/client_example.py analyze "What is the trend in revenue growth?" --dataset financial_statements
```

### Using the Portfolio Advisor

```bash
# Run a single query
python portfolio_advisor.py "Should I adjust my portfolio given current market conditions?"

# Run with LangSmith integration
python portfolio_advisor.py "Should I buy more tech stocks?" -l

# Run in interactive mode with LangSmith tracking
python portfolio_advisor.py -i -l
```

### Example Queries

- "What is the trend in revenue growth for the past 4 quarters?"
- "Analyze the relationship between market sentiment and stock price movements"
- "Identify the top-performing sectors during high volatility periods"
- "Summarize the key financial ratios and their implications"
- "Given market volatility, how should I adjust my portfolio allocation?"

## 📁 Project Structure

```
financial-ai-stack/
├── data/
│   ├── datasets/            # Pre-labeled financial datasets
│   └── cache/               # Cached preprocessed datasets
├── src/
│   ├── api/                 # FastAPI implementation
│   ├── data/                # Data services (market, alpaca)
│   ├── data_integration/    # Dataset loading/preprocessing
│   ├── document_processing/ # Document formatting/summarization
│   │   ├── formatting/      # Tabular and number formatting
│   │   ├── market_aware/    # Volatility-aware retrieval
│   │   └── summarization/   # Document summarization
│   ├── langgraph_engine/    # LangGraph implementation
│   │   ├── langsmith_tracker.py    # LangSmith tracking
│   │   ├── langsmith_integration.py # LangSmith integration
│   │   ├── context_retriever.py    # Context retrieval
│   │   ├── decision_maker.py       # Decision making
│   │   └── graph.py                # Portfolio graph
│   └── workflow/            # LangGraph workflow
├── portfolio_advisor.py     # CLI tool with LangSmith integration
├── examples/                # Example usage scripts
├── README.md                # This file
├── README-LangSmith.md      # LangSmith integration details
└── requirements.txt         # Project dependencies
```

## 🔌 Integration with Voyage-Finance-2

The system is designed to work with the `voyage-finance-2` embeddings, which are already integrated in the core system. The document processing components enhance the context management capabilities of the embeddings by:

1. Optimizing formatting of financial data for token efficiency
2. Providing market-aware context retrieval based on volatility
3. Summarizing financial documents for improved context utilization

## 📚 Component Documentation

Each module has detailed documentation explaining its purpose and usage:

- [Document Processing](src/document_processing/README.md)
- [Data Integration](src/data_integration/README.md)
- [LangGraph Workflow](src/workflow/README.md)
- [API Interface](src/api/README.md)
- [LangSmith Integration](README-LangSmith.md)

## 🔄 LangSmith Integration

The system includes full LangSmith integration for tracking LangGraph runs and versioning prompts:

- **Run tracking** - Monitor and analyze each step of the LangGraph workflow
- **Prompt versioning** - Manage and switch between different prompt versions
- **Performance analytics** - Measure token usage and response quality

See [README-LangSmith.md](README-LangSmith.md) for detailed setup and usage instructions.

## 🔧 Advanced Configuration

The system can be configured in various ways:

- **Volatility Threshold**: Adjust in `FinancialAnalysisWorkflow` initialization
- **Document Summarization**: Configure length and style in `DocumentSummarizer`
- **Dataset Preprocessing**: Customize in `FinancialDatasetLoader`
- **LangSmith Project**: Configure project name and tracking options in `.env`

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

# Financial Analysis API

API for analyzing financial data using OpenAI and LangGraph.

## Features

- Financial data analysis with OpenAI o1 model
- Market-aware context adjustments
- Authentication using API keys
- Multiple dataset support
- Response caching with configurable TTL
- Numerical validation of financial analysis
- LangSmith integration for tracking and analytics

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your API keys
4. Run the API:
   ```
   python src/api/financial_analysis_api.py
   ```

## API Usage

### Authentication

All API endpoints require authentication using an API key passed in the `X-API-Key` header.

### Endpoints

- `POST /analyze` - Analyze financial data
- `GET /datasets` - List available datasets
- `GET /market_conditions` - Get current market conditions
- `GET /dataset/{dataset_name}/info` - Get information about a specific dataset
- `POST /cache/clear` - Clear the response cache

## Caching System

The API includes a response caching system to improve performance and reduce costs associated with repeated API calls.

### Cache Configuration

Configure caching in your `.env` file:

```
# Caching Configuration
CACHE_TYPE=in_memory  # Options: in_memory, redis
CACHE_TTL=3600  # Default TTL in seconds (1 hour)

# Redis Configuration (if using redis cache)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=  # Leave empty if no password
```

### Cache Types

- `in_memory`: Simple in-memory cache (default, not suitable for production)
- `redis`: Redis-based distributed cache (recommended for production)

### Dynamic TTL

The cache implements dynamic TTL (Time-To-Live) based on market volatility:
- During normal market conditions: Uses the configured CACHE_TTL
- During high volatility: Automatically reduces TTL to ensure fresh analysis

## Development

### Running Tests

```
pytest tests/
```

# Portfolio AI Stack

An AI-powered portfolio analysis and recommendation system.

## Features

- **Retrieval-Augmented Generation (RAG)** - Using Gemini 2.5 Pro Experimental to provide accurate, grounded financial advice
- **Embedding Pipeline** - Process and vectorize financial documents for semantic search
- **Context Retrieval** - Intelligent retrieval of financial knowledge from various sources
- **Vector Database Integration** - Store and search embeddings efficiently using Pinecone
- **Preset Financial Data** - Ready-to-use financial knowledge covering equities, funds, and investment principles

## Architecture

The system is built with the following components:

1. **Embedding Pipeline** (`src/pipelines/embedding_pipeline.py`) - Processes financial documents into embeddings
2. **Pinecone Storage** (`src/pipelines/pinecone_storage.py`) - Manages vector storage in Pinecone
3. **RAG System** (`src/rag/rag_system.py`) - Core RAG implementation with query processing and response generation
4. **Context Retrieval** (`src/context/context_retrieval_system.py`) - Multi-source context retrieval system
5. **Gemini Integration** (`src/utils/gemini_client.py`) - Client for Google's Gemini 2.5 Pro Experimental model
6. **Preset Financial Data** (`src/data/preset_financial_data.py`) - Pre-processed financial knowledge ready for use

## Preset Financial Data

The system includes comprehensive preset financial data to bypass the document processing pipeline:

- **S&P 500 and Major ETFs** - Information about major market indices and ETFs
- **Company Profiles** - Detailed information about companies like Apple (AAPL)
- **Investment Principles** - Topics like portfolio rebalancing, inflation hedging, and retirement strategies
- **Fixed Income Knowledge** - Bond duration, interest rates, and yield curve information

### Using Preset Data

To initialize and use the preset data:

```bash
# Set up the preset data and load it into Pinecone
python scripts/setup_preset_data.py

# With options
python scripts/setup_preset_data.py --clear --namespace my_namespace
```

### Preset Data Integration

The `PresetDataIntegration` class provides methods to:
- Load preset financial data to the vector database
- Generate deterministic mock embeddings for testing
- Search for similar documents using the preset data

```python
from src.pipelines.preset_data_integration import PresetDataIntegration

# Initialize
integration = PresetDataIntegration()

# Load data to vector database
stats = integration.load_data_to_vector_db(categories=["fund_knowledge"])

# Search for similar documents
results = integration.search_similar_documents(
    query="What is the S&P 500 index?",
    top_k=3
)
```

## Environment Setup

The system requires the following environment variables:

```
# Gemini API Key
GEMINI_API_KEY=your_gemini_api_key

# Pinecone Vector Database
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX_NAME=your_pinecone_index_name
```

## Testing

The system includes comprehensive tests that can run in two modes:

1. **Test Mode** - Uses mock responses for quick testing without API calls
   ```
   python src/tests/test_rag_pipeline.py
   ```

2. **API Mode** - Tests with real Gemini API calls (requires API key and respects rate limits)
   ```
   GEMINI_API_ENABLED=1 python src/tests/test_rag_pipeline.py
   ```

To test just the Gemini client:
```
python src/tests/test_gemini_client.py
```

## Model Information

The system uses Google's **Gemini 2.5 Pro Experimental** (`gemini-2.5-pro-exp-03-25`) model for:
- Generating financial advice and insights
- Creating hypothetical documents for improved retrieval
- Processing complex financial queries

Note: The Gemini API has rate limits that apply to the free tier.

## Portfolio AI Stack Components

The system consists of several integrated components:

### Frontend
- **Portfolio Advisor Web App**: A Next.js-based web application for collecting user preferences and generating portfolio recommendations
  - Located in `frontend/portfolio-advisor/`
  - Provides user-friendly interface for inputting financial goals and risk tolerance
  - Displays interactive portfolio recommendations with allocation visualization

### AI Components
- **LangGraph Portfolio Engine**: Context-aware portfolio decision engine using LangGraph
- **RAG System**: Retrieval Augmented Generation for financial context
- **Vector Database**: Pinecone for storing financial knowledge embeddings
- **LLM Integration**: Claude 3.7 and other models for financial reasoning

### Data Layer
- **Market Data**: Integration with Alpaca API for real-time market data
- **Financial Knowledge Base**: Structured financial knowledge and ETF data
- **Time-Series Database**: Using TimeScaleDB for historical price data

## Getting Started

### Running the Portfolio Advisor Frontend

1. Navigate to the frontend directory:
   ```bash
   cd frontend/portfolio-advisor
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

### Running the Backend Components

// ... existing code ... 