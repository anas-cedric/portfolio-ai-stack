"""
Generate a visual representation of the LangGraph portfolio decision graph.

This script creates a visualization of the LangGraph workflow for portfolio decisions.
"""

from src.langgraph_engine.graph import create_portfolio_graph
import os


def save_graph_visualization(output_path: str = "portfolio_graph.png"):
    """
    Generate and save a visualization of the portfolio decision graph.
    
    Args:
        output_path: Path to save the visualization
    """
    # Create the graph
    workflow = create_portfolio_graph()
    
    # Generate a visualization
    try:
        # Convert the StateGraph to a networkx graph first
        from langgraph.checkpoint import MemorySaver
        from langgraph.visualization import visualize as lg_visualize
        import os
        
        # Create a checkpoint saver
        checkpoint_saver = MemorySaver()
        checkpointed_graph = workflow.with_checkpointer(checkpoint_saver)
        
        # Get the working directory
        cwd = os.getcwd()
        output_full_path = os.path.join(cwd, output_path)
        
        # Generate the visualization
        lg_visualize(checkpointed_graph, to_file=output_full_path)
        
        print(f"Graph visualization saved to: {output_full_path}")
    
    except ImportError:
        print("Could not generate visualization. Make sure networkx and graphviz are installed.")
    except Exception as e:
        print(f"Error generating visualization: {str(e)}")


if __name__ == "__main__":
    # Generate the visualization
    save_graph_visualization() 