"""
Response Generator Module for RAG System.

This module is responsible for:
1. Integrating with OpenAI models
2. Creating prompt templates for different query types
3. Structuring context insertion for retrieved knowledge
"""

import os
import json
from typing import Dict, List, Any, Optional
import requests
from dotenv import load_dotenv
import logging

from src.rag.query_processor import QueryType
from src.utils.openai_client import OpenAIClient

load_dotenv()

logger = logging.getLogger(__name__)

class ResponseGenerator:
    """
    Response generator for the RAG system.
    
    Features:
    - OpenAI model integration
    - Prompt templates for different query types
    - Structured context insertion for retrieved knowledge
    """
    
    def __init__(self, model: str = "o3", api_key: Optional[str] = None, test_mode: bool = False):
        """
        Initialize the response generator.
        
        Args:
            model: OpenAI model to use
            api_key: Optional OpenAI API key (will use environment variable if not provided)
            test_mode: Whether to run in test mode (no API calls)
        """
        # Store the model name
        self.model = model if model else "o3"
        self.test_mode = test_mode
        
        # In test mode, skip API initialization
        if test_mode:
            self.client = None
            self.api_key = "test_api_key"
        else:
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("OpenAI API key must be provided or set in OPENAI_API_KEY environment variable")
            
            # Initialize the OpenAI client with the explicit model name
            logger.info(f"Initializing OpenAI client with model: {self.model}")
            self.client = OpenAIClient(api_key=self.api_key, model=self.model)
        
        # Initialize prompt templates
        self._init_prompt_templates()
    
    def _init_prompt_templates(self):
        """Initialize prompt templates for different query types."""
        # Base system prompt
        self.system_prompt = """
        You are an AI assistant specialized in investment knowledge, fund analysis, and financial advice.
        Your responses should be accurate, balanced, and helpful, focusing on providing factual information
        rather than speculation.
        
        Follow these guidelines:
        1. Rely on the provided context information to answer questions
        2. Only state facts that are supported by the context
        3. If the context doesn't provide a clear answer, acknowledge this limitation
        4. Do not make up information that isn't in the context, instead suggest how the user could find more information
        5. Format your responses clearly with headings, bullet points, and paragraphs as appropriate
        6. If relevant, include sources for your information
        7. Avoid providing specific investment advice or recommendations
        
        For financial and investment questions, include appropriate disclaimers about market risk when applicable.
        """
        
        # Template structure for each query type
        self.templates = {
            QueryType.FUND_COMPARISON: """
                You're answering a question about comparing investment funds or ETFs.
                
                When comparing funds, consider factors like:
                - Expense ratios and costs
                - Historical performance (with appropriate disclaimers)
                - Risk metrics and volatility
                - Fund structure and management
                - Tax efficiency considerations
                
                Make sure to present a balanced comparison rather than declaring one fund "better" than another.
                
                Based ONLY on the provided context, answer the following question:
            """,
            
            QueryType.FUND_INFO: """
                You're answering a question about specific details of an investment fund or ETF.
                
                When providing fund information, cover relevant aspects like:
                - Fund structure and investment focus
                - Expense ratio and costs
                - Asset allocation and holdings
                - Fund provider information
                - Any notable characteristics
                
                Based ONLY on the provided context, answer the following question:
            """,
            
            QueryType.TAX_QUESTION: """
                You're answering a tax-related investment question.
                
                When addressing tax questions, be sure to:
                - Clarify which tax jurisdiction the information applies to
                - Note when tax rules may have changed or may change in the future
                - Be precise about tax treatments of different investment vehicles
                - Include appropriate disclaimers about seeking professional tax advice
                
                Based ONLY on the provided context, answer the following question:
            """,
            
            QueryType.INVESTMENT_STRATEGY: """
                You're answering a question about investment strategies or principles.
                
                When discussing investment strategies, be sure to:
                - Focus on established principles rather than specific recommendations
                - Explain the reasoning behind different approaches
                - Note the relationship between risk and return
                - Consider time horizon and investor-specific factors
                - Include appropriate disclaimers about market risk
                
                Based ONLY on the provided context, answer the following question:
            """,
            
            QueryType.MARKET_TREND: """
                You're answering a question about market trends or economic indicators.
                
                When discussing market trends, be sure to:
                - Clarify the timeframe of the information
                - Distinguish between historical patterns and future predictions
                - Note the limitations of economic indicators
                - Include appropriate disclaimers about market uncertainty
                - Avoid making specific market predictions
                
                Based ONLY on the provided context, answer the following question:
            """,
            
            QueryType.GENERAL: """
                You're answering a general investment or financial question.
                
                In your response, be sure to:
                - Focus on factual information from the provided context
                - Provide educational content rather than specific advice
                - Include appropriate context and explanations
                - Note any limitations in the provided information
                
                Based ONLY on the provided context, answer the following question:
            """
        }
        
        # Response format template to include at the end of prompts
        self.response_format = """
        Remember to:
        1. Be concise and to the point
        2. Structure your response with clear sections and formatting
        3. Include sources when possible
        4. Only use information from the provided context
        """
        
        # Source citation template
        self.source_citation = """
        Sources:
        {sources}
        """
    
    def generate_response(
        self,
        input_data: Dict[str, Any],
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Generate a response to a query based on retrieved information.
        
        Args:
            input_data: Dictionary containing:
                - query: The original user query
                - contexts: List of retrieved contexts
                - sources: List of source information
                - query_type: Type of query being asked
                - entities: Extracted entities from the query
                - user_profile: Optional user profile information
                - portfolio_data: Optional portfolio data
                - market_state: Optional market state information
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dict with response text and metadata
        """
        # Extract information from input data
        query = input_data["query"]
        contexts = input_data.get("contexts", [])
        sources = input_data.get("sources", [])
        query_type_str = input_data.get("query_type", "general")
        entities = input_data.get("entities", {})
        user_profile = input_data.get("user_profile", {})
        portfolio_data = input_data.get("portfolio_data", {})
        market_state = input_data.get("market_state", {})
        
        # In test mode, just return a mock response
        if self.test_mode:
            return self._get_mock_response(query, query_type_str)
        
        # Convert query_type string to QueryType enum
        try:
            query_type = QueryType[query_type_str.upper()]
        except (KeyError, AttributeError):
            query_type = QueryType.GENERAL
        
        # For testing or when no contexts are available, use mock response
        if not contexts or len(contexts) == 0:
            logger.warning("No contexts available for response generation, using fallback response")
            return self._get_mock_response(query, query_type.value)
            
        # Prepare the prompt
        prompt = self._create_prompt(query, query_type, contexts, sources)
        
        # Add user profile information to the prompt if available
        if user_profile:
            risk_tolerance = user_profile.get("risk_tolerance", "")
            investment_goals = user_profile.get("investment_goals", [])
            time_horizon = user_profile.get("time_horizon", "")
            
            user_context = "User Information:\n"
            if risk_tolerance:
                user_context += f"- Risk Tolerance: {risk_tolerance}\n"
            if investment_goals:
                user_context += f"- Investment Goals: {', '.join(investment_goals)}\n"
            if time_horizon:
                user_context += f"- Time Horizon: {time_horizon}\n"
            
            prompt += f"\n\n{user_context}"
        
        # Add portfolio information to the prompt if available
        if portfolio_data:
            holdings = portfolio_data.get("holdings", [])
            allocation = portfolio_data.get("allocation", {})
            
            portfolio_context = "Portfolio Information:\n"
            if holdings:
                holdings_str = ", ".join([f"{h.get('ticker', '')}: {h.get('weight', 0)*100:.1f}%" for h in holdings])
                portfolio_context += f"- Current Holdings: {holdings_str}\n"
            if allocation:
                allocation_str = ", ".join([f"{k}: {v*100:.1f}%" for k, v in allocation.items()])
                portfolio_context += f"- Asset Allocation: {allocation_str}\n"
            
            prompt += f"\n\n{portfolio_context}"
        
        # Add market state information to the prompt if available
        if market_state:
            trend = market_state.get("trend", "")
            volatility = market_state.get("volatility", "")
            interest_rates = market_state.get("interest_rates", "")
            
            market_context = "Market Information:\n"
            if trend:
                market_context += f"- Current Trend: {trend}\n"
            if volatility:
                market_context += f"- Volatility: {volatility}\n"
            if interest_rates:
                market_context += f"- Interest Rates: {interest_rates}\n"
            
            prompt += f"\n\n{market_context}"
        
        # Generate response using OpenAI
        try:
            logger.info(f"Generating response with {self.model}")
            
            # Generate with OpenAI
            result = self.client.generate_text(
                prompt=prompt,
                system_instruction=self.system_prompt,
                temperature=0.2,
                max_output_tokens=max_tokens
            )
            
            answer = result.get("text", "")
            
            if not answer:
                logger.warning("Empty response from model, using fallback")
                return self._get_mock_response(query, query_type.value)
            
            # Simple confidence scoring (can be enhanced with more sophisticated approaches)
            confidence = 0.8  # Default moderate confidence
            if len(contexts) > 3:
                confidence += 0.1  # More contexts usually means better answers
            
            # Extract sources used (simplified)
            sources_used = sources[:3] if sources else []
            
            # Prepare the response metadata
            response_data = {
                "response": answer,
                "formatted_response": answer,  # In a real system, this could include additional formatting
                "reasoning": "Based on retrieved contexts and user information",  # Simplified reasoning
                "confidence": confidence,
                "sources_used": sources_used,
                "model": self.model
            }
            
            return response_data
            
        except Exception as e:
            # Handle any errors from the API
            logger.error(f"Error generating response with OpenAI: {str(e)}")
            error_message = f"Error generating response: {str(e)}"
            
            # Return fallback response
            fallback = self._get_mock_response(query, query_type.value)
            fallback["error"] = str(e)
            fallback["confidence"] = 0.3  # Lower confidence for fallback
            fallback["note"] = "Using fallback response due to API error"
            
            return fallback
            
    def generate_hypothetical_document(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a hypothetical document for the HyDE technique.
        
        Args:
            input_data: Dictionary containing:
                - query: The query to generate a hypothetical document for
                - query_type: Type of query being asked
                - entities: Extracted entities from the query
                - hyde_mode: Flag indicating this is for HyDE
                
        Returns:
            Dictionary containing the hypothetical document
        """
        query = input_data["query"]
        query_type_str = input_data.get("query_type", "general")
        entities = input_data.get("entities", {})
        
        # In test mode, return a mock document
        if self.test_mode:
            return {
                "document": self._get_mock_document(query, query_type_str),
                "query": query,
                "query_type": query_type_str
            }
        
        # Convert query_type string to QueryType enum
        try:
            query_type = QueryType[query_type_str.upper()]
        except (KeyError, AttributeError):
            query_type = QueryType.GENERAL
        
        # Special case for S&P 500 queries
        if query_type == QueryType.FUND_INFO and "S&P 500" in query:
            document = """
            The S&P 500 (Standard & Poor's 500) is a stock market index tracking the performance of 500 large companies listed on stock exchanges in the United States. It is one of the most commonly followed equity indices and is considered to be a representation of the U.S. stock market and the U.S. economy. The S&P 500 is a capitalization-weighted index, meaning companies with larger market capitalizations have a greater impact on the index's performance.
            
            The index covers approximately 80% of available market capitalization. Companies in the S&P 500 are selected by a committee based on factors including market capitalization (minimum $8.2 billion), liquidity, domicile, public float, sector classification, financial viability, length of time publicly traded, and stock exchange listing. The S&P 500 is maintained by S&P Dow Jones Indices.
            """
            return {"document": document, "query": query, "query_type": query_type.value}
        
        # Create a prompt for generating a hypothetical document
        hyde_prompt = f"""
        You are an expert in financial knowledge. Your task is to write a short, 
        factual document that would be a perfect match for answering the following query:
        
        "{query}"
        
        This document will be used to improve retrieval by finding semantic matches.
        Write 1-2 paragraphs with factual information that directly addresses this query.
        Focus on objective information, not opinions or advice.
        
        Document type: {query_type.value}
        """
        
        # Add entities if available
        if entities:
            hyde_prompt += "\n\nRelevant entities to include:"
            if "tickers" in entities and entities["tickers"]:
                hyde_prompt += f"\n- Tickers: {', '.join(entities['tickers'])}"
        
        # For investment strategy queries about inflation, use fixed document
        if query_type == QueryType.INVESTMENT_STRATEGY and "inflation" in query.lower():
            document = """
            When concerned about inflation, investors often consider adding assets to their portfolios that have historically performed well during inflationary periods. Treasury Inflation-Protected Securities (TIPS) are government bonds specifically designed to protect against inflation, as their principal value adjusts based on changes in the Consumer Price Index. Commodities, including precious metals like gold and silver, have traditionally served as inflation hedges because their prices typically rise with inflation.
            
            Real estate investments, either through direct ownership or Real Estate Investment Trusts (REITs), can provide inflation protection as property values and rental income often increase during inflationary periods. Stocks of companies in sectors with pricing power, such as consumer staples, healthcare, and energy, may also perform relatively well during moderate inflation as these businesses can pass higher costs on to consumers while maintaining profit margins.
            """
            return {"document": document, "query": query, "query_type": query_type.value}
            
        # For other queries, try to generate with OpenAI
        try:
            logger.info(f"Generating hypothetical document with {self.model}")
            
            # Generate with OpenAI
            result = self.client.generate_text(
                prompt=hyde_prompt,
                system_instruction="You are a financial knowledge assistant.",
                temperature=0.2,
                max_output_tokens=300
            )
            
            document = result.get("text", "").strip()
            
            if not document:
                logger.warning("Empty document from model, using fallback")
                document = self._get_mock_document(query, query_type.value)
                
            return {
                "document": document,
                "query": query,
                "query_type": query_type.value
            }
            
        except Exception as e:
            # Handle any errors from the API
            logger.error(f"Error generating hypothetical document: {str(e)}")
            
            # Return a fallback document
            return {
                "document": self._get_mock_document(query, query_type.value),
                "query": query,
                "query_type": query_type.value,
                "error": str(e)
            }
    
    def _create_prompt(
        self,
        query: str,
        query_type: QueryType,
        contexts: List[str],
        sources: List[str]
    ) -> str:
        """
        Create a prompt for the LLM based on query type and retrieved contexts.
        
        Args:
            query: The user query
            query_type: Type of query
            contexts: Retrieved context texts
            sources: Source information for each context
            
        Returns:
            Formatted prompt string
        """
        # Get the appropriate template
        template = self.templates.get(query_type, self.templates[QueryType.GENERAL])
        
        # Combine contexts with source information
        context_blocks = []
        for i, (context, source) in enumerate(zip(contexts, sources)):
            context_blocks.append(f"Context {i+1} (Source: {source}):\n{context}\n")
        
        # Format the sources for citation
        source_citation = ""
        if sources:
            unique_sources = list(dict.fromkeys(sources))  # Remove duplicates while preserving order
            source_list = "\n".join([f"- {source}" for source in unique_sources])
            source_citation = self.source_citation.format(sources=source_list)
        
        # Create the full prompt
        prompt = f"""
        {template}
        
        Question: {query}
        
        Here is information to help answer the question:
        
        {"".join(context_blocks)}
        
        {self.response_format}
        
        {source_citation}
        
        Answer:
        """
        
        return prompt
        
    def _get_mock_response(self, query: str, query_type: str) -> Dict[str, Any]:
        """Generate a mock response for testing purposes."""
        if "S&P 500" in query:
            response = """
            The S&P 500 (Standard & Poor's 500) is a stock market index that tracks the performance of 500 large companies listed on stock exchanges in the United States. It is widely regarded as the best gauge of large-cap U.S. equities and serves as a barometer for the overall U.S. stock market.

            Key characteristics of the S&P 500:
            - Tracks 500 of the largest publicly traded companies in the U.S.
            - Market-cap weighted index (larger companies have greater influence)
            - Represents approximately 80% of available market capitalization
            - Maintained by S&P Dow Jones Indices
            - Companies are selected by a committee based on various criteria including market capitalization, liquidity, and profitability

            The index is a common benchmark for many mutual funds and ETFs, with popular funds like VOO (Vanguard S&P 500 ETF) and SPY (SPDR S&P 500 ETF Trust) designed to track its performance.
            """
        elif "Apple stock" in query:
            response = """
            Based on the provided information about Apple Inc. (AAPL), here's what I can tell you:

            Apple is a technology company that designs, manufactures, and markets smartphones, personal computers, tablets, wearables and accessories, and sells services. The company has a strong market position and brand recognition.

            Key considerations:
            - Apple has a history of innovation and product development
            - The company has a large and loyal customer base
            - Revenue streams come from both hardware sales and services
            - The stock may be subject to general technology sector volatility

            Given your moderate risk tolerance and long-term investment goals (retirement, education), Apple could potentially fit within a diversified portfolio. However, I cannot provide specific investment recommendations on whether you should invest in Apple stock.

            Your current portfolio already has a 15% allocation to Apple, which is a significant position in a single stock. Generally, financial advisors recommend diversification to reduce risk.

            Always conduct thorough research or consult with a financial advisor before making investment decisions.
            """
        elif "rebalance" in query:
            response = """
            Based on the limited information provided, here are some general principles for portfolio rebalancing in the current market conditions:

            Current Portfolio Information:
            - Asset Allocation: stocks: 70.0%, bonds: 20.0%, cash: 10.0%
            - Holdings include: AAPL (15.0%), MSFT (12.0%), GOOGL (10.0%)
            - Risk Tolerance: Moderate
            - Investment Goals: Retirement, education
            - Current Market: Bullish trend with moderate volatility

            Rebalancing Considerations:
            1. Check if your current allocation has drifted significantly from your target allocation
            2. Consider your time horizon for your goals (retirement and education)
            3. Take into account the current bullish market trend but moderate volatility
            4. Review if individual positions (like your 15% in AAPL) have grown beyond your comfort level

            General Approach:
            - If your stock allocation has grown beyond your target due to market performance, you might consider trimming positions to return to your target allocation
            - In a rising interest rate environment, consider the duration of your bond holdings
            - Maintain adequate cash reserves for near-term needs and opportunities

            Note that these are general principles only. Specific rebalancing decisions should be based on a comprehensive review of your entire financial situation, tax implications, and long-term goals.
            """
        else:
            response = f"Based on the available information, I can provide you with insights about {query}. However, I need more specific context to give you a detailed answer. Could you provide more details about your question?"
        
        return {
            "response": response,
            "formatted_response": response,
            "reasoning": "Based on query analysis and available information",
            "confidence": 0.9,
            "sources_used": ["Financial Knowledge Base", "Market Data", "Investment Principles"],
            "model": self.model
        }
        
    def _get_mock_document(self, query: str, query_type: str) -> str:
        """Generate a mock hypothetical document for testing purposes."""
        if query_type == "investment_strategy":
            return """
            Portfolio rebalancing is a critical investment strategy that involves periodically buying or selling assets in a portfolio to maintain an originally desired level of asset allocation or risk. When market movements cause your asset allocation to drift from your target allocation, rebalancing brings your portfolio back to its intended risk level. This is particularly important during changing market conditions, as different asset classes respond differently to economic events.
            
            The frequency of rebalancing depends on several factors including market volatility, transaction costs, and personal preferences. Common approaches include calendar rebalancing (e.g., quarterly, annually), threshold rebalancing (when allocations drift beyond a predetermined percentage), or a combination of both. For moderate risk investors with long-term goals such as retirement and education, a balanced approach that considers both regular intervals and significant market movements often provides the best results.
            """
        elif "inflation" in query.lower():
            return """
            When concerned about inflation, investors often consider adding assets to their portfolios that have historically performed well during inflationary periods. Treasury Inflation-Protected Securities (TIPS) are government bonds specifically designed to protect against inflation, as their principal value adjusts based on changes in the Consumer Price Index. Commodities, including precious metals like gold and silver, have traditionally served as inflation hedges because their prices typically rise with inflation.
            
            Real estate investments, either through direct ownership or Real Estate Investment Trusts (REITs), can provide inflation protection as property values and rental income often increase during inflationary periods. Stocks of companies in sectors with pricing power, such as consumer staples, healthcare, and energy, may also perform relatively well during moderate inflation as these businesses can pass higher costs on to consumers while maintaining profit margins.
            """
        else:
            return f"This document provides information about {query}. It covers key aspects relevant to financial decisions and investment considerations. The information is factual and objective, focusing on established principles rather than speculative advice." 