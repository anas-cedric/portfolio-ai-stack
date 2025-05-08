"""
Financial prompts library.

This module contains a comprehensive collection of prompts for various financial analysis tasks.
"""

from typing import Dict, Any, Optional, List
import os
from dotenv import load_dotenv
import logging
import json
import openai
from src.utils.openai_client import OpenAIClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# --- Commented out unnecessary model initialization ---
# def initialize_openai_model():
#     """Initialize and configure the OpenAI model."""
#     # Get the API key from environment variables
#     api_key = os.getenv("OPENAI_API_KEY")
#     if not api_key:
#         raise ValueError("OPENAI_API_KEY environment variable not set")
#     
#     # Initialize the model - using o3 by default
#     model_name = os.getenv("OPENAI_MODEL", "o3")
#     try:
#         client = OpenAIClient(api_key=api_key, model=model_name)
#         logger.info(f"Successfully initialized OpenAI model: {model_name}")
#         return client
#     except Exception as e:
#         logger.error(f"Error initializing OpenAI model: {str(e)}")
#         # Fall back to a different model if needed
#         fallback_model = "o4-mini-2025-04-16"
#         logger.info(f"Falling back to alternative model: {fallback_model}")
#         return OpenAIClient(api_key=api_key, model=fallback_model)
# 
# # Initialize the model
# try:
#     model = initialize_openai_model()
#     if model: # Check if initialization was successful
#         logger.info("OpenAIClient initialized successfully at module level.")
#     else:
#         logger.error("Failed to initialize OpenAIClient at module level. Model set to None.")
# except Exception as e:
#     logger.error(f"Exception during OpenAIClient initialization at module level: {str(e)}")
#     model = None
# --- End commented out block ---

