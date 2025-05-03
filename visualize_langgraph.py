#!/usr/bin/env python
"""
Visualize the LangGraph portfolio decision flow.

This script generates a visualization of the LangGraph workflow
to help understand the decision flow.
"""

import os
import logging
import importlib.util

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_package_installed(package_name):
    """Check if a package is installed."""
    return importlib.util.find_spec(package_name) is not None

def main():
    """Generate and save LangGraph visualizations."""
    # Check if required packages are installed
    required_packages = ["langgraph", "graphviz"]
    missing_packages = [pkg for pkg in required_packages if not is_package_installed(pkg)]
    
    if missing_packages:
        logger.error("Missing required packages: %s", ", ".join(missing_packages))
        logger.info("Please install required packages:")
        logger.info("pip install %s", " ".join(missing_packages))
        return
    
    try:
        # Create the output directory if it doesn't exist
        os.makedirs('docs', exist_ok=True)
        
        # Import modules only after checking dependencies
        from src.langgraph_engine.graph import create_portfolio_graph
        from src.langgraph_engine.diagram import save_graph_visualization
        
        # Generate the LangGraph visualization
        logger.info("Generating LangGraph visualization...")
        save_graph_visualization("docs/langgraph_flow.png")
        
        logger.info("LangGraph visualization saved to docs/langgraph_flow.png")
        
        # Generate the system dataflow diagram using graphviz
        logger.info("Generating system dataflow diagram...")
        from docs.generate_diagram import generate_dataflow_diagram
        generate_dataflow_diagram()
        
        logger.info("Visualizations complete.")
        
    except ImportError as e:
        logger.error("Error importing visualization dependencies: %s", str(e))
        logger.info("Make sure both langgraph and graphviz are installed:")
        logger.info("pip install langgraph graphviz")
        logger.info("You may also need to install the Graphviz system package.")
        
    except Exception as e:
        logger.error("Error generating visualizations: %s", str(e))

if __name__ == "__main__":
    main() 