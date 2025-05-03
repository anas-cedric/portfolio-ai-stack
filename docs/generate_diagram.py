#!/usr/bin/env python
"""
Generate a simple dataflow diagram for the LangGraph portfolio system.

This script uses the graphviz library to create a visual representation
of the system's data flow.
"""

import os
from graphviz import Digraph

def generate_dataflow_diagram(output_file="dataflow_diagram"):
    """
    Generate a dataflow diagram for the portfolio system.
    
    Args:
        output_file: Name of the output file (without extension)
    """
    # Create a new directed graph
    dot = Digraph(comment='Portfolio System Dataflow', format='png')
    
    # Set graph attributes
    dot.attr('graph', rankdir='TB', size='11,8', ratio='fill', nodesep='0.5')
    dot.attr('node', shape='box', style='filled', color='lightblue', fontname='Arial')
    dot.attr('edge', fontname='Arial')
    
    # Define the main nodes
    
    # External data sources
    with dot.subgraph(name='cluster_external') as c:
        c.attr(label='External Data Sources', style='filled', color='lightgrey')
        c.node('market_data', 'Market Data\nAlpaca API')
        c.node('macro_data', 'Macroeconomic Data\nFRED/BLS/BEA APIs')
        c.node('financial_docs', 'Financial Documents\nSEC EDGAR')
    
    # User data
    with dot.subgraph(name='cluster_user') as c:
        c.attr(label='User & Portfolio Data', style='filled', color='lightgrey')
        c.node('user_profile', 'User Profile')
        c.node('portfolio_data', 'Portfolio Holdings')
        c.node('transaction_data', 'Transaction History')
    
    # LangGraph components
    with dot.subgraph(name='cluster_langgraph') as c:
        c.attr(label='LangGraph Decision Engine', style='filled', color='lightgrey')
        c.node('context_retriever', 'Context Retriever')
        c.node('decision_maker', 'Decision Maker')
        c.node('fallback_handler', 'Error Handler')
    
    # Storage layer
    with dot.subgraph(name='cluster_storage') as c:
        c.attr(label='Storage Layer', style='filled', color='lightgrey')
        c.node('supabase', 'Supabase\nUser & Portfolio Data')
        c.node('pinecone', 'Pinecone\nVector Database')
    
    # Define edges for data flow
    
    # External data to LangGraph
    dot.edge('market_data', 'context_retriever', label='Market Data')
    dot.edge('macro_data', 'context_retriever', label='Economic Indicators')
    dot.edge('financial_docs', 'context_retriever', label='Document Embeddings')
    
    # User data to LangGraph
    dot.edge('user_profile', 'context_retriever', label='User Preferences')
    dot.edge('portfolio_data', 'context_retriever', label='Holdings')
    
    # Storage to components
    dot.edge('supabase', 'user_profile', label='Fetch')
    dot.edge('supabase', 'portfolio_data', label='Fetch')
    dot.edge('supabase', 'transaction_data', label='Fetch')
    dot.edge('pinecone', 'context_retriever', label='Query Vectors')
    
    # LangGraph internal flow
    dot.edge('context_retriever', 'decision_maker', label='Contexts')
    dot.edge('context_retriever', 'fallback_handler', label='Errors', style='dashed')
    dot.edge('decision_maker', 'fallback_handler', label='Errors', style='dashed')
    
    # Output
    dot.node('portfolio_decision', 'Portfolio Decision', shape='box', style='filled', color='#AAEEBB')
    dot.edge('decision_maker', 'portfolio_decision', label='Recommendation')
    dot.edge('fallback_handler', 'portfolio_decision', label='Fallback Decision', style='dashed')
    
    # Save the diagram
    dot.render(os.path.join('docs', output_file), view=False)
    print(f"Diagram saved as docs/{output_file}.png")

if __name__ == '__main__':
    # Generate the diagram
    generate_dataflow_diagram() 