class FinancialPrompts:
    """Collection of financial analysis prompts."""
    
    @staticmethod
    def get_system_prompt() -> str:
        """Get the base system prompt for financial analysis."""
        return """
        You are a sophisticated financial analyst specialized in interpreting financial data and providing insights.
        Your analysis should be data-driven, precise, and focused on actionable insights.
        
        Guidelines:
        1. Base all conclusions firmly on the provided data
        2. Use precise financial terminology
        3. Highlight key metrics and trends
        4. Maintain professional, neutral tone
        5. Cite specific data points when making claims
        6. Address queries directly and comprehensively
        7. Include appropriate disclaimers about market risk
        8. Consider both quantitative and qualitative factors
        9. Provide context for your analysis
        10. Be clear about limitations and uncertainties
        """
    
    @staticmethod
    def get_analysis_prompt(query: str, context: str, market_conditions: Optional[Dict[str, Any]] = None) -> str:
        """Get a prompt for financial analysis."""
        market_context = ""
        if market_conditions:
            volatility = market_conditions.get("volatility", 0)
            is_high_volatility = market_conditions.get("is_high_volatility", False)
            market_context = f"""
            Current Market Conditions:
            - Volatility Index: {volatility:.2f}
            - Market State: {'High Volatility' if is_high_volatility else 'Normal'}
            
            Please consider these market conditions in your analysis.
            """
        
        return f"""
        QUERY: {query}
        
        CONTEXT:
        {context}
        
        {market_context}
        
        Please provide a detailed financial analysis based on the above information.
        Include:
        1. Key findings and insights
        2. Supporting data points
        3. Trend analysis
        4. Risk considerations
        5. Recommendations (if appropriate)
        """
    
    @staticmethod
    def get_portfolio_analysis_prompt(
        portfolio_data: Dict[str, Any],
        market_data: Optional[Dict[str, Any]] = None,
        risk_profile: Optional[Dict[str, Any]] = None
    ) -> str:
        """Get a prompt for portfolio analysis."""
        return f"""
        Portfolio Analysis Request
        
        Current Portfolio:
        {portfolio_data}
        
        Market Data:
        {market_data if market_data else 'Not provided'}
        
        Risk Profile:
        {risk_profile if risk_profile else 'Not provided'}
        
        Please analyze the portfolio considering:
        1. Asset allocation and diversification
        2. Risk-adjusted returns
        3. Sector exposure
        4. Geographic distribution
        5. Cost efficiency
        6. Tax considerations
        7. Alignment with risk profile
        """
    
    @staticmethod
    def get_market_analysis_prompt(
        market_data: Dict[str, Any],
        timeframe: str = "1Y",
        focus_areas: Optional[List[str]] = None
    ) -> str:
        """Get a prompt for market analysis."""
        focus_text = "\n".join(f"- {area}" for area in (focus_areas or []))
        
        return f"""
        Market Analysis Request
        
        Timeframe: {timeframe}
        Market Data: {market_data}
        
        Focus Areas:
        {focus_text if focus_text else 'General market analysis'}
        
        Please provide:
        1. Market trend analysis
        2. Key economic indicators
        3. Sector performance
        4. Volatility assessment
        5. Risk factors
        6. Market sentiment
        7. Notable events or catalysts
        """
    
    @staticmethod
    def get_company_analysis_prompt(
        company_data: Dict[str, Any],
        financial_statements: Optional[Dict[str, Any]] = None,
        market_position: Optional[Dict[str, Any]] = None
    ) -> str:
        """Get a prompt for company analysis."""
        return f"""
        Company Analysis Request
        
        Company Data:
        {company_data}
        
        Financial Statements:
        {financial_statements if financial_statements else 'Not provided'}
        
        Market Position:
        {market_position if market_position else 'Not provided'}
        
        Please analyze:
        1. Financial health
        2. Growth prospects
        3. Competitive position
        4. Management effectiveness
        5. Risk factors
        6. Valuation metrics
        7. Industry comparison
        """
    
    @staticmethod
    def get_risk_analysis_prompt(
        portfolio_data: Dict[str, Any],
        market_conditions: Dict[str, Any],
        risk_metrics: Optional[Dict[str, Any]] = None
    ) -> str:
        """Get a prompt for risk analysis."""
        return f"""
        Risk Analysis Request
        
        Portfolio Data:
        {portfolio_data}
        
        Market Conditions:
        {market_conditions}
        
        Risk Metrics:
        {risk_metrics if risk_metrics else 'Not provided'}
        
        Please assess:
        1. Portfolio risk profile
        2. Market risk exposure
        3. Concentration risk
        4. Liquidity risk
        5. Credit risk
        6. Interest rate risk
        7. Currency risk
        8. Risk mitigation strategies
        """
    
    @staticmethod
    def get_tax_analysis_prompt(
        portfolio_data: Dict[str, Any],
        tax_context: Dict[str, Any],
        tax_brackets: Optional[Dict[str, Any]] = None
    ) -> str:
        """Get a prompt for tax analysis."""
        return f"""
        Tax Analysis Request
        
        Portfolio Data:
        {portfolio_data}
        
        Tax Context:
        {tax_context}
        
        Tax Brackets:
        {tax_brackets if tax_brackets else 'Not provided'}
        
        Please analyze:
        1. Tax efficiency
        2. Capital gains exposure
        3. Dividend tax implications
        4. Tax-loss harvesting opportunities
        5. Tax-advantaged account utilization
        6. Tax bracket considerations
        7. Tax optimization strategies
        """
    
    @staticmethod
    def get_portfolio_generation_prompt(
        age: int,
        risk_tolerance: str,
        time_horizon: str,
        initial_investment: float,
        target_allocation: Dict[str, float]
    ) -> str:
        """Create a prompt instructing the LLM to generate a portfolio recommendation.

        Args:
            age: User's age in years
            risk_tolerance: Derived risk tolerance category (e.g., Low, Moderate, Above-Avg)
            time_horizon: Investment time horizon description (e.g., "10 years", "long-term")
            initial_investment: Initial capital available to invest (in USD)
            target_allocation: Dict of ticker/asset -> target weight (0-1)

        Returns:
            A formatted system prompt string.
        """
        # Remove aggregate keys like "Bonds %" to shorten the prompt
        filtered_alloc = {k: v for k, v in target_allocation.items() if "%" not in k}
        total_weight = sum(filtered_alloc.values())
        if total_weight and abs(total_weight - 1.0) > 1e-6:
            logger.debug(f"Normalizing allocation weights. Raw total={total_weight:.4f} (should be 1.0)")
            filtered_alloc = {k: round(v / total_weight, 6) for k, v in filtered_alloc.items()}
        allocation_json = json.dumps(filtered_alloc, separators=(",", ":"))
        
        return (
            f"You are a Certified Financial Planner.\n\n"
            f"Client: age {age}, risk {risk_tolerance}, horizon {time_horizon}, invest ${initial_investment:,.0f}.\n"
            f"Target allocation json: {allocation_json}\n\n"
            "TASK: Return JSON ONLY with keys summary, holdings, notes. No markdown, no extra text.\n"
            "Rules: holdings ≤10 items, each {ticker, percentage, dollars}; percentage within 0.02 of target; dollars=percentage*initial_investment rounded.\n"
            "summary ≤15 words; notes ≤25 words; total ≤180 tokens; think silently."
        )
    
    @staticmethod
    def analyze_financial_data(prompt: str, use_math_model: bool = False) -> Dict[str, Any]:
        """
        Analyze financial data using the appropriate model based on task type.
        
        Args:
            prompt: The financial analysis prompt
            use_math_model: Whether to use the math-focused model (o4-mini-2025-04-16)
            
        Returns:
            Dictionary containing the analysis results
        """
        # Always use OpenAI
        return FinancialPrompts._analyze_with_openai(prompt, use_math=use_math_model)
    
    @staticmethod
    def _analyze_with_openai(prompt: str, use_math: bool = False) -> Dict[str, Any]:
        """
        Analyze financial data using OpenAI models.
        
        Args:
            prompt: The financial analysis prompt
            use_math: Whether to use the math-focused model (o4-mini-2025-04-16)
            
        Returns:
            Dictionary containing the analysis results
        """
        # Determine which model to use
        model_to_use = os.getenv("MATH_MODEL", "o3") if use_math else os.getenv("REASONING_MODEL", "o3")
        
        try:
            # Check if model is initialized
            if model is None:
                openai_client = initialize_openai_model()
            else:
                openai_client = model
                
            if not openai_client:
                return {
                    "analysis": "OpenAI client is not initialized. Cannot perform analysis.",
                    "model_used": "none",
                    "error": "Client initialization failed"
                }
            
            # Get system instruction
            system_instruction = FinancialPrompts.get_system_prompt()
            
            # If we're using math focused tasks, make sure we use o4-mini-2025-04-16
            if use_math and "o3" in openai_client.model:
                try:
                    openai_client = OpenAIClient(model="o4-mini-2025-04-16")
                    logger.info("Switched to o4-mini-2025-04-16 for math-focused task")
                except Exception:
                    logger.warning("Failed to switch to o4-mini-2025-04-16 model, continuing with current model")
            
            logger.info(f"Sending financial analysis prompt to OpenAI model: {openai_client.model} (length: {len(prompt)})")
            
            # Generate content
            response = openai_client.generate_text(
                prompt=prompt,
                system_instruction=system_instruction,
                max_output_tokens=4096  # Increased from 2048 to ensure we get a complete response
            )
            
            # Extract response text
            response_text = response.get("text", "")
            
            # Return the analysis
            return {
                "analysis": response_text,
                "model_used": openai_client.model
            }
            
        except Exception as e:
            logger.error(f"Error generating financial analysis with OpenAI: {str(e)}")
            return {
                "analysis": f"Error generating analysis: {str(e)}",
                "model_used": model_to_use,
                "error": str(e)
            }
    
    @staticmethod
    def analyze_portfolio_calculations(portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform precise mathematical calculations on portfolio data using o4-mini-2025-04-16.
        
        Args:
            portfolio_data: The portfolio data to analyze
            
        Returns:
            Dictionary containing the calculation results
        """
        prompt = f"""
        Please perform the following portfolio calculations on this data:
        
        {json.dumps(portfolio_data, indent=2)}
        
        Calculate and return the following metrics as a JSON object:
        1. Portfolio variance
        2. Risk-adjusted returns (Sharpe ratio)
        3. Sector allocation percentages
        4. Portfolio beta
        5. Historical performance metrics
        6. Concentration risk
        
        Format all percentages with two decimal places and all currency values in standard notation.
        Return only the calculated metrics as a valid JSON object.
        """
        
        # Use the math model for calculations
        return FinancialPrompts.analyze_financial_data(prompt, use_math_model=True)
    
    @staticmethod
    def explain_portfolio_strategy(portfolio_data: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate explanations and reasoning about portfolio strategy using o3.
        
        Args:
            portfolio_data: The portfolio data
            market_data: Current market data
            
        Returns:
            Dictionary containing the analysis results
        """
        prompt = f"""
        Please analyze this portfolio in the context of current market conditions:
        
        PORTFOLIO DATA:
        {json.dumps(portfolio_data, indent=2)}
        
        MARKET DATA:
        {json.dumps(market_data, indent=2)}
        
        Provide a comprehensive analysis that explains:
        1. How well the portfolio is positioned for current market conditions
        2. Key strengths and vulnerabilities
        3. Strategic recommendations
        4. Rationale behind each recommendation
        
        Focus on clear reasoning and actionable insights.
        """
        
        # Use the reasoning model for explanations
        return FinancialPrompts.analyze_financial_data(prompt, use_math_model=False)
    
    # ---- New two-step portfolio generation helpers ----
    
    @staticmethod
    def get_holdings_generation_prompt(
        age: int,
        risk_tolerance: str,
        time_horizon: str,
        initial_investment: float,
        target_allocation: Dict[str, float]
    ) -> str:
        """Prompt o4-mini-high to output only the holdings list.

        Output schema:
        {"holdings": [{"ticker": str, "percentage": float, "dollars": float}]}
        """
        filtered_alloc = {k: v for k, v in target_allocation.items() if "%" not in k}
        total_weight = sum(filtered_alloc.values())
        if total_weight and abs(total_weight - 1.0) > 1e-6:
            logger.debug(f"Normalizing allocation weights. Raw total={total_weight:.4f} (should be 1.0)")
            filtered_alloc = {k: round(v / total_weight, 6) for k, v in filtered_alloc.items()}
        alloc_json = json.dumps(filtered_alloc, separators=(",", ":"))
        
        return (
            f"Client profile: age {age}, risk {risk_tolerance}, horizon {time_horizon}, invest {initial_investment}.\n"
            f"Target allocation: {alloc_json}\n\n"
            "Return JSON ONLY with key 'holdings': list of up to 10 objects {ticker, percentage, dollars}.\n"
            "percentage within 0.02 of target weight; dollars = percentage * invest (round nearest dollar).\n"
            "No markdown, no extra keys."
        )
    
    @staticmethod
    def get_summary_notes_prompt(holdings_json: str) -> str:
        """Prompt o3 to create summary and notes based on holdings JSON string."""
        return (
            "Given the ETF holdings JSON below, return JSON ONLY with keys 'summary' (≤15 words) and 'notes' (≤25 words).\n"
            f"Holdings JSON: {holdings_json}"
        )
    
    # ---- New prompts for post-generation chat ----
    
    @staticmethod
    def get_allocation_explanation_prompt(question: str, holdings_json: str, notes: str | None = None) -> str:
        """Return a prompt asking the LLM to answer questions about the allocation."""
        addl_notes = f"\nExisting notes: {notes}" if notes else ""
        return (
            "You are Paige, an AI portfolio advisor. A user has questions about the following holdings JSON.\n"
            f"Holdings JSON: {holdings_json}{addl_notes}\n\n"
            f"User question: {question}\n\n"
            "Answer clearly and concisely. If numbers are referenced, keep consistent with the holdings JSON.\n"
            "IMPORTANT: Only answer questions directly related to the provided portfolio holdings and financial advice. "
            "If the user asks an off-topic question, politely state that you can only assist with portfolio-related inquiries."
        )
    
    @staticmethod
    def get_refinement_ack_prompt(ticker: str, change_pct: float) -> str:
        """Prompt confirming the refinement request before regeneration."""
        direction = "increase" if change_pct > 0 else "decrease"
        return (
            f"Acknowledged. I will {direction} {ticker} by {abs(change_pct)*100:.1f}%. Generating the adjusted portfolio now..."
        )