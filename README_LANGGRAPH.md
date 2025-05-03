# LangGraph-based Portfolio Decision System

This module implements a context-aware portfolio decision system using LangGraph.

## Overview

Traditional portfolio management systems typically follow a data flow like:

```
Data → Feature Engineering → ML Models → Portfolio Decisions
```

Our new approach leverages LangGraph to create a more context-aware system:

```
Data → Context Retrieval → O1 with LangGraph → Portfolio Decisions
```

This approach allows for more reasoned decision-making that incorporates multiple data sources, user profiles, and market conditions.

## Architecture

The system consists of the following components:

1. **Context Retriever**: Retrieves relevant information based on the user's query and state
2. **Decision Maker**: Makes portfolio decisions based on retrieved context
3. **LangGraph Workflow**: Orchestrates the flow between context retrieval and decision making

```
Query → [Context Retriever] → Contexts → [Decision Maker] → Portfolio Decision
```

## Data Sources

The system integrates multiple data sources:

- Market data from Alpaca API
- Economic indicators from FRED, BLS, and BEA
- Financial documents from SEC EDGAR
- Fund prospectuses and reports
- User profile data and portfolio holdings

## Usage

### Command Line Interface

The `portfolio_advisor.py` script provides a command-line interface to interact with the system:

```bash
# Basic query
python portfolio_advisor.py "Should I buy more AAPL?"

# Interactive mode
python portfolio_advisor.py -i

# Use a specific user profile
python portfolio_advisor.py -p profiles/conservative.json "What bonds should I add to my portfolio?"

# Verbose mode
python portfolio_advisor.py -v "How should I rebalance my portfolio?"
```

### User Profiles

You can create custom user profiles as JSON files in the `profiles/` directory. See examples:
- `profiles/conservative.json`
- `profiles/aggressive.json`

### Programmatic Usage

```python
from src.langgraph_engine.graph import run_portfolio_graph

result = run_portfolio_graph(
    query="Should I invest in technology stocks?",
    user_profile=user_profile,
    portfolio_data=portfolio_data,
    market_state=market_state
)

print(result["decision"])
print(result["recommendations"])
```

## Dependencies

- LangGraph: Agent orchestration framework
- Anthropic Claude: AI reasoning engine
- Pinecone: Vector database for context storage
- Voyage AI: Embeddings for semantic search

## Configuration

Environment variables are used for API keys and configuration:

```
ANTHROPIC_API_KEY=...
PINECONE_API_KEY=...
VOYAGE_API_KEY=...
ALPACA_DATA_API_KEY=...
```

See `.env.example` for required variables.

## Extending the System

### Adding New Data Sources

To add a new data source:
1. Update the `ContextRetriever` to incorporate the new data
2. Ensure the data is properly formatted for the decision maker
3. Update the system prompt if needed to handle the new data source

### Customizing Decision Logic

The decision logic can be customized by modifying:
1. The system prompt in `DecisionMaker._get_system_prompt()`
2. The prompt template in `DecisionMaker._create_prompt()`
3. The LangGraph workflow in `create_portfolio_graph()`

## Benefits Over Traditional Approach

- **Contextual Understanding**: Better integration of diverse information sources
- **Reasoning**: Can explain decisions and provide rationale
- **Adaptability**: Can handle novel questions and market conditions
- **Personalization**: Deeply integrates user profile and preferences
- **Transparency**: Provides sources and confidence levels for decisions 