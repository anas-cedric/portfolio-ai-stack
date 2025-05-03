"""
Decision Maker for LangGraph-based Portfolio Engine.

This module is responsible for making investment decisions based on
retrieved context and user state information.
"""

from typing import Dict, List, Any, Optional, TypedDict, Union
import os
import logging
import json
import openai
from dotenv import load_dotenv

from src.utils.api_parameters import ModelType, ApiParameters, TaskType

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DecisionInput(TypedDict):
    """Type definition for decision input."""
    query: str
    contexts: List[str]
    sources: List[str]
    user_profile: Dict[str, Any]
    portfolio_data: Optional[Dict[str, Any]]
    market_state: Optional[Dict[str, Any]]
    retrieval_metadata: Dict[str, Any]


class DecisionOutput(TypedDict):
    """Type definition for decision output."""
    query: str
    decision: Dict[str, Any]
    reasoning: str
    recommendations: List[Dict[str, Any]]
    confidence: float
    sources_used: List[str]


class DecisionMaker:
    """
    AI-powered decision maker for portfolio decisions.
    
    This class uses OpenAI models (o3, o4-mini) to make portfolio 
    decisions based on:
    1. Retrieved context
    2. User profile
    3. Current portfolio state
    4. Market conditions
    """
    
    def __init__(
        self, 
        model: Optional[str] = None, 
        api_key: Optional[str] = None
    ):
        """
        Initialize the decision maker.
        
        Args:
            model: LLM model to use (defaults to environment variable or o3)
            api_key: Optional API key (will use environment variable if not provided)
        """
        # Use model from env var, or default to o3
        self.model_name = model or os.getenv("OPENAI_MODEL", "o3")
        
        # Get model type from name
        try:
            self.model_type = ModelType(self.model_name)
        except ValueError:
            # If unknown model, default to o3
            logger.warning(f"Unknown model '{self.model_name}', falling back to o3")
            self.model_type = ModelType.O3
            self.model_name = self.model_type.value
        
        # Initialize parameters manager with the chosen model
        self.params_manager = ApiParameters(self.model_type)

        # Get API key from environment variables if not provided
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=self.api_key)
        logger.info(f"DecisionMaker initialized with OpenAI model: {self.model_name}")
            
        logger.info(f"DecisionMaker ready to make financial decisions with model: {self.model_name}")
    
    def make_decision(self, input_data: DecisionInput) -> DecisionOutput:
        """
        Make a portfolio decision based on the provided data.
        
        Args:
            input_data: The input data for making a decision
            
        Returns:
            Decision output containing the decision and reasoning
        """
        query = input_data["query"]
        contexts = input_data["contexts"]
        sources = input_data["sources"]
        user_profile = input_data.get("user_profile", {})
        portfolio_data = input_data.get("portfolio_data", {})
        market_state = input_data.get("market_state", {})
        
        logger.info(f"Making decision for query: {query}")
        
        # Create the prompt for the AI model
        prompt = self._create_prompt(
            query=query,
            contexts=contexts,
            sources=sources,
            user_profile=user_profile,
            portfolio_data=portfolio_data,
            market_state=market_state
        )
        
        # Get the decision from the model
        try:
            # Use OpenAI client
            response = self._get_openai_response(prompt)
            model_response = response.choices[0].message.content
            
            # Parse the response
            parsed_response = self._parse_response(model_response)
            
            logger.info(f"Decision made with confidence: {parsed_response['confidence']}")
            
            return {
                "query": query,
                "decision": parsed_response["decision"],
                "reasoning": parsed_response["reasoning"],
                "recommendations": parsed_response["recommendations"],
                "confidence": parsed_response["confidence"],
                "sources_used": parsed_response["sources_used"]
            }
        
        except Exception as e:
            logger.error(f"Error making decision: {str(e)}")
            # Return a default response in case of error
            return {
                "query": query,
                "decision": {"action": "no_action", "reason": "error"},
                "reasoning": f"Error making decision: {str(e)}",
                "recommendations": [],
                "confidence": 0.0,
                "sources_used": []
            }
    
    def _get_openai_response(self, prompt: str) -> Any:
        """
        Get a response from an OpenAI model.
        
        Args:
            prompt: The formatted prompt
            
        Returns:
            Response from OpenAI
        """
        # Get optimized parameters for financial decisions
        params = self.params_manager.get_parameters(TaskType.FINANCIAL_DECISION)
        
        # Base message content
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": prompt}
        ]
        
        # Determine if this is a math-heavy task or reasoning-heavy task
        task_type = self._determine_task_type(prompt)
        model_to_use = self._select_model_for_task(task_type)
        
        logger.info(f"Task determined to be {task_type}, using model: {model_to_use}")
        
        # Set up parameters based on model type
        params.update({
            "model": model_to_use,
            "messages": messages,
        })
        
        # Add reasoning_effort for o3-mini models if needed
        if "o3-mini" in model_to_use:
            params["reasoning_effort"] = "high" if "high" in model_to_use else "medium"
        
        # Rename max_tokens if needed for OpenAI compatibility
        if "max_output_tokens" in params and "max_tokens" not in params:
            params["max_tokens"] = params.pop("max_output_tokens")
        
        # For regular o3, use appropriate max_completion_tokens parameter
        if model_to_use == "o3" and "max_tokens" in params:
            params["max_completion_tokens"] = params.pop("max_tokens")
        
        # Remove API key from parameters if present (it's passed directly to the client)
        if "api_key" in params:
            del params["api_key"]
        
        logger.info(f"Calling OpenAI model {model_to_use} with parameters: {params}")
        
        # Make the API call with the appropriate parameters
        return self.client.chat.completions.create(**params)
    
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the language model.
        
        Returns:
            The system prompt
        """
        return """
        You are an AI portfolio advisor specialized in investment decisions.
        Your task is to make portfolio decisions based on:
        1. User's query
        2. Retrieved relevant information
        3. User profile and risk tolerance
        4. Current portfolio holdings
        5. Market conditions
        
        Provide your response in a structured format with:
        1. Decision - A clear action to take
        2. Reasoning - Explanation of why this decision makes sense
        3. Recommendations - Specific recommendations, if applicable
        4. Sources - References to the information sources you used
        5. Confidence - A score from 0.0 to 1.0 indicating your confidence
        
        Be specific in your decision and avoid vague recommendations.
        If you cannot make a confident decision based on the information provided,
        acknowledge this limitation and suggest what additional information would be helpful.
        
        Remember that all investment decisions involve risk, and include appropriate disclaimers.
        
        You must respond with a valid JSON object containing the decision structure.
        """
    
    def _create_prompt(
        self,
        query: str,
        contexts: List[str],
        sources: List[str],
        user_profile: Dict[str, Any],
        portfolio_data: Optional[Dict[str, Any]],
        market_state: Optional[Dict[str, Any]]
    ) -> str:
        """
        Create a prompt for the language model based on the input data.
        
        Args:
            query: The user's query
            contexts: Retrieved context information
            sources: Sources of the retrieved information
            user_profile: User profile information
            portfolio_data: Current portfolio state
            market_state: Current market conditions
            
        Returns:
            A formatted prompt
        """
        # Format the contexts with their sources
        formatted_contexts = []
        for i, (context, source) in enumerate(zip(contexts, sources)):
            formatted_contexts.append(f"Source {i+1} ({source}):\n{context}\n")
        
        contexts_text = "\n".join(formatted_contexts)
        
        # Format user profile
        profile_text = self._format_user_profile(user_profile)
        
        # Format portfolio data
        portfolio_text = self._format_portfolio_data(portfolio_data)
        
        # Format market state
        market_text = self._format_market_state(market_state)
        
        # Build the prompt
        prompt = f"""
        USER QUERY:
        {query}
        
        RELEVANT INFORMATION:
        {contexts_text}
        
        USER PROFILE:
        {profile_text}
        
        CURRENT PORTFOLIO:
        {portfolio_text}
        
        MARKET CONDITIONS:
        {market_text}
        
        Based on the above information, make a portfolio decision that best addresses the user's query.
        Format your response as a JSON object with the following structure:
        
        ```json
        {{
            "decision": {{
                "action": "buy|sell|hold|rebalance|allocate|no_action",
                "details": "specific details about the decision"
            }},
            "reasoning": "detailed explanation of your reasoning",
            "recommendations": [
                {{
                    "type": "buy|sell|allocation|strategy",
                    "asset": "asset identifier if applicable",
                    "rationale": "why this recommendation",
                    "details": "specific details"
                }}
            ],
            "confidence": 0.85,
            "sources_used": ["source references used in decision making"]
        }}
        ```
        
        Remember to base your decision only on the information provided and indicate your confidence level accurately.
        """
        
        return prompt
    
    def _format_user_profile(self, user_profile: Dict[str, Any]) -> str:
        """
        Format user profile information for the prompt.
        
        Args:
            user_profile: User profile information
            
        Returns:
            Formatted user profile text
        """
        if not user_profile:
            return "No user profile information available."
        
        profile_items = []
        
        if "risk_tolerance" in user_profile:
            profile_items.append(f"Risk Tolerance: {user_profile['risk_tolerance']}")
        
        if "investment_goals" in user_profile:
            goals = ", ".join(user_profile["investment_goals"])
            profile_items.append(f"Investment Goals: {goals}")
        
        if "time_horizon" in user_profile:
            profile_items.append(f"Time Horizon: {user_profile['time_horizon']}")
        
        if "age" in user_profile:
            profile_items.append(f"Age: {user_profile['age']}")
        
        if "income" in user_profile:
            profile_items.append(f"Income: {user_profile['income']}")
        
        if not profile_items:
            return "Limited user profile information available."
        
        return "\n".join(profile_items)
    
    def _format_portfolio_data(self, portfolio_data: Optional[Dict[str, Any]]) -> str:
        """
        Format portfolio data for the prompt.
        
        Args:
            portfolio_data: Portfolio data
            
        Returns:
            Formatted portfolio text
        """
        if not portfolio_data:
            return "No portfolio information available."
        
        portfolio_items = []
        
        if "total_value" in portfolio_data:
            portfolio_items.append(f"Total Value: ${portfolio_data['total_value']:,.2f}")
        
        if "holdings" in portfolio_data and portfolio_data["holdings"]:
            holdings_text = "Holdings:\n"
            for holding in portfolio_data["holdings"]:
                ticker = holding.get("ticker", "Unknown")
                name = holding.get("name", ticker)
                value = holding.get("value", 0)
                percentage = holding.get("percentage", 0)
                holdings_text += f"- {ticker} ({name}): ${value:,.2f} ({percentage:.2f}%)\n"
            portfolio_items.append(holdings_text)
        
        if "allocations" in portfolio_data and portfolio_data["allocations"]:
            allocations_text = "Asset Allocations:\n"
            for asset_class, percentage in portfolio_data["allocations"].items():
                allocations_text += f"- {asset_class}: {percentage:.2f}%\n"
            portfolio_items.append(allocations_text)
        
        if not portfolio_items:
            return "Limited portfolio information available."
        
        return "\n".join(portfolio_items)
    
    def _format_market_state(self, market_state: Optional[Dict[str, Any]]) -> str:
        """
        Format market state for the prompt.
        
        Args:
            market_state: Market state information
            
        Returns:
            Formatted market state text
        """
        if not market_state:
            return "No market condition information available."
        
        market_items = []
        
        if "trend" in market_state:
            market_items.append(f"Market Trend: {market_state['trend']}")
        
        if "indicators" in market_state and market_state["indicators"]:
            indicators_text = "Economic Indicators:\n"
            for indicator, value in market_state["indicators"].items():
                indicators_text += f"- {indicator}: {value}\n"
            market_items.append(indicators_text)
        
        if "volatility" in market_state:
            market_items.append(f"Market Volatility: {market_state['volatility']}")
        
        if not market_items:
            return "Limited market information available."
        
        return "\n".join(market_items)
        
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the model's response to extract decision components.
        
        Args:
            response: Raw model response
            
        Returns:
            Parsed structure with decision, reasoning, etc.
        """
        # Default response in case parsing fails
        default_response = {
            "decision": {"action": "no_action", "reason": "parsing_error"},
            "reasoning": "Could not parse model response into the expected format.",
            "recommendations": [],
            "confidence": 0.5,
            "sources_used": []
        }
        
        try:
            # Try to find the JSON part of the response using regex
            import re
            json_match = re.search(r'```json\s*({.*?})\s*```', response, re.DOTALL)
            
            if json_match:
                # If found within code blocks, extract and parse
                json_str = json_match.group(1)
                parsed = json.loads(json_str)
                
            else:
                # Try to extract any JSON object from the response
                json_pattern = r'({[\s\S]*})'
                match = re.search(json_pattern, response)
                
                if match:
                    json_str = match.group(1)
                    parsed = json.loads(json_str)
                else:
                    # If no JSON found, use direct response as reasoning
                    logger.warning("No JSON found in response, using default structure")
                    parsed = default_response
                    parsed["reasoning"] = response.strip()
            
            # Validate the parsed response has the required fields
            required_fields = ["decision", "reasoning"]
            for field in required_fields:
                if field not in parsed:
                    parsed[field] = default_response[field]
                    logger.warning(f"Missing required field '{field}' in response, using default")
            
            # Set defaults for optional fields if missing
            if "recommendations" not in parsed:
                parsed["recommendations"] = []
            
            if "confidence" not in parsed:
                parsed["confidence"] = 0.7  # Default confidence
            
            if "sources_used" not in parsed:
                parsed["sources_used"] = []
            
            return parsed
            
        except Exception as e:
            logger.error(f"Error parsing model response: {str(e)}")
            # Return the default response with the original text as reasoning
            default_response["reasoning"] = response.strip()
            return default_response
    
    def _determine_task_type(self, prompt: str) -> str:
        """
        Determine the task type based on the prompt content.
        
        Args:
            prompt: The user prompt
            
        Returns:
            Task type string ("math", "reasoning", or "general")
        """
        # Check for mathematical content (numbers, percentages, formulas)
        math_indicators = [
            r'\d+%', r'\$\d+', r'\d+\.\d+',  # Percentages, dollar amounts, decimals
            r'calculate', r'compute', r'formula', r'equations',  # Calculation words
            r'yield', r'returns?', r'profit', r'loss', r'gain'  # Financial math terms
        ]
        
        import re
        math_count = sum(bool(re.search(pattern, prompt, re.IGNORECASE)) for pattern in math_indicators)
        
        # Check for reasoning and decision-making content
        reasoning_indicators = [
            r'why', r'explain', r'consider', r'analyze', r'evaluation',  # Reasoning words
            r'strategy', r'decide', r'decision', r'approach', r'advise',  # Strategic words
            r'recommend', r'suggestion', r'alternative', r'option'  # Advisory words
        ]
        
        reasoning_count = sum(bool(re.search(pattern, prompt, re.IGNORECASE)) for pattern in reasoning_indicators)
        
        # Determine task type based on prevalence of indicators
        if math_count > reasoning_count and math_count >= 2:
            return "math"
        elif reasoning_count >= 2:
            return "reasoning"
        else:
            return "general"
    
    def _select_model_for_task(self, task_type: str) -> str:
        """
        Select the appropriate model for the given task type.
        
        Args:
            task_type: The identified task type
            
        Returns:
            Model name to use
        """
        if task_type == "math":
            # Use o4-mini-2025-04-16 for math-heavy tasks
            return "o4-mini-2025-04-16"
        elif task_type == "reasoning":
            # Use regular o3 for reasoning-heavy tasks
            return ModelType.O3.value
        else:
            # Default to regular o3 for general tasks
            return ModelType.O3.value 