"""
Test the LangGraph-based portfolio advisor.

This module contains unit tests for the LangGraph-based portfolio advisor.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import json
import importlib.util

# Add the root directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Check if langgraph is installed
langgraph_installed = importlib.util.find_spec("langgraph") is not None

# Define mocks that will be used if langgraph is installed
if langgraph_installed:
    from src.langgraph_engine.graph import create_portfolio_graph, run_portfolio_graph
    from src.langgraph_engine.context_retriever import ContextRetriever
    from src.langgraph_engine.decision_maker import DecisionMaker

    class MockContextRetriever:
        """Mock class for ContextRetriever to use in tests."""
        
        def retrieve(self, input_data):
            """Return mock retrieval results."""
            return {
                "query": input_data["query"],
                "contexts": [
                    "VTI is a Vanguard Total Stock Market ETF with an expense ratio of 0.03%.",
                    "The total stock market has historically returned around 7-10% annually over long periods.",
                    "A diversified portfolio typically includes a mix of stocks, bonds, and other asset classes."
                ],
                "sources": [
                    "Fund Knowledge Database",
                    "Market History",
                    "Investment Principles"
                ],
                "user_profile": input_data["user_profile"],
                "portfolio_data": input_data.get("portfolio_data"),
                "market_state": input_data.get("market_state"),
                "retrieval_metadata": {
                    "query_type": "investment_strategy",
                    "entities": {"tickers": ["VTI"]},
                    "relevance_scores": [0.95, 0.87, 0.82]
                }
            }

    class MockDecisionMaker:
        """Mock class for DecisionMaker to use in tests."""
        
        def make_decision(self, input_data):
            """Return mock decision results."""
            return {
                "query": input_data["query"],
                "decision": {
                    "action": "buy",
                    "details": "Consider adding more VTI to your portfolio."
                },
                "reasoning": "VTI provides broad market exposure with a very low expense ratio, which aligns with long-term investment goals.",
                "recommendations": [
                    {
                        "type": "buy",
                        "asset": "VTI",
                        "rationale": "Low cost, broad diversification",
                        "details": "Consider dollar-cost averaging to build position"
                    }
                ],
                "confidence": 0.85,
                "sources_used": ["Fund Knowledge Database", "Investment Principles"]
            }


@unittest.skipIf(not langgraph_installed, "LangGraph not installed, skipping tests")
class TestLangGraph(unittest.TestCase):
    """Test cases for the LangGraph implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_query = "Should I invest in VTI?"
        self.test_user_profile = {
            "risk_tolerance": "moderate",
            "investment_goals": ["retirement", "growth"],
            "time_horizon": "long-term"
        }
        self.test_portfolio_data = {
            "total_value": 100000.00,
            "holdings": [
                {"ticker": "VTI", "name": "Vanguard Total Stock Market ETF", "value": 25000.00, "percentage": 25.0},
                {"ticker": "BND", "name": "Vanguard Total Bond Market ETF", "value": 25000.00, "percentage": 25.0}
            ]
        }
    
    @patch('src.langgraph_engine.graph.ContextRetriever', new=MockContextRetriever)
    @patch('src.langgraph_engine.graph.DecisionMaker', new=MockDecisionMaker)
    def test_graph_creation(self):
        """Test that the portfolio graph can be created."""
        graph = create_portfolio_graph()
        self.assertIsNotNone(graph)
    
    @patch('src.langgraph_engine.graph.ContextRetriever', new=MockContextRetriever)
    @patch('src.langgraph_engine.graph.DecisionMaker', new=MockDecisionMaker)
    def test_graph_execution(self):
        """Test that the portfolio graph executes and returns expected results."""
        result = run_portfolio_graph(
            query=self.test_query,
            user_profile=self.test_user_profile,
            portfolio_data=self.test_portfolio_data
        )
        
        # Check that the result has the expected fields
        self.assertIn("decision", result)
        self.assertIn("reasoning", result)
        self.assertIn("recommendations", result)
        self.assertIn("confidence", result)
        
        # Check specific values
        self.assertEqual(result["decision"]["action"], "buy")
        self.assertGreater(result["confidence"], 0.8)
        self.assertIn("VTI", result["recommendations"][0]["asset"])
    
    @patch.object(ContextRetriever, 'retrieve')
    @patch.object(DecisionMaker, 'make_decision')
    def test_integration_with_mocks(self, mock_make_decision, mock_retrieve):
        """Test the integration between components using mocks."""
        # Set up the mock return values
        mock_retrieve.return_value = {
            "query": self.test_query,
            "contexts": ["Test context"],
            "sources": ["Test source"],
            "user_profile": self.test_user_profile,
            "portfolio_data": self.test_portfolio_data,
            "market_state": None,
            "retrieval_metadata": {"query_type": "test"}
        }
        
        mock_make_decision.return_value = {
            "query": self.test_query,
            "decision": {"action": "test_action", "details": "Test details"},
            "reasoning": "Test reasoning",
            "recommendations": [{"type": "test", "asset": "TEST", "rationale": "Test", "details": "Test"}],
            "confidence": 0.9,
            "sources_used": ["Test source"]
        }
        
        # Run the workflow
        result = run_portfolio_graph(
            query=self.test_query,
            user_profile=self.test_user_profile,
            portfolio_data=self.test_portfolio_data,
            context_retriever=ContextRetriever(),
            decision_maker=DecisionMaker()
        )
        
        # Verify the workflow executed as expected
        self.assertEqual(mock_retrieve.call_count, 1)
        self.assertEqual(mock_make_decision.call_count, 1)
        self.assertEqual(result["decision"]["action"], "test_action")
        self.assertEqual(result["confidence"], 0.9)
    
    def test_error_handling(self):
        """Test that the graph handles errors appropriately."""
        # Create a retriever that will raise an exception
        class ErrorRetriever:
            def retrieve(self, input_data):
                raise ValueError("Test error")
        
        # Run the workflow with the error-generating retriever
        result = run_portfolio_graph(
            query=self.test_query,
            user_profile=self.test_user_profile,
            context_retriever=ErrorRetriever(),
            decision_maker=MockDecisionMaker()
        )
        
        # Check that the fallback logic was triggered
        self.assertIn("error", result)
        self.assertEqual(result["decision"]["action"], "no_action")
        self.assertTrue("error" in result["reasoning"].lower())


if __name__ == '__main__':
    if not langgraph_installed:
        print("LangGraph is not installed. To run these tests, install it with:")
        print("pip install langgraph")
    else:
        unittest.main() 