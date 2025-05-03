"""
API Parameter Management Module

Centralizes the configuration and validation of API parameters for different
models including OpenAI models (o1, o3, o3-mini, o4-mini).

This module provides:
1. Standardized parameter mappings for each model
2. Parameter validation to prevent API errors
3. Default configurations for different task types
4. Utility functions for API call optimization
"""

import os
import logging
from typing import Dict, Any, Optional, Union, List, Literal
from enum import Enum
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class ModelType(str, Enum):
    """Types of models supported by the system."""
    # OpenAI models
    O1 = "o1"
    O3 = "o3"
    O3_MINI = "o3-mini"
    O3_MINI_HIGH = "o3"
    O4_MINI = "o4-mini-2025-04-16"
    
    # Other OpenAI/compatible models
    GPT4 = "gpt-4-0125-preview"
    GPT4_TURBO = "gpt-4-turbo-preview"
    GPT35_TURBO = "gpt-3.5-turbo-0125"
    
    @classmethod
    def get_default_model(cls) -> 'ModelType':
        """Get the default model from environment or fall back to O3."""
        model_str = os.getenv("OPENAI_MODEL", "o3")
        
        try:
            return cls(model_str)
        except ValueError:
            logger.warning(f"Unknown model '{model_str}' in environment, falling back to o3")
            return cls.O3

class ApiProvider(str, Enum):
    """API providers for different model types."""
    OPENAI = "openai"
    OTHER = "other"

class TaskType(str, Enum):
    """Types of tasks that might require different parameter configurations."""
    REASONING = "reasoning"
    CREATIVE = "creative"
    QA = "qa"
    SUMMARIZATION = "summarization"
    CODE = "code"
    FINANCIAL_DECISION = "financial_decision"
    CLASSIFICATION = "classification"
    MATH = "math"  # Add math task type explicitly
    DEFAULT = "default"

