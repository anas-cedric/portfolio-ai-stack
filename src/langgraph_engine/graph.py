"""
LangGraph Implementation for Portfolio Decision Engine.

This module defines the LangGraph workflow for making portfolio decisions
based on context retrieval and reasoning.
"""

from typing import Dict, List, Any, Annotated, TypedDict, Literal, Optional, Union, Tuple
import logging
from langgraph.graph import StateGraph, END
from src.langgraph_engine.context_retriever import ContextRetriever, RetrievalInput, RetrievalOutput
from src.langgraph_engine.decision_maker import DecisionMaker, DecisionInput, DecisionOutput

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the state type
class PortfolioGraphState(TypedDict):
    """Type definition for the portfolio graph state."""
    # Input fields
    query: str
    user_profile: Dict[str, Any]
    portfolio_data: Optional[Dict[str, Any]]
    market_state: Optional[Dict[str, Any]]
    
    # Processing fields
    contexts: Optional[List[str]]
    sources: Optional[List[str]]
    retrieval_metadata: Optional[Dict[str, Any]]
    
    # Output fields
    decision: Optional[Dict[str, Any]]
    reasoning: Optional[str]
    recommendations: Optional[List[Dict[str, Any]]]
    confidence: Optional[float]
    sources_used: Optional[List[str]]
    
    # Control fields
    error: Optional[str]
    should_fallback: Optional[bool]


def create_portfolio_graph(
    context_retriever: Optional[ContextRetriever] = None,
    decision_maker: Optional[DecisionMaker] = None
) -> StateGraph:
    """
    Create a LangGraph-based portfolio decision workflow.
    
    Args:
        context_retriever: Optional context retriever (will create a new one if not provided)
        decision_maker: Optional decision maker (will create a new one if not provided)
        
    Returns:
        A StateGraph for portfolio decision making
    """
    # Create components if not provided
    retriever = context_retriever or ContextRetriever()
    decider = decision_maker or DecisionMaker()
    
    # Create the graph
    workflow = StateGraph(PortfolioGraphState)
    
    # Define the nodes
    
    # Context retrieval node
    def retrieve_context(state: PortfolioGraphState) -> PortfolioGraphState:
        """Retrieve relevant context for the query."""
        try:
            logger.info("Retrieving context for query: %s", state["query"])
            
            # Prepare the input for retrieval
            retrieval_input: RetrievalInput = {
                "query": state["query"],
                "user_profile": state["user_profile"],
                "portfolio_data": state.get("portfolio_data"),
                "market_state": state.get("market_state")
            }
            
            # Retrieve context
            retrieval_output = retriever.retrieve(retrieval_input)
            
            # Update the state with retrieval results
            return {
                **state,
                "contexts": retrieval_output["contexts"],
                "sources": retrieval_output["sources"],
                "retrieval_metadata": retrieval_output["retrieval_metadata"]
            }
        
        except Exception as e:
            logger.error("Error retrieving context: %s", str(e))
            return {**state, "error": f"Context retrieval error: {str(e)}", "should_fallback": True}
    
    # Decision making node
    def make_decision(state: PortfolioGraphState) -> PortfolioGraphState:
        """Make a portfolio decision based on retrieved context."""
        try:
            logger.info("Making decision for query: %s", state["query"])
            
            # Make sure we have contexts
            if not state.get("contexts"):
                return {**state, "error": "No contexts available for decision making", "should_fallback": True}
            
            # Prepare the input for decision making
            decision_input: DecisionInput = {
                "query": state["query"],
                "contexts": state["contexts"],
                "sources": state["sources"],
                "user_profile": state["user_profile"],
                "portfolio_data": state.get("portfolio_data"),
                "market_state": state.get("market_state"),
                "retrieval_metadata": state["retrieval_metadata"]
            }
            
            # Make decision
            decision_output = decider.make_decision(decision_input)
            
            # Update the state with decision results
            return {
                **state,
                "decision": decision_output["decision"],
                "reasoning": decision_output["reasoning"],
                "recommendations": decision_output["recommendations"],
                "confidence": decision_output["confidence"],
                "sources_used": decision_output["sources_used"]
            }
        
        except Exception as e:
            logger.error("Error making decision: %s", str(e))
            return {**state, "error": f"Decision making error: {str(e)}", "should_fallback": True}
    
    # Fallback node for handling errors
    def handle_fallback(state: PortfolioGraphState) -> PortfolioGraphState:
        """Handle fallback logic when errors occur."""
        logger.warning("Using fallback logic due to error: %s", state.get("error"))
        
        return {
            **state,
            "decision": {"action": "no_action", "details": "Could not make a decision due to an error"},
            "reasoning": f"Error encountered during processing: {state.get('error', 'Unknown error')}",
            "recommendations": [
                {
                    "type": "information",
                    "asset": None,
                    "rationale": "Error recovery",
                    "details": "Please try again with a more specific query or contact support"
                }
            ],
            "confidence": 0.0,
            "sources_used": []
        }
    
    # Add nodes to the graph
    workflow.add_node("retrieve_context", retrieve_context)
    workflow.add_node("make_decision", make_decision)
    workflow.add_node("handle_fallback", handle_fallback)
    
    # Define the edges
    
    # Start → Retrieve Context
    workflow.set_entry_point("retrieve_context")
    
    # Retrieve Context → Make Decision (if no error)
    # Retrieve Context → Handle Fallback (if error)
    workflow.add_conditional_edges(
        "retrieve_context",
        lambda state: "handle_fallback" if state.get("should_fallback") else "make_decision"
    )
    
    # Make Decision → End (if no error)
    # Make Decision → Handle Fallback (if error)
    workflow.add_conditional_edges(
        "make_decision",
        lambda state: "handle_fallback" if state.get("should_fallback") else END
    )
    
    # Handle Fallback → End
    workflow.add_edge("handle_fallback", END)
    
    return workflow


def run_portfolio_graph(
    query: str,
    user_profile: Dict[str, Any],
    portfolio_data: Optional[Dict[str, Any]] = None,
    market_state: Optional[Dict[str, Any]] = None,
    context_retriever: Optional[ContextRetriever] = None,
    decision_maker: Optional[DecisionMaker] = None
) -> Dict[str, Any]:
    """
    Run the portfolio graph with optional custom components.
    
    Args:
        query: The user's query
        user_profile: User profile information
        portfolio_data: Current portfolio state
        market_state: Current market conditions
        context_retriever: Optional custom context retriever
        decision_maker: Optional custom decision maker
        
    Returns:
        The final state of the workflow
    """
    logger.info(f"Running portfolio graph for query: {query}")
    
    # Create workflow with optional custom components
    workflow = create_portfolio_graph(
        context_retriever=context_retriever,
        decision_maker=decision_maker
    )
    
    # Prepare initial state
    initial_state = {
        "query": query,
        "user_profile": user_profile,
        "portfolio_data": portfolio_data or {},
        "market_state": market_state or {},
        "contexts": [],
        "decision": None,
        "reasoning": None,
        "recommendations": []
    }
    
    # Compile the graph first (for LangGraph 0.2.x)
    compiled_graph = workflow.compile()
    
    # Run the workflow using invoke() on the compiled graph
    result = compiled_graph.invoke(initial_state)
    
    return result 