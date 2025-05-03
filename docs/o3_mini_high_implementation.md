# OpenAI o3-mini-high Integration

This document describes the implementation of OpenAI's o3-mini-high model in the PAIGE financial analysis system.

## Overview

OpenAI o3-mini-high is a powerful reasoning model with specialized capabilities in STEM fields, particularly in math, science, and coding. It is part of the o3 family of models, optimized for these domains while maintaining cost efficiency.

The "high" variant uses increased reasoning effort, providing higher accuracy at the cost of slightly increased response time.

## Implementation Details

### Configuration

- Set `OPENAI_MODEL=o3-mini-high` in the `.env` file to use this model across the application
- Alternatively, you can use `o3-mini` for standard reasoning effort (faster responses)

### Model-Specific Parameters

When using o3-mini or o3-mini-high, our implementation automatically:

1. Sets the `reasoning_effort` parameter:
   - `reasoning_effort="high"` for o3-mini-high
   - `reasoning_effort="medium"` for o3-mini

2. Uses a lower temperature (0.1) for more deterministic responses

3. Maintains appropriate API formatting for each component

### Components Updated for o3-mini-high Support

The following components have been updated to properly support o3-mini-high:

1. **Financial Analysis Workflow**: Core analysis engine now handles o3-mini-high
2. **Document Summarizer**: Document processing with enhanced summarization capabilities
3. **RAG System**: Response generation with improved context integration
4. **Decision Maker**: Portfolio decision engine with better reasoning

## Performance Considerations

- o3-mini-high provides strong performance in financial analysis, particularly for numerical reasoning and complex calculations
- It offers 39% reduction in major errors compared to o1-mini
- Particularly strong in STEM domains, with high reasoning effort achieving 83.6% accuracy on AIME math competition questions

## Limitations

- o3-mini-high does not support vision capabilities
- For visual reasoning tasks, continue using o1

## Usage Guidelines

- Use o3-mini-high for complex financial analysis tasks requiring precise reasoning
- Use standard o3-mini when response speed is more important than maximum accuracy
- Configure via environment variable for consistent model usage throughout the application

## API Key Troubleshooting

If you encounter issues with your OpenAI API key when trying to use o3-mini-high, check the following:

1. **API Access Tier**: o3-mini-high is only available to select developers in API usage tiers 3-5
2. **Project Permissions**: Ensure your API key is associated with a project that has access to reasoning models
3. **Error Handling**: Implement graceful fallbacks to other models (like o1) when o3-mini-high is not available
4. **Quota Limitations**: Check if you've reached your usage quota or if billing is properly configured
5. **Authentication**: Verify the API key is correctly formatted and not expired

If your API key returns an "invalid_project" error, you may need to:
- Request access to the o3-mini model family through your OpenAI account dashboard
- Update your API key to one with the appropriate access level
- Contact OpenAI support to verify your account's access permissions

Until access is granted, you can temporarily modify the code to use an alternative model like o1 or gpt-4.

## Additional References

- See [OpenAI o3-mini documentation](https://openai.com/o3-mini) for more details about the model's capabilities
- See OpenAI System Card for comprehensive evaluation results 