class ApiParameters:
    """
    Centralized API parameter management for various models.
    
    This class handles:
    - Model-specific parameter mappings
    - Parameter validation
    - Default configurations by task type
    - Optimization suggestions
    """
    
    def __init__(
        self, 
        model: Optional[Union[str, ModelType]] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize the API parameter manager.
        
        Args:
            model: The model to use (defaults to OPENAI_MODEL env var or O3)
            api_key: API key (defaults to appropriate env var based on provider)
        """
        # Convert string model name to ModelType enum
        if model is None:
            self.model = ModelType.get_default_model()
        elif isinstance(model, str):
            try:
                self.model = ModelType(model)
            except ValueError:
                logger.warning(f"Unknown model '{model}', falling back to default")
                self.model = ModelType.get_default_model()
        else:
            self.model = model
        
        # Determine the API provider for this model
        self.provider = self._get_provider_for_model(self.model)
        
        # Get the appropriate API key based on provider
        self.api_key = api_key or self._get_api_key_for_provider(self.provider)
        if not self.api_key:
            logger.warning(f"No API key provided or found for {self.provider.value} provider")
        
        # Set up model-specific parameter mappings
        self._setup_model_parameters()
        
        logger.info(f"Initialized API parameters manager with model: {self.model.value} (provider: {self.provider.value})")
    
    def _get_provider_for_model(self, model: ModelType) -> ApiProvider:
        """Determine the API provider for a given model."""
        if model in [ModelType.O1, ModelType.O3, ModelType.O3_MINI, ModelType.O3_MINI_HIGH,
                     ModelType.GPT4, ModelType.GPT4_TURBO, ModelType.GPT35_TURBO, ModelType.O4_MINI]:
            return ApiProvider.OPENAI
        else:
            return ApiProvider.OTHER
    
    def _get_api_key_for_provider(self, provider: ApiProvider) -> Optional[str]:
        """Get the appropriate API key from environment variables based on provider."""
        if provider == ApiProvider.OPENAI:
            return os.getenv("OPENAI_API_KEY")
        else:
            return None
    
    def _setup_model_parameters(self) -> None:
        """Set up model-specific parameter mappings and constraints."""
        # Common parameters across all models
        self.common_params = {
            "max_tokens": None,  # Will be set based on task type
            "temperature": 0.7,  # Default general temperature
            "top_p": 1.0,
        }
        
        # O1-specific parameters
        self.o1_params = {
            **self.common_params,
            "model": "o1",
            "max_tokens": 1024,
            "temperature": 0.1,  # More deterministic by default
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        }
        
        # O3-specific parameters
        self.o3_params = {
            **self.common_params,
            "model": "o3",
            "max_tokens": 2048,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        }
        
        # O3-mini specific parameters
        self.o3_mini_params = {
            **self.common_params,
            "model": "o3-mini",
            "max_tokens": 1024,
            "reasoning_effort": "medium",
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        }
        
        # O3-mini-high specific parameters
        self.o3_mini_high_params = {
            **self.common_params,
            "model": "o3",
            "max_tokens": 2048,
            "temperature": 0.2,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        }

        # O4-mini-2025-04-16 specific parameters
        self.o4_mini_params = {
            **self.common_params,
            "model": "o4-mini-2025-04-16",
            "max_tokens": 1024,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        }
        
        # GPT-4 specific parameters
        self.gpt4_params = {
            **self.common_params,
            "model": "gpt-4-0125-preview",
            "max_tokens": 4000,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        }
        
        # GPT-4 Turbo specific parameters
        self.gpt4_turbo_params = {
            **self.common_params,
            "model": "gpt-4-turbo-preview",
            "max_tokens": 4000,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        }
        
        # GPT-3.5 Turbo specific parameters
        self.gpt35_turbo_params = {
            **self.common_params,
            "model": "gpt-3.5-turbo-0125",
            "max_tokens": 2048,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        }
        
        # Map model types to their parameter sets
        self.model_params_map = {
            ModelType.O1: self.o1_params,
            ModelType.O3: self.o3_params,
            ModelType.O3_MINI: self.o3_mini_params,
            ModelType.O3_MINI_HIGH: self.o3_mini_high_params,
            ModelType.O4_MINI: self.o4_mini_params,
            ModelType.GPT4: self.gpt4_params,
            ModelType.GPT4_TURBO: self.gpt4_turbo_params,
            ModelType.GPT35_TURBO: self.gpt35_turbo_params,
        }
        
        # Default task type parameter adjustments
        self.task_adjustments = {
            TaskType.REASONING: {
                "temperature": 0.1,
                "top_p": 0.9,
                # For O3 mini, set reasoning effort to high in get_parameters
            },
            TaskType.CREATIVE: {
                "temperature": 0.8,
                "top_p": 0.95,
            },
            TaskType.QA: {
                "temperature": 0.3,
                "top_p": 0.9,
            },
            TaskType.SUMMARIZATION: {
                "temperature": 0.2,
                "top_p": 0.9,
            },
            TaskType.CODE: {
                "temperature": 0.1,
                "top_p": 0.95,
            },
            TaskType.FINANCIAL_DECISION: {
                "temperature": 0.0,  # Highly deterministic for financial decisions
                "top_p": 0.9,
                # For O3 mini, set reasoning effort to high in get_parameters
            },
            TaskType.CLASSIFICATION: {
                "temperature": 0.1,
                "top_p": 0.9,
            },
            TaskType.DEFAULT: {}  # No adjustments for default
        }
        
        # Parameter constraints for validation (min, max)
        self.param_constraints = {
            "temperature": (0.0, 2.0),
            "top_p": (0.0, 1.0),
            "frequency_penalty": (-2.0, 2.0),
            "presence_penalty": (-2.0, 2.0),
        }
    
    def get_parameters(self, task_type: Optional[Union[str, TaskType]] = None, **overrides) -> Dict[str, Any]:
        """
        Get optimized parameters for the specified task type.
        
        Args:
            task_type: The type of task (defaults to DEFAULT)
            **overrides: Explicit parameter overrides
            
        Returns:
            Dictionary of API parameters
        """
        # Get the base parameters for the current model
        params = self.model_params_map.get(self.model, self.common_params).copy()
        
        # Add API key if present
        if self.api_key:
            params["api_key"] = self.api_key
        
        # Convert string task type to TaskType enum
        if task_type is None:
            task_enum = TaskType.DEFAULT
        elif isinstance(task_type, str):
            try:
                task_enum = TaskType(task_type)
            except ValueError:
                logger.warning(f"Unknown task type '{task_type}', using DEFAULT")
                task_enum = TaskType.DEFAULT
        else:
            task_enum = task_type
        
        # Apply task-specific adjustments
        task_params = self.task_adjustments.get(task_enum, {})
        params.update(task_params)
        
        # Special handling for O3-mini models with reasoning tasks
        if self.model in [ModelType.O3_MINI, ModelType.O3_MINI_HIGH] and \
           task_enum in [TaskType.REASONING, TaskType.FINANCIAL_DECISION]:
            # Ensure high reasoning effort for reasoning tasks
            params["reasoning_effort"] = "high"
        
        # Apply explicit overrides
        params.update(overrides)
        
        # Validate parameters
        self._validate_parameters(params)
        
        # Model-specific parameter adjustments for API compatibility
        if self.provider == ApiProvider.OPENAI:
            # Handle different parameter names for OpenAI models
            if self.model in [ModelType.O3_MINI, ModelType.O3_MINI_HIGH, ModelType.O3] and "max_tokens" in params:
                # O3 models use max_completion_tokens instead of max_tokens
                params["max_completion_tokens"] = params.pop("max_tokens")
        
        return params
    
    def _validate_parameters(self, params: Dict[str, Any]) -> None:
        """
        Validate parameters against constraints.
        
        Args:
            params: Parameters to validate
            
        Raises:
            ValueError: If a parameter is out of bounds
        """
        for param_name, (min_val, max_val) in self.param_constraints.items():
            if param_name in params:
                value = params[param_name]
                if isinstance(value, (int, float)) and not min_val <= value <= max_val:
                    logger.warning(
                        f"Parameter '{param_name}' value {value} outside valid range "
                        f"[{min_val}, {max_val}]. Clamping to valid range."
                    )
                    # Clamp to valid range instead of raising an error
                    params[param_name] = max(min_val, min(value, max_val))
    
    def suggest_optimal_parameters(self, token_count: int, task_type: TaskType = TaskType.DEFAULT) -> Dict[str, Any]:
        """
        Suggest optimal parameters based on input token count and task type.
        
        Args:
            token_count: Approximate input token count
            task_type: Type of task
            
        Returns:
            Dictionary of suggested parameters
        """
        params = self.get_parameters(task_type)
        
        # Adjust max tokens based on input size and model
        if self.model == ModelType.O1:
            # O1 has a total token limit of 16K
            max_total = 16000
            suggested_output = min(4000, max_total - token_count - 500)  # 500 token buffer
            # Use the correct parameter name based on model
            if "max_completion_tokens" in params:
                params["max_completion_tokens"] = suggested_output
            else:
                params["max_tokens"] = suggested_output
                
        elif self.model in [ModelType.O3_MINI, ModelType.O3_MINI_HIGH]:
            # O3 mini has a total token limit of 16K
            max_total = 16000
            suggested_output = min(4000, max_total - token_count - 500)
            params["max_completion_tokens"] = suggested_output
            
        elif self.model == ModelType.O3:
            # O3 has a total token limit of 100K
            max_total = 100000
            suggested_output = min(4000, max_total - token_count - 1000)
            params["max_completion_tokens"] = suggested_output
            
        elif self.model == ModelType.O4_MINI:
            # Assume O4 mini has a token limit similar to O3 mini
            max_total = 16000
            suggested_output = min(4000, max_total - token_count - 500)
            params["max_tokens"] = suggested_output
            
        else:
            # Default for other models
            max_total = 8000
            suggested_output = min(2000, max_total - token_count - 500)
            params["max_tokens"] = suggested_output
        
        # Ensure suggested output is positive
        if "max_tokens" in params:
            params["max_tokens"] = max(100, params["max_tokens"])
        elif "max_completion_tokens" in params:
            params["max_completion_tokens"] = max(100, params["max_completion_tokens"])
        
        return params


# Convenience functions for common use cases

def get_reasoning_parameters(model: Optional[Union[str, ModelType]] = None, **overrides) -> Dict[str, Any]:
    """
    Get parameters optimized for reasoning tasks.
    
    Args:
        model: Model to use (defaults to O3)
        **overrides: Explicit parameter overrides
        
    Returns:
        Dictionary of API parameters
    """
    if model is None:
        model = ModelType.O3  # Default to O3 for reasoning
    
    api_params = ApiParameters(model)
    return api_params.get_parameters(TaskType.REASONING, **overrides)

def get_financial_decision_parameters(model: Optional[Union[str, ModelType]] = None, **overrides) -> Dict[str, Any]:
    """
    Get parameters optimized for financial decision tasks.
    
    Args:
        model: Model to use (defaults to O3)
        **overrides: Explicit parameter overrides
        
    Returns:
        Dictionary of API parameters
    """
    if model is None:
        model = ModelType.O3  # Default to O3 for financial decisions
    
    api_params = ApiParameters(model)
    return api_params.get_parameters(TaskType.FINANCIAL_DECISION, **overrides)

def get_recommended_model_for_task(task_type: TaskType) -> ModelType:
    """
    Get the recommended model for a specific task type.
    
    Args:
        task_type: The type of task
        
    Returns:
        Recommended model type
    """
    if task_type == TaskType.MATH:
        return ModelType.O4_MINI
    elif task_type in [TaskType.REASONING, TaskType.FINANCIAL_DECISION]:
        return ModelType.O3
    elif task_type == TaskType.CREATIVE:
        return ModelType.O3_MINI_HIGH
    else:
        return ModelType.O3  # Default to O3 for most tasks


class ModelRouter:
    """
    Routes tasks to the most appropriate model based on content.
    
    This class analyzes query content to determine the optimal model
    for processing, prioritizing efficiency and accuracy.
    """
    
    def __init__(
        self,
        math_model: str = ModelType.O4_MINI.value,
        reasoning_model: str = ModelType.O3.value,
        default_model: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize the model router.
        
        Args:
            math_model: Model to use for math-heavy tasks
            reasoning_model: Model to use for reasoning-heavy tasks
            default_model: Default model if no specific task is detected
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.math_model = math_model
        self.reasoning_model = reasoning_model
        self.default_model = default_model or reasoning_model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        # Keywords that suggest math-heavy content
        self.math_keywords = [
            "calculate", "computation", "formula", "percentage", 
            "return", "yield", "numerical", "metric", "ratio",
            "average", "mean", "median", "standard deviation",
            "correlation", "projection", "forecast"
        ]
        
        # Keywords that suggest reasoning-heavy content
        self.reasoning_keywords = [
            "explain", "analyze", "evaluate", "compare", "contrast",
            "synthesize", "recommend", "justify", "reason", "decide",
            "strategy", "approach", "alternative", "implication"
        ]
        
        # Initialize parameter manager for each model
        self.math_params = ApiParameters(math_model)
        self.reasoning_params = ApiParameters(reasoning_model)
    
    def detect_task_type(self, query: str) -> str:
        """
        Analyze query content to determine appropriate task type.
        
        Args:
            query: The query text to analyze
            
        Returns:
            Task type: "math", "reasoning", or "general"
        """
        query_lower = query.lower()
        
        # Count keyword occurrences
        math_score = sum(1 for kw in self.math_keywords if kw in query_lower)
        reasoning_score = sum(1 for kw in self.reasoning_keywords if kw in query_lower)
        
        # Check for numbers and symbols that indicate math content
        import re
        if re.search(r'\d+%|\$\d+|\d+\.\d+|[+\-*/=]', query):
            math_score += 2
        
        # Determine predominant task type
        if math_score > reasoning_score and math_score >= 2:
            return "math"
        elif reasoning_score >= 2:
            return "reasoning"
        else:
            return "general"
    
    def get_model_for_task(self, task_type: Union[str, TaskType]) -> str:
        """
        Get the appropriate model for a task type.
        
        Args:
            task_type: Type of task ("math", "reasoning", "general")
            
        Returns:
            Model name to use
        """
        if isinstance(task_type, TaskType):
            task_type = task_type.value
            
        if task_type == "math":
            return self.math_model
        elif task_type == "reasoning":
            return self.reasoning_model
        else:
            return self.default_model
    
    def get_parameters_for_query(self, query: str, **overrides) -> Dict[str, Any]:
        """
        Determine the appropriate model and parameters for a query.
        
        Args:
            query: The query to analyze
            **overrides: Parameter overrides
            
        Returns:
            Parameter dictionary with appropriate model selected
        """
        task_type = self.detect_task_type(query)
        model = self.get_model_for_task(task_type)
        
        # Use the appropriate parameter set based on task type
        if task_type == "math":
            return self.math_params.get_parameters(TaskType.MATH, **overrides)
        elif task_type == "reasoning":
            return self.reasoning_params.get_parameters(TaskType.REASONING, **overrides)
        else:
            # Use reasoning parameters for general tasks
            return self.reasoning_params.get_parameters(TaskType.DEFAULT, **overrides) 