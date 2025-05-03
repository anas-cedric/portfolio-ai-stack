"""
Financial Document Metadata Extractor.

This module implements specialized metadata extraction for financial documents,
focusing on common financial metrics, dates, entities, and relationships.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinancialMetadataExtractor:
    """
    Extracts structured financial metadata from document elements.
    
    Features:
    - Financial entity recognition (companies, funds, tickers)
    - Financial metric extraction (AUM, expense ratios, returns)
    - Date and time period identification
    - Relationship extraction (fund manager, parent company)
    - Regulatory filing recognition (10-K, 10-Q, prospectus)
    """
    
    def __init__(self):
        """Initialize the financial metadata extractor."""
        # Common financial entities and patterns
        self.ticker_pattern = r'\b[A-Z]{1,5}\b'  # Simple ticker pattern
        self.fund_types = [
            "ETF", "Mutual Fund", "Index Fund", "Bond Fund",
            "Money Market Fund", "Target Date Fund"
        ]
        
        # Common financial metrics
        self.financial_metrics = {
            "expense_ratio": [
                r'expense\s+ratio\s*:?\s*([\d.]+)%',
                r'expense\s+ratio\s*of\s*([\d.]+)%'
            ],
            "aum": [
                r'assets\s+under\s+management\s*:?\s*\$?([\d.,]+)\s*(million|billion|trillion|M|B|T)',
                r'AUM\s*:?\s*\$?([\d.,]+)\s*(million|billion|trillion|M|B|T)',
                r'fund\s+assets\s*:?\s*\$?([\d.,]+)\s*(million|billion|trillion|M|B|T)'
            ],
            "returns": [
                r'([\d.]+)%\s*(annual|annualized|1-year|3-year|5-year|10-year|year-to-date|YTD)\s*returns?',
                r'(1-year|3-year|5-year|10-year|YTD)\s*returns?\s*:?\s*([\d.]+)%'
            ],
            "inception_date": [
                r'inception\s+date\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\w+\s+\d{1,2},?\s+\d{4})',
                r'fund\s+inception\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\w+\s+\d{1,2},?\s+\d{4})'
            ]
        }
        
        # Regulatory filing types
        self.filing_types = {
            "10-K": ["annual report", "10-K", "10K", "annual filing"],
            "10-Q": ["quarterly report", "10-Q", "10Q", "quarterly filing"],
            "prospectus": ["prospectus", "fund prospectus", "summary prospectus"],
            "fact_sheet": ["fact sheet", "fund facts", "etf facts", "product summary"]
        }
        
        logger.info("Initialized FinancialMetadataExtractor")
    
    def extract_all_metadata(self, document_elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract all available metadata from document elements.
        
        Args:
            document_elements: List of document elements from UnstructuredProcessor
            
        Returns:
            Dictionary containing extracted financial metadata
        """
        # Combine all text for easier searching
        all_text = "\n\n".join([elem.get("text", "") for elem in document_elements])
        
        # Extract various metadata
        entities = self.extract_financial_entities(all_text)
        metrics = self.extract_financial_metrics(all_text)
        filing_info = self.identify_filing_type(all_text)
        dates = self.extract_dates(all_text)
        
        # Put everything together
        metadata = {
            "entities": entities,
            "metrics": metrics,
            "filing_info": filing_info,
            "dates": dates
        }
        
        # Look for specific sections (tables of contents, etc.) to further enhance metadata
        section_info = self.identify_document_sections(document_elements)
        if section_info:
            metadata["sections"] = section_info
        
        return metadata
    
    def extract_financial_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract financial entities from document text.
        
        Args:
            text: Document text
            
        Returns:
            Dictionary of extracted financial entities
        """
        entities = {
            "tickers": set(),
            "fund_types": set(),
            "companies": set()
        }
        
        # Extract potential tickers (simple implementation)
        ticker_matches = re.findall(self.ticker_pattern, text)
        # Filter out common false positives (like THE, AND, etc.)
        common_words = {"THE", "AND", "FOR", "NEW", "INC", "LLC", "LTD"}
        entities["tickers"] = set([t for t in ticker_matches if t not in common_words])
        
        # Identify fund types
        for fund_type in self.fund_types:
            if fund_type.lower() in text.lower():
                entities["fund_types"].add(fund_type)
        
        # Convert sets to lists for JSON serialization
        entities = {k: list(v) for k, v in entities.items()}
        
        return entities
    
    def extract_financial_metrics(self, text: str) -> Dict[str, Any]:
        """
        Extract financial metrics from document text.
        
        Args:
            text: Document text
            
        Returns:
            Dictionary of extracted financial metrics
        """
        metrics = {}
        
        # Search for each financial metric
        for metric_name, patterns in self.financial_metrics.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    # Different handling based on the metric
                    if metric_name == "expense_ratio":
                        metrics[metric_name] = float(matches[0])
                    elif metric_name == "aum":
                        value, unit = matches[0]
                        multiplier = 1
                        if unit.lower() in ["billion", "b"]:
                            multiplier = 1e9
                        elif unit.lower() in ["million", "m"]:
                            multiplier = 1e6
                        elif unit.lower() in ["trillion", "t"]:
                            multiplier = 1e12
                        metrics[metric_name] = float(value.replace(",", "")) * multiplier
                    elif metric_name == "returns":
                        # Simple implementation - in production would have more robust parsing
                        metrics[metric_name] = {
                            "value": float(matches[0][0]),
                            "period": matches[0][1]
                        }
                    elif metric_name == "inception_date":
                        metrics[metric_name] = matches[0]
                    
                    # Break after finding the first match for this metric
                    break
        
        return metrics
    
    def identify_filing_type(self, text: str) -> Dict[str, Any]:
        """
        Identify the type of financial filing.
        
        Args:
            text: Document text
            
        Returns:
            Dictionary with filing type information
        """
        filing_info = {
            "type": None,
            "confidence": 0.0
        }
        
        # Check for each filing type
        for filing_type, keywords in self.filing_types.items():
            matches = 0
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    matches += 1
            
            confidence = matches / len(keywords) if keywords else 0
            
            if confidence > filing_info["confidence"]:
                filing_info["type"] = filing_type
                filing_info["confidence"] = confidence
        
        return filing_info
    
    def extract_dates(self, text: str) -> Dict[str, Any]:
        """
        Extract relevant dates from document text.
        
        Args:
            text: Document text
            
        Returns:
            Dictionary of extracted dates
        """
        dates = {}
        
        # Common date patterns in financial documents
        date_patterns = [
            # Various date formats
            (r'(?:as of|dated|date[d:]|report date)?\s*(\w+\s+\d{1,2},?\s+\d{4})', "general_date"),
            (r'(?:quarter ended|period ended|fiscal year ended|year ended)\s*(\w+\s+\d{1,2},?\s+\d{4}|\d{1,2}/\d{1,2}/\d{2,4})', "period_end_date"),
            (r'(?:inception date|fund inception):\s*(\w+\s+\d{1,2},?\s+\d{4}|\d{1,2}/\d{1,2}/\d{2,4})', "inception_date")
        ]
        
        # Extract dates
        for pattern, date_type in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                dates[date_type] = matches[0]
        
        return dates
    
    def identify_document_sections(self, document_elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Identify important sections within the document.
        
        Args:
            document_elements: List of document elements
            
        Returns:
            Dictionary of identified document sections
        """
        sections = {}
        
        # Look for table of contents elements
        toc_indicators = ["table of contents", "contents", "toc"]
        for i, element in enumerate(document_elements):
            elem_text = element.get("text", "").lower()
            for indicator in toc_indicators:
                if indicator in elem_text and len(elem_text) < 500:  # Likely a TOC heading
                    # Look at the next few elements for TOC items
                    toc_items = []
                    for j in range(i+1, min(i+20, len(document_elements))):
                        toc_text = document_elements[j].get("text", "")
                        # Simple TOC item detection (would be more robust in production)
                        if re.search(r'^\s*[\w\s]+\s*\.{2,}\s*\d+\s*$', toc_text):
                            toc_items.append(toc_text.strip())
                    
                    if toc_items:
                        sections["table_of_contents"] = toc_items
                        break
            
            # Break if we found a TOC
            if "table_of_contents" in sections:
                break
        
        # Look for specific sections that are valuable for financial documents
        section_keywords = {
            "risk_factors": ["risk factors", "principal risks", "fund risks"],
            "fund_summary": ["fund summary", "etf summary", "investment summary"],
            "performance": ["performance", "fund performance", "historical performance"],
            "holdings": ["holdings", "portfolio holdings", "top holdings", "securities held"]
        }
        
        # Find sections
        for section_name, keywords in section_keywords.items():
            for i, element in enumerate(document_elements):
                elem_text = element.get("text", "").lower()
                
                # Check if this element is a section heading
                is_heading = False
                for keyword in keywords:
                    if keyword in elem_text and len(elem_text) < 200:  # Likely a heading
                        is_heading = True
                        break
                
                if is_heading:
                    # Collect the content from the next few elements
                    section_content = []
                    for j in range(i+1, min(i+10, len(document_elements))):
                        # Stop if we hit another heading
                        next_text = document_elements[j].get("text", "")
                        if len(next_text) < 100 and any(kw in next_text.lower() for section_kws in section_keywords.values() for kw in section_kws):
                            break
                        
                        section_content.append(next_text)
                    
                    if section_content:
                        sections[section_name] = "\n\n".join(section_content)
                    
                    break
        
        return sections
    
    def process_table_data(self, tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract financial information from tables.
        
        Args:
            tables: List of table elements from UnstructuredProcessor
            
        Returns:
            Dictionary of structured data extracted from tables
        """
        if not tables:
            return {}
        
        table_data = {}
        
        # Process each table
        for i, table in enumerate(tables):
            table_name = f"table_{i}"
            table_content = table.get("text", "")
            
            # Identify common financial tables
            if re.search(r'(expense|fee|fund\s+fees)', table_content, re.IGNORECASE):
                table_name = "expense_table"
            elif re.search(r'(performance|returns|1-year|3-year|5-year|10-year)', table_content, re.IGNORECASE):
                table_name = "performance_table"
            elif re.search(r'(holdings|portfolio|position|allocation)', table_content, re.IGNORECASE):
                table_name = "holdings_table"
            elif re.search(r'(sector|geographic|country|region)', table_content, re.IGNORECASE):
                table_name = "allocation_table"
            
            # Store the table content
            table_data[table_name] = table_content
        
        return table_data 