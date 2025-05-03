"""
LangSmith Integration for LangGraph Portfolio Engine.

This module provides integration between LangSmith and the LangGraph Portfolio Engine, 
enabling tracking, analytics, and prompt versioning.
"""

import os
import logging
from typing import Dict, Any, Optional, Union, Callable, List
from dotenv import load_dotenv

# LangSmith imports
from src.langgraph_engine.langsmith_tracker import (
    LangSmithTracker, 
    PromptVersionManager,
    wrap_langsmith_decision_maker,
    wrap_langsmith_context_retriever
)

# LangGraph imports
from src.langgraph_engine.context_retriever import ContextRetriever
from src.langgraph_engine.decision_maker import DecisionMaker
from src.langgraph_engine.graph import create_portfolio_graph, run_portfolio_graph

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Default prompt templates
DEFAULT_DECISION_PROMPT = """
You are a sophisticated financial advisor analyzing portfolio decisions.

Given the following information:
- User Query: {query}
- User Profile: {user_profile}
- Portfolio Data: {portfolio_data}
- Market State: {market_state}
- Retrieved Context: {contexts}

Provide a well-reasoned financial decision that addresses the query.
Support your decision with specific references to the provided information.
Consider risk factors, market conditions, and the user's financial goals.

Your response should include:
1. A clear decision or recommendation
2. The reasoning behind your decision
3. Specific action items (if applicable)
4. Any relevant caveats or warnings
"""

DEFAULT_RETRIEVAL_PROMPT = """
You are a financial context retriever responsible for finding relevant information.

Given the following information:
- User Query: {query}
- User Profile: {user_profile}
- Portfolio Data: {portfolio_data}
- Market State: {market_state}

Identify the key concepts and requirements needed to answer this query effectively.
Focus on extracting the financial terms, asset classes, timeframes, and risk considerations.
"""


