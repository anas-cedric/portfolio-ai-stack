# Document Processing for Financial AI

This module provides enhanced processing capabilities for financial data, specifically designed to work with LLMs and a LangGraph-based system.

## Components

### 1. Formatting

The formatting module optimizes financial data for LLM context utilization:

- `TabularFormatter`: Efficiently formats financial data in tabular format
  - Compact representation of tabular data
  - Intelligent column selection based on importance
  - Scale-aware number formatting (K, M, B suffixes)
  - Prioritization of important data

- `CompactNumberFormatter`: Format numbers in financial notation
  - Scale-appropriate suffixes (K, M, B, T)
  - Financial notation conventions
  - Consistent decimal precision
  - Special handling for percentages, basis points, ratios

### 2. Summarization

The summarization module creates concise summaries of financial documents:

- `DocumentSummarizer`: Leverages Claude to create optimized summaries
  - Length-aware summarization (brief, medium, detailed)
  - Financial terminology preservation
  - Key data point extraction
  - Table and figure reference handling
  - Structured summarization by sections

### 3. Market-Aware Retrieval

The market-aware module adjusts retrieval patterns based on market conditions:

- `VolatilityAwareRetriever`: Adjusts retrieval depth based on market volatility
  - Dynamic context window scaling
  - Historical volatility calculation
  - Adaptive document retrieval
  - Market event sensitivity
  - Prompt enhancement with volatility context

## Usage Examples

See the `examples/document_processing_examples.py` file for detailed usage examples of each component.

### Basic Usage

#### Tabular Formatter

```python
from src.document_processing.formatting import TabularFormatter
import pandas as pd

# Initialize the formatter
formatter = TabularFormatter(max_width=80, precision=2)

# Format a DataFrame
df = pd.DataFrame(your_data)
formatted_table = formatter.format_dataframe(df)
print(formatted_table)

# Format a dictionary
formatted_dict = formatter.format_dict(your_dict_data)
print(formatted_dict)
```

#### Document Summarizer

```python
from src.document_processing.summarization import DocumentSummarizer

# Initialize the summarizer
summarizer = DocumentSummarizer()

# Generate a summary
summary = summarizer.summarize(
    text=your_document_text,
    target_length="medium",  # "brief", "medium", or "detailed"
    document_type="prospectus"  # Type of financial document
)

# Extract key points
key_points = summarizer.extract_key_points(
    text=your_document_text,
    max_points=5
)

# Generate a structured summary
structure = ["overview", "key_risks", "performance"]
structured_summary = summarizer.summarize_with_structure(
    text=your_document_text,
    structure=structure
)
```

#### Volatility-Aware Retriever

```python
from src.document_processing.market_aware import VolatilityAwareRetriever

# Initialize the retriever
retriever = VolatilityAwareRetriever(
    base_document_count=3,
    max_document_count=10,
    volatility_threshold=1.5
)

# Retrieve documents with volatility awareness
results = retriever.retrieve(
    query="financial impact of rising interest rates",
    base_retriever=your_base_retriever  # Any retriever with search() or get_relevant_documents()
)

# Get market context
market_context = retriever.get_market_context()

# Enhance a prompt with volatility context
enhanced_prompt = retriever.adjust_prompt_for_volatility(
    prompt="Analyze current market conditions."
)
```

## Integration with LangGraph

These components can be easily integrated into a LangGraph-based system:

1. **Use the formatters in preparation nodes** to optimize data before sending to LLMs
2. **Add the summarizer as a preprocessing node** to condense document content
3. **Enhance retrieval nodes with volatility awareness** to adapt to market conditions

For more complex examples, see the LangGraph integration patterns in the main system documentation. 