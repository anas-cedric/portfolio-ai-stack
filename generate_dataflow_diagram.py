#!/usr/bin/env python
"""
Generate a data flow diagram for the portfolio AI stack.
This script creates a visual representation of the current architecture.
"""

import graphviz

def create_data_flow_diagram():
    """Create a data flow diagram for the current architecture."""
    
    # Create a new directed graph
    dot = graphviz.Digraph(
        'portfolio_ai_stack_flow', 
        comment='Portfolio AI Stack Data Flow',
        format='png'
    )
    
    # Configure the graph
    dot.attr(rankdir='TB', size='11,8', ratio='fill', nodesep='0.5', ranksep='0.7')
    dot.attr('node', shape='box', style='filled,rounded', fontname='Arial', fontsize='12', margin='0.2,0.1')
    dot.attr('edge', fontname='Arial', fontsize='10')
    
    # Define node styles
    external_style = {'fillcolor': '#D6EAF8', 'color': '#2E86C1'}
    ingestion_style = {'fillcolor': '#D5F5E3', 'color': '#27AE60'}
    retrieval_style = {'fillcolor': '#FCF3CF', 'color': '#F39C12'}
    graph_style = {'fillcolor': '#FADBD8', 'color': '#E74C3C'}
    storage_style = {'fillcolor': '#E8DAEF', 'color': '#8E44AD'}
    
    # Create clusters for each layer
    with dot.subgraph(name='cluster_external') as c:
        c.attr(label='External Data Sources', style='filled,rounded', fillcolor='#EBF5FB', color='#3498DB')
        
        # External data sources
        c.node('alpaca', 'Alpaca API\n(Market Data)', **external_style)
        c.node('fed', 'Fed APIs\n(Economic Data)', **external_style)
        c.node('edgar', 'SEC EDGAR\n(Financial Documents)', **external_style)
        c.node('user_data', 'User & Portfolio Data', **external_style)
    
    with dot.subgraph(name='cluster_ingestion') as c:
        c.attr(label='Data Ingestion Layer', style='filled,rounded', fillcolor='#EAFAF1', color='#2ECC71')
        
        # Ingestion components
        c.node('market_pipeline', 'Market Data Pipeline\n(src/data/market_data_service.py)', **ingestion_style)
        c.node('econ_pipeline', 'Economic Data Pipeline\n(src/data/economic_data_service.py)', **ingestion_style)
        c.node('doc_pipeline', 'Document Processing\n(ETL & Extraction)', **ingestion_style)
    
    with dot.subgraph(name='cluster_retrieval') as c:
        c.attr(label='Context Retrieval Layer', style='filled,rounded', fillcolor='#FEF9E7', color='#F1C40F')
        
        # Retrieval components
        c.node('query_processor', 'Query Processor\n(src/rag/query_processor.py)', **retrieval_style)
        c.node('retriever', 'Enhanced Retriever\n(src/rag/retriever.py)', **retrieval_style)
        c.node('context_retriever', 'Context Retriever\n(src/langgraph_engine/context_retriever.py)', **retrieval_style)
    
    with dot.subgraph(name='cluster_graph') as c:
        c.attr(label='LangGraph Engine', style='filled,rounded', fillcolor='#FDEDEC', color='#CB4335')
        
        # LangGraph components
        c.node('graph', 'Portfolio Graph\n(src/langgraph_engine/graph.py)', **graph_style)
        c.node('decision_maker', 'Decision Maker\n(src/langgraph_engine/decision_maker.py)', **graph_style)
    
    with dot.subgraph(name='cluster_storage') as c:
        c.attr(label='Data Storage Layer', style='filled,rounded', fillcolor='#F4ECF7', color='#9B59B6')
        
        # Storage components
        c.node('pinecone', 'Pinecone\n(Vector Database)', **storage_style)
        c.node('supabase', 'Supabase\n(User & Portfolio Data)', **storage_style)
        c.node('timescale', 'TimeScaleDB\n(Time-Series Data)', **storage_style)
    
    # CLI interface
    dot.node('cli', 'Portfolio Advisor CLI\n(portfolio_advisor.py)', style='filled,rounded', fillcolor='#FDEBD0', color='#E67E22')
    
    # Add edges to show data flow
    
    # External to ingestion
    dot.edge('alpaca', 'market_pipeline', label='OHLCV, Order Books')
    dot.edge('fed', 'econ_pipeline', label='Interest Rates, Inflation')
    dot.edge('edgar', 'doc_pipeline', label='Prospectuses, Reports')
    dot.edge('user_data', 'cli', label='User Queries')
    
    # Ingestion to storage
    dot.edge('market_pipeline', 'pinecone', label='Market Knowledge')
    dot.edge('market_pipeline', 'timescale', label='Price History')
    dot.edge('econ_pipeline', 'pinecone', label='Economic Indicators')
    dot.edge('econ_pipeline', 'timescale', label='Economic Time Series')
    dot.edge('doc_pipeline', 'pinecone', label='Document Embeddings')
    
    # Storage to retrieval
    dot.edge('pinecone', 'retriever', label='Vector Search')
    dot.edge('supabase', 'context_retriever', label='User Profile Data')
    dot.edge('timescale', 'context_retriever', label='Time Series Data')
    
    # Retrieval flow
    dot.edge('query_processor', 'retriever', label='Processed Query')
    dot.edge('retriever', 'context_retriever', label='Raw Contexts')
    
    # LangGraph flow
    dot.edge('context_retriever', 'graph', label='Enhanced Contexts')
    dot.edge('graph', 'decision_maker', label='State & Contexts')
    dot.edge('decision_maker', 'graph', label='Decision Output')
    
    # CLI flow
    dot.edge('cli', 'query_processor', label='User Query')
    dot.edge('graph', 'cli', label='Portfolio Decision')
    
    # Save and render the graph
    dot.render('portfolio_flow_diagram', view=True)
    return dot

if __name__ == "__main__":
    create_data_flow_diagram() 