class LangSmithIntegration:
    """
    LangSmith integration for the LangGraph Portfolio Engine.
    
    This class provides methods for integrating LangSmith with the LangGraph
    portfolio engine, including run tracking, prompt versioning, and analytics.
    """
    
    def __init__(
        self,
        project_name: str = "portfolio-advisor",
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        enable_tracking: bool = True,
        enable_prompt_versioning: bool = True
    ):
        """
        Initialize the LangSmith integration.
        
        Args:
            project_name: The name of the project in LangSmith
            api_key: Optional LangSmith API key (defaults to LANGCHAIN_API_KEY env var)
            api_url: Optional LangSmith API URL (defaults to LANGCHAIN_ENDPOINT env var)
            enable_tracking: Whether to enable run tracking
            enable_prompt_versioning: Whether to enable prompt versioning
        """
        self.project_name = project_name
        self.api_key = api_key or os.getenv("LANGCHAIN_API_KEY")
        self.api_url = api_url or os.getenv("LANGCHAIN_ENDPOINT")
        self.enable_tracking = enable_tracking
        self.enable_prompt_versioning = enable_prompt_versioning
        
        # Initialize LangSmith tracker
        self.tracker = LangSmithTracker(
            project_name=project_name,
            api_key=self.api_key,
            api_url=self.api_url
        )
        
        # Initialize prompt version manager
        self.prompt_manager = PromptVersionManager(tracker=self.tracker)
        
        # Register default prompts
        if self.enable_prompt_versioning:
            self._register_default_prompts()
        
        # Set tracking status
        self.tracking_active = self.tracker.is_active() and self.enable_tracking
        logger.info(f"LangSmith integration initialized. Tracking active: {self.tracking_active}")
    
    def _register_default_prompts(self):
        """Register default prompts with the prompt manager."""
        self.prompt_manager.register_prompt(
            prompt_name="decision_maker",
            prompt_template=DEFAULT_DECISION_PROMPT,
            version="v1",
            description="Default decision maker prompt template"
        )
        
        self.prompt_manager.register_prompt(
            prompt_name="context_retriever",
            prompt_template=DEFAULT_RETRIEVAL_PROMPT,
            version="v1",
            description="Default context retrieval prompt template"
        )
        
        logger.info("Default prompts registered with prompt manager")
    
    def create_tracked_portfolio_graph(self):
        """
        Create a portfolio graph with LangSmith tracking.
        
        Returns:
            A StateGraph for portfolio decision making with tracking enabled
        """
        # Wrap the context retriever and decision maker with LangSmith tracking
        if self.tracking_active:
            TrackedContextRetriever = wrap_langsmith_context_retriever(
                ContextRetriever, 
                tracker=self.tracker
            )
            
            TrackedDecisionMaker = wrap_langsmith_decision_maker(
                DecisionMaker,
                tracker=self.tracker
            )
            
            # Create instances with tracking
            context_retriever = TrackedContextRetriever()
            decision_maker = TrackedDecisionMaker()
            
            # Create graph with tracked components
            graph = create_portfolio_graph(
                context_retriever=context_retriever,
                decision_maker=decision_maker
            )
            
            return graph
        else:
            # Create standard graph without tracking
            return create_portfolio_graph()
    
    def run_tracked_portfolio_graph(
        self,
        query: str,
        user_profile: Dict[str, Any],
        portfolio_data: Optional[Dict[str, Any]] = None,
        market_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run the portfolio graph with LangSmith tracking.
        
        Args:
            query: The user's query
            user_profile: User profile information
            portfolio_data: Current portfolio state
            market_state: Current market conditions
            
        Returns:
            The final state of the workflow with tracking metadata
        """
        try:
            # Start tracking without using context manager
            run = self.tracker.track_run(
                name="portfolio_analysis",
                inputs={
                    "query": query,
                    "user_profile": user_profile,
                    "portfolio_data": portfolio_data,
                    "market_state": market_state
                },
                run_type="chain"
            )
            
            # Create tracked components
            if self.tracking_active:
                TrackedContextRetriever = wrap_langsmith_context_retriever(
                    ContextRetriever, 
                    tracker=self.tracker
                )
                
                TrackedDecisionMaker = wrap_langsmith_decision_maker(
                    DecisionMaker,
                    tracker=self.tracker
                )
                
                context_retriever = TrackedContextRetriever()
                decision_maker = TrackedDecisionMaker()
            else:
                context_retriever = None
                decision_maker = None
            
            # Run the graph
            result = run_portfolio_graph(
                query=query,
                user_profile=user_profile,
                portfolio_data=portfolio_data,
                market_state=market_state,
                context_retriever=context_retriever,
                decision_maker=decision_maker
            )
            
            # End tracking
            self.tracker.end_run(run)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in tracked portfolio graph: {str(e)}")
            # Ensure run is ended even if there's an error
            if 'run' in locals():
                self.tracker.end_run(run)
            raise
    
    def get_prompt_versions(self, prompt_name: str) -> List[Dict[str, Any]]:
        """
        Get all versions of a prompt.
        
        Args:
            prompt_name: Name of the prompt
            
        Returns:
            List of prompt versions
        """
        return self.prompt_manager.list_prompt_versions(prompt_name)
    
    def set_active_prompt_version(self, prompt_name: str, version: str) -> bool:
        """
        Set the active version for a prompt.
        
        Args:
            prompt_name: Name of the prompt
            version: Version to set as active
            
        Returns:
            True if successful, False otherwise
        """
        return self.prompt_manager.set_active_version(prompt_name, version)
    
    def register_new_prompt_version(
        self,
        prompt_name: str,
        prompt_template: str,
        version: Optional[str] = None,
        description: Optional[str] = None
    ) -> str:
        """
        Register a new prompt version.
        
        Args:
            prompt_name: Name of the prompt
            prompt_template: The prompt template
            version: Optional version identifier
            description: Optional description of the prompt
            
        Returns:
            The version identifier
        """
        return self.prompt_manager.register_prompt(
            prompt_name=prompt_name,
            prompt_template=prompt_template,
            version=version,
            description=description
        )


# Global instance for easy access
langsmith_integration = None

def get_langsmith_integration() -> LangSmithIntegration:
    """
    Get or create the global LangSmith integration instance.
    
    Returns:
        LangSmith integration instance
    """
    global langsmith_integration
    if langsmith_integration is None:
        langsmith_integration = LangSmithIntegration()
    return langsmith_integration

def init_langsmith(
    project_name: str = "portfolio-advisor",
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    enable_tracking: bool = True,
    enable_prompt_versioning: bool = True
) -> LangSmithIntegration:
    """
    Initialize the global LangSmith integration instance.
    
    Args:
        project_name: The name of the project in LangSmith
        api_key: Optional LangSmith API key (defaults to LANGCHAIN_API_KEY env var)
        api_url: Optional LangSmith API URL (defaults to LANGCHAIN_ENDPOINT env var)
        enable_tracking: Whether to enable run tracking
        enable_prompt_versioning: Whether to enable prompt versioning
        
    Returns:
        LangSmith integration instance
    """
    global langsmith_integration
    langsmith_integration = LangSmithIntegration(
        project_name=project_name,
        api_key=api_key,
        api_url=api_url,
        enable_tracking=enable_tracking,
        enable_prompt_versioning=enable_prompt_versioning
    )
    return langsmith_integration 