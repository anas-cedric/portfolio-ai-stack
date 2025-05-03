# Portfolio AI Stack - Current Architecture

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            External Data Sources                                 │
│                                                                                 │
│  ┌─────────────┐          ┌────────────┐         ┌──────────────┐  ┌─────────┐  │
│  │  Alpaca API │          │  Fed APIs  │         │  SEC EDGAR   │  │User Data│  │
│  │ Market Data │          │ Economic   │         │  Financial   │  │Portfolio │  │
│  └──────┬──────┘          └─────┬──────┘         └──────┬───────┘  └────┬────┘  │
└─────────┼───────────────────────┼────────────────────────┼────────────────┼─────┘
          │                        │                        │               │
          ▼                        ▼                        ▼               │
┌─────────────────────────────────────────────────────────────────────┐    │
│                         Data Ingestion Layer                         │    │
│                                                                     │    │
│  ┌─────────────────┐    ┌────────────────┐    ┌───────────────┐     │    │
│  │ Market Pipeline │    │ Economic Data  │    │   Document    │     │    │
│  │   market_data   │    │    Pipeline    │    │  Processing   │     │    │
│  └────────┬────────┘    └───────┬────────┘    └───────┬───────┘     │    │
└───────────┼───────────────────────┼──────────────────┼──────────────┘    │
            │                       │                  │                    │
            ▼                       ▼                  ▼                    │
┌───────────────────────────────────────────────────────────────┐          │
│                      Data Storage Layer                       │          │
│                                                               │          │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐      │          │
│  │  Pinecone   │     │  Supabase   │     │ TimeScaleDB │      │          │
│  │   Vector    │     │ User Data &  │     │ Time-Series │      │          │
│  │  Database   │     │   State     │     │    Data     │      │          │
│  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘      │          │
└─────────┼──────────────────────┼─────────────────┼─────────────┘          │
          │                      │                 │                         │
          ▼                      │                 │                         │
┌─────────────────────────────────────────────────────────────┐             │
│                    Context Retrieval Layer                  │             │
│                                                             │             │
│  ┌───────────────┐     ┌───────────────┐     ┌────────────┐ │   ┌─────────────────┐
│  │Query Processor│     │   Retriever   │     │  Context   │ │   │                 │
│  │ Classification│────▶│ Vector Search │────▶│ Retriever  │ │   │ Portfolio       │
│  │Entity Extract │     │Hybrid Ranking │     │User-Aware  │ │   │ Advisor CLI     │
│  └───────────────┘     └───────────────┘     └──────┬─────┘ │   │                 │
└─────────────────────────────────────────────────────┼───────┘   │  User Interface │
                                                      │           │                 │
                                                      ▼           │      Query      │
┌─────────────────────────────────────────────────────────────┐   │       │        │
│                      LangGraph Engine                       │   │       │        │
│                                                             │   │       │        │
│  ┌────────────────┐                ┌────────────────┐       │   │       │        │
│  │ Portfolio Graph│                │ Decision Maker │       │   │       │        │
│  │ Orchestration  │◀───────────▶   │   Claude AI    │       │   │       │        │
│  │ Error Handling │                │   Reasoning    │       │   │       │        │
│  └───────┬────────┘                └────────────────┘       │   │       │        │
└──────────┼────────────────────────────────────────────────────┘   │       │        │
           │                                                        │       │        │
           └───────────────────── Portfolio Decision ──────────────▶│       ◀────────┘
                                                                    └─────────────────┘
```

## Component Descriptions

### External Data Sources
- **Alpaca API**: Provides market data (OHLCV, order book, trade volume, asset metadata)
- **Fed APIs**: Economic indicators (interest rates, inflation metrics, employment data)
- **SEC EDGAR**: Financial documents (fund prospectuses, annual reports, filings)
- **User Data**: Investment goals, risk tolerance, preferences

### Data Ingestion Layer
- **Market Pipeline**: Processes market data from various sources
- **Economic Pipeline**: Collects and standardizes economic indicators
- **Document Processing**: ETL for extracting structured data from documents

### Data Storage Layer
- **Pinecone**: Vector database storing embeddings for knowledge retrieval
- **Supabase**: User profiles, portfolio state, transaction history
- **TimeScaleDB**: Time-series data for historical prices and indicators

### Context Retrieval Layer
- **Query Processor** (`src/rag/query_processor.py`): Analyzes user queries, extracts entities
- **Retriever** (`src/rag/retriever.py`): Performs vector search with hybrid ranking
- **Context Retriever** (`src/langgraph_engine/context_retriever.py`): Enhances context with user profile, portfolio awareness

### LangGraph Engine
- **Portfolio Graph** (`src/langgraph_engine/graph.py`): Orchestrates the workflow, manages state
- **Decision Maker** (`src/langgraph_engine/decision_maker.py`): Claude-powered reasoning for portfolio decisions

### User Interface
- **Portfolio Advisor CLI** (`portfolio_advisor.py`): Command-line interface for user interaction

## Key Data Flows

1. **User Query Flow**:
   ```
   User → CLI → Query Processor → Retriever → Context Retriever → Portfolio Graph → Decision Maker → CLI → User
   ```

2. **Market Data Flow**:
   ```
   Alpaca API → Market Pipeline → Pinecone/TimeScaleDB → Context Retriever → Portfolio Graph
   ```

3. **Economic Data Flow**:
   ```
   Fed APIs → Economic Pipeline → Pinecone/TimeScaleDB → Context Retriever → Portfolio Graph
   ```

4. **Document Data Flow**:
   ```
   SEC EDGAR → Document Processing → Pinecone → Retriever → Context Retriever → Portfolio Graph
   ```

## Advanced Features

- **User Profile Enhancement**: Context retrieval adapts based on user risk tolerance and goals
- **Portfolio-Aware Context**: Existing holdings influence the retrieval process
- **Market State Sensitivity**: Volatility affects retrieval patterns
- **LangGraph Orchestration**: State-based workflow with error handling
- **Structured Decision Making**: Generates actionable recommendations with confidence scores 