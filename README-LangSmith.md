# LangSmith Integration for Portfolio AI Stack

This document explains how to set up and use the LangSmith integration with the Portfolio AI Stack, enabling:

- **Prompt versioning**: Track and manage different versions of prompts
- **Run tracking**: Monitor and analyze the performance of LangGraph components
- **Performance analytics**: Get insights into token usage and performance metrics

## Setup Instructions

### 1. Get a LangSmith API Key

1. Sign up for LangSmith at [smith.langchain.com](https://smith.langchain.com)
2. Create a new project (e.g., "portfolio-advisor")
3. In your profile settings, generate an API key

### 2. Add LangSmith Credentials to .env

Add the following to your `.env` file:

```
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_PROJECT=portfolio-advisor
```

### 3. Install Required Packages

```bash
pip install langsmith
```

## Using LangSmith with the Portfolio Advisor

### Command Line Interface

Run the portfolio advisor with LangSmith tracking:

```bash
# Enable LangSmith tracking for a single query
python portfolio_advisor.py "Should I invest in technology stocks?" -l

# Run in interactive mode with LangSmith tracking
python portfolio_advisor.py -i -l
```

### Interactive Mode Commands

When running in interactive mode with LangSmith enabled:

- `prompts` - List all available prompt versions
- `set prompt [name] [version]` - Switch to a different prompt version
- Other standard commands work as usual

### Programmatic Usage

```python
from src.langgraph_engine.langsmith_integration import init_langsmith, get_langsmith_integration

# Initialize LangSmith (do this once at the beginning of your application)
init_langsmith(
    project_name="portfolio-advisor",
    enable_tracking=True,
    enable_prompt_versioning=True
)

# Get the LangSmith integration instance
langsmith = get_langsmith_integration()

# Run the tracked portfolio graph
result = langsmith.run_tracked_portfolio_graph(
    query="Should I buy more tech stocks?",
    user_profile=user_profile,
    portfolio_data=portfolio_data
)

# Get available prompt versions
versions = langsmith.get_prompt_versions("decision_maker")

# Create a new prompt version
version_id = langsmith.register_new_prompt_version(
    prompt_name="decision_maker", 
    prompt_template="Your new prompt template here",
    version="v2",  # Optional, will generate timestamp if not provided
    description="Updated prompt with better risk assessment"
)

# Set active prompt version
langsmith.set_active_prompt_version("decision_maker", "v2")
```

## LangSmith Features

### Prompt Versioning

- **Store prompt versions**: Save different versions of prompts in LangSmith
- **Manage versions**: View, compare, and switch between different prompt versions
- **Version tagging**: Organize prompts with descriptive version tags

### Run Tracking

- **Full trace visualization**: See the entire execution flow, from the initial query to the final response
- **Input/output capture**: Review the inputs and outputs at each step of the workflow
- **Error analysis**: Identify and debug failures in your workflow

### Performance Analytics

- **Token usage tracking**: Monitor token consumption for each component
- **Response timing**: Analyze latency across different parts of your workflow
- **Quality metrics**: Track confidence scores and other quality indicators

## Viewing Results in LangSmith

1. Log in to your LangSmith account at [smith.langchain.com](https://smith.langchain.com)
2. Select your project (e.g., "portfolio-advisor")
3. View your tracked runs, organized by timestamp and trace ID
4. Click on any run to see detailed information:
   - Full trace visualization
   - Inputs and outputs at each step
   - Token usage and latency metrics
   - Prompt versions used

## LangSmith API Structure

The LangSmith integration consists of:

- `LangSmithTracker`: Core class for interacting with LangSmith API
- `PromptVersionManager`: Manages prompt versions locally and in LangSmith
- `LangSmithIntegration`: Provides high-level API for working with the LangGraph portfolio engine

## Best Practices

1. **Version your prompts**: Create a new version when making significant changes
2. **Add descriptive tags**: Use meaningful version names and descriptions
3. **Monitor token usage**: Use the analytics to identify optimization opportunities
4. **Compare version performance**: Test different prompt versions to find the most effective ones
5. **Use run IDs for debugging**: Log the LangSmith run ID for easier troubleshooting 