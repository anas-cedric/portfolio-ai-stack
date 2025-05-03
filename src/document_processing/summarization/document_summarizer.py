"""
Financial document summarizer.

This module contains utilities for summarizing financial documents
to optimize context window utilization while preserving key information.
"""

import os
import re
import logging
import openai
from typing import Dict, List, Any, Optional, Tuple, Union
from dotenv import load_dotenv

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentSummarizer:
    """
    Summarizes financial documents using OpenAI to optimize context utilization.
    
    Features:
    - Length-aware summarization
    - Financial terminology preservation
    - Key data point extraction
    - Table and figure reference preservation
    """
    
    def __init__(
        self,
        model: str = "o1",
        api_key: Optional[str] = None,
        max_tokens: int = 4000
    ):
        """
        Initialize the document summarizer.
        
        Args:
            model: OpenAI model to use
            api_key: Optional OpenAI API key (will use environment variable if not provided)
            max_tokens: Maximum size of generated summaries
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set in OPENAI_API_KEY environment variable")
        
        # Initialize the OpenAI client
        self.client = openai.OpenAI(api_key=self.api_key)
        
        self.model = model
        self.max_tokens = max_tokens
        
        logger.info("DocumentSummarizer initialized with model: %s", model)
    
    def summarize(
        self,
        text: str,
        target_length: str = "medium",
        document_type: str = "general",
        focus_areas: Optional[List[str]] = None,
        preserve_data: bool = True
    ) -> str:
        """
        Summarize a financial document.
        
        Args:
            text: The document text
            target_length: "short", "medium", or "detailed"
            document_type: Type of financial document
            focus_areas: List of specific areas to focus on
            preserve_data: Whether to preserve numerical data points
            
        Returns:
            Summarized document
        """
        # Estimate the original length
        original_length = len(text.split())
        logger.info("Summarizing document of length %d words", original_length)
        
        # Determine the target token count
        if target_length == "short":
            target_tokens = min(int(original_length * 0.2), self.max_tokens)
        elif target_length == "medium":
            target_tokens = min(int(original_length * 0.4), self.max_tokens)
        else:  # detailed
            target_tokens = min(int(original_length * 0.6), self.max_tokens)
        
        # Create the prompt
        prompt = self._create_summarization_prompt(
            text=text,
            target_length=target_length,
            document_type=document_type,
            focus_areas=focus_areas,
            preserve_data=preserve_data,
            target_tokens=target_tokens
        )
        
        # Generate the summary with fallback options
        try:
            # Determine which models to try, in order of preference
            models_to_try = []
            if "o3-mini" in self.model:
                models_to_try = [
                    {"model": self.model, "is_o3": True},  # First try the requested o3 model
                    {"model": "o1", "is_o3": False},       # Fall back to o1 if o3 fails
                    {"model": "gpt-4", "is_o3": False}     # Last resort fallback
                ]
            else:
                models_to_try = [
                    {"model": self.model, "is_o3": False}  # Just try the requested model
                ]
            
            # Try each model in sequence until one works
            summary = None
            last_error = None
            
            for model_info in models_to_try:
                try:
                    model_name = model_info["model"]
                    is_o3 = model_info["is_o3"]
                    
                    logger.info(f"Attempting summarization with model: {model_name}")
                    
                    if is_o3:
                        # Configure o3-mini models with appropriate reasoning effort
                        response = self.client.chat.completions.create(
                            model=model_name,
                            messages=[
                                {"role": "user", "content": prompt}
                            ],
                            reasoning_effort="high" if model_name.endswith("-high") else "medium",
                            max_tokens=self.max_tokens,
                            temperature=0.1
                        )
                    else:
                        # Default configuration for o1 and other models
                        response = self.client.chat.completions.create(
                            model=model_name,
                            max_tokens=self.max_tokens,
                            messages=[
                                {"role": "user", "content": prompt}
                            ]
                        )
                        
                    # Successfully got a response
                    summary = response.choices[0].message.content
                    
                    # If we had to fall back to a different model, log this
                    if model_name != self.model:
                        logger.warning(f"Fell back to model {model_name} because original model {self.model} failed with: {last_error}")
                    
                    break  # Break the loop if successful
                    
                except Exception as e:
                    last_error = str(e)
                    logger.warning(f"Error with model {model_info['model']}: {last_error}")
                    continue  # Try the next model
            
            # If all models failed, raise the last error
            if summary is None:
                raise Exception(f"All model attempts failed. Last error: {last_error}")
                
            logger.info("Generated summary of length %d tokens", len(summary.split()))
            return summary
            
        except Exception as e:
            logger.error("Error generating summary: %s", str(e))
            # If the text is too long, try a two-stage summarization approach
            if "exceeded maxima" in str(e).lower() or "too long" in str(e).lower():
                return self._two_stage_summarization(text, target_length, document_type, focus_areas, preserve_data)
            else:
                raise
    
    def extract_key_points(
        self,
        text: str,
        max_points: int = 10,
        document_type: str = "general",
        focus_areas: Optional[List[str]] = None
    ) -> List[str]:
        """
        Extract key points from a financial document.
        
        Args:
            text: The document text
            max_points: Maximum number of key points to extract
            document_type: Type of financial document
            focus_areas: List of specific areas to focus on
            
        Returns:
            List of key points
        """
        # Create the prompt
        prompt = self._create_key_points_prompt(text, max_points, document_type, focus_areas)
        
        # Extract the key points
        try:
            if "o3-mini" in self.model:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    reasoning_effort="high" if self.model.endswith("-high") else "medium",
                    max_tokens=self.max_tokens,
                    temperature=0.1
                )
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
            key_points_text = response.choices[0].message.content
            
            # Process the response to get a list of key points
            key_points = []
            for line in key_points_text.split("\n"):
                line = line.strip()
                if line and (line.startswith("- ") or line.startswith("• ") or 
                             line.startswith("* ") or line[0].isdigit() and line[1] in [".", ")"]):
                    # Remove the list marker
                    point = re.sub(r"^[- •*\d.)\s]+", "", line).strip()
                    key_points.append(point)
            
            # If no bullet points were found, try returning lines
            if not key_points:
                key_points = [line.strip() for line in key_points_text.split("\n") if line.strip()]
            
            return key_points[:max_points]
            
        except Exception as e:
            logger.error("Error extracting key points: %s", str(e))
            raise
    
    def summarize_with_structure(
        self,
        text: str,
        structure: List[str],
        document_type: str = "general",
        preserve_data: bool = True
    ) -> Dict[str, str]:
        """
        Summarize a document according to a predefined structure.
        
        Args:
            text: The document text
            structure: List of sections to structure the summary by
                      (e.g., ["overview", "key_risks", "performance"])
            document_type: Type of financial document
            preserve_data: Whether to preserve numerical data points
            
        Returns:
            Dictionary of section summaries
        """
        # Create the prompt
        prompt = self._create_structured_summary_prompt(text, structure, document_type, preserve_data)
        
        # Generate the structured summary
        try:
            if "o3-mini" in self.model:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    reasoning_effort="high" if self.model.endswith("-high") else "medium",
                    max_tokens=self.max_tokens,
                    temperature=0.1
                )
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
            structured_text = response.choices[0].message.content
            
            # Parse the structured summary
            sections = {}
            current_section = None
            current_content = []
            
            for line in structured_text.split("\n"):
                line = line.strip()
                
                # Check if this is a section header
                is_header = False
                for section in structure:
                    section_name = section.replace("_", " ").title()
                    if line.lower().startswith(section.lower()) or line.lower().startswith(section_name.lower()):
                        # If we were processing a previous section, save it
                        if current_section and current_content:
                            sections[current_section] = "\n".join(current_content).strip()
                        
                        # Start a new section
                        current_section = section
                        current_content = []
                        is_header = True
                        break
                
                # If not a header, add to current content
                if not is_header and current_section:
                    current_content.append(line)
            
            # Add the last section
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content).strip()
            
            # Fill in any missing sections
            for section in structure:
                if section not in sections:
                    sections[section] = "No information available for this section."
            
            return sections
            
        except Exception as e:
            logger.error("Error generating structured summary: %s", str(e))
            raise
    
    def _two_stage_summarization(
        self,
        text: str,
        target_length: str,
        document_type: str,
        focus_areas: Optional[List[str]],
        preserve_data: bool
    ) -> str:
        """
        Perform two-stage summarization for long documents.
        
        Args:
            text: The document text
            target_length: Summary length
            document_type: Type of financial document
            focus_areas: List of specific areas to focus on
            preserve_data: Whether to preserve numerical data points
            
        Returns:
            Summarized document
        """
        logger.info("Document too long. Using two-stage summarization.")
        
        # Split the document into chunks
        chunks = self._split_text(text, 10000)  # 10K token chunks
        
        # First stage: Summarize each chunk
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            logger.info("Summarizing chunk %d of %d", i+1, len(chunks))
            
            # Create a chunk-specific prompt
            chunk_prompt = f"""
Here is a chunk of a longer document. Create a concise summary capturing all key information, 
particularly numerical data and main points.

DOCUMENT TYPE: {document_type}

DOCUMENT CHUNK {i+1} of {len(chunks)}:
{chunk}

INSTRUCTIONS:
- Generate a comprehensive yet concise summary of this chunk.
- Extract and preserve all key financial data points.
- Focus on facts, figures, and primary conclusions.
- Be precise and data-focused.
"""
            
            try:
                # Using OpenAI for chunk summarization
                if "o3-mini" in self.model:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "user", "content": chunk_prompt}
                        ],
                        reasoning_effort="high" if self.model.endswith("-high") else "medium",
                        max_tokens=int(self.max_tokens / 2),
                        temperature=0.1
                    )
                else:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        max_tokens=int(self.max_tokens / 2),
                        messages=[
                            {"role": "user", "content": chunk_prompt}
                        ]
                    )
                chunk_summary = response.choices[0].message.content
                chunk_summaries.append(chunk_summary)
                logger.info("Generated chunk summary of length %d tokens", len(chunk_summary.split()))
            except Exception as e:
                logger.error("Error during chunk summarization: %s", str(e))
                # If a chunk fails, add a placeholder
                chunk_summaries.append(f"[Error summarizing chunk {i+1}: {str(e)}]")
        
        # Second stage: Combine chunk summaries and create final summary
        combined_summaries = "\n\n--- NEXT CHUNK SUMMARY ---\n\n".join(chunk_summaries)
        
        final_prompt = self._create_summarization_prompt(
            text=combined_summaries,
            target_length=target_length,
            document_type=document_type,
            focus_areas=focus_areas,
            preserve_data=preserve_data,
            target_tokens=min(int(len(combined_summaries.split()) * 0.7), self.max_tokens)
        )
        
        # Generate the final summary
        try:
            if "o3-mini" in self.model:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": final_prompt}
                    ],
                    reasoning_effort="high" if self.model.endswith("-high") else "medium",
                    max_tokens=self.max_tokens,
                    temperature=0.1
                )
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    messages=[
                        {"role": "user", "content": final_prompt}
                    ]
                )
            final_summary = response.choices[0].message.content
            logger.info("Generated final summary of length %d tokens", len(final_summary.split()))
            return final_summary
        except Exception as e:
            logger.error("Error during final summarization: %s", str(e))
            raise
    
    def _create_summarization_prompt(
        self,
        text: str,
        target_length: str,
        document_type: str,
        focus_areas: Optional[List[str]],
        preserve_data: bool,
        target_tokens: int
    ) -> str:
        """
        Create a prompt for document summarization.
        
        Args:
            text: The document text
            target_length: Summary length
            document_type: Type of financial document
            focus_areas: List of specific areas to focus on
            preserve_data: Whether to preserve numerical data points
            target_tokens: Target token count
            
        Returns:
            Prompt for OpenAI
        """
        # Base instructions
        instructions = [
            f"Summarize the following {document_type} document.",
            f"Create a {target_length} summary approximately {target_tokens} tokens in length."
        ]
        
        # Special instructions based on document type
        if document_type == "prospectus":
            instructions.append("Preserve information about fund objectives, risks, expenses, and past performance.")
        elif document_type == "annual_report":
            instructions.append("Focus on performance, notable changes, market impacts, and future outlook.")
        elif document_type == "fact_sheet":
            instructions.append("Emphasize key metrics, allocations, performance, and fund characteristics.")
        elif document_type == "research":
            instructions.append("Maintain analytical points, recommendations, and supporting data.")
        elif document_type == "statement":
            instructions.append("Focus on main financial results, notable changes, and significant metrics.")
        
        # Add focus areas if provided
        if focus_areas:
            areas_text = ", ".join(focus_areas)
            instructions.append(f"Pay special attention to these areas: {areas_text}")
        
        # Add data preservation instruction
        if preserve_data:
            instructions.append("Preserve all significant numerical data points, statistics, and financial metrics.")
            instructions.append("Keep any performance figures, expense ratios, allocations, and important dates intact.")
        
        # Additional quality instructions
        instructions.extend([
            "Maintain a neutral, professional tone appropriate for financial documents.",
            "Exclude general background information unless it provides critical context.",
            "Present information in a logical, structured flow.",
            "Use financial terminology accurately and consistently."
        ])
        
        # Compile the final prompt
        prompt = "\n".join(instructions) + "\n\n"
        prompt += "DOCUMENT TO SUMMARIZE:\n" + text
        
        return prompt
    
    def _create_key_points_prompt(
        self,
        text: str,
        max_points: int,
        document_type: str,
        focus_areas: Optional[List[str]]
    ) -> str:
        """
        Create a prompt for extracting key points.
        
        Args:
            text: The document text
            max_points: Maximum number of key points
            document_type: Type of financial document
            focus_areas: List of specific areas to focus on
            
        Returns:
            Prompt for OpenAI
        """
        # Base instructions
        instructions = [
            f"Extract up to {max_points} key points from the following {document_type} document.",
            "Focus on the most significant information that an investor or analyst would need to know.",
            "Include concrete numerical data and specific facts rather than general statements.",
            "Present each key point as a concise bullet point, not paragraphs."
        ]
        
        # Special instructions based on document type
        if document_type == "prospectus":
            instructions.append("Prioritize points about investment objectives, principal risks, fees, and historical performance.")
        elif document_type == "annual_report":
            instructions.append("Focus on performance highlights, significant portfolio changes, and manager insights about the market.")
        elif document_type == "fact_sheet":
            instructions.append("Emphasize fund metrics, allocations, performance figures, and key risk statistics.")
        
        # Add focus areas if provided
        if focus_areas:
            areas_text = ", ".join(focus_areas)
            instructions.append(f"Pay special attention to these areas: {areas_text}")
        
        # Compile the final prompt
        prompt = "\n".join(instructions) + "\n\n"
        prompt += "DOCUMENT FOR KEY POINT EXTRACTION:\n" + text
        
        return prompt
    
    def _create_structured_summary_prompt(
        self,
        text: str,
        structure: List[str],
        document_type: str,
        preserve_data: bool
    ) -> str:
        """
        Create a prompt for structured document summarization.
        
        Args:
            text: The document text
            structure: List of sections to structure the summary by
            document_type: Type of financial document
            preserve_data: Whether to preserve numerical data points
            
        Returns:
            Prompt for OpenAI
        """
        sections_text = ", ".join(section.replace("_", " ") for section in structure)
        
        # Base instructions
        instructions = [
            f"Summarize the following {document_type} document into these specific sections: {sections_text}.",
            "For each section, extract and summarize only the relevant information from the document.",
            "Use clear section headers for each part of the summary.",
            "If information for a particular section is not found in the document, note this briefly."
        ]
        
        # Data preservation instruction
        if preserve_data:
            instructions.append("Preserve all significant numerical data points and financial metrics in your summary.")
        
        # Compile the final prompt
        prompt = "\n".join(instructions) + "\n\n"
        prompt += "DOCUMENT TO SUMMARIZE:\n" + text
        
        return prompt
    
    def _split_text(self, text: str, max_chunk_size: int) -> List[str]:
        """
        Split text into smaller chunks for processing.
        
        Args:
            text: The text to split
            max_chunk_size: Maximum size of each chunk in tokens (approximate)
            
        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            # Approximate token count (typically tokens ≈ 0.75 * word count)
            word_size = len(word) // 4 + 1
            
            # If adding this word would exceed the chunk size, save the chunk and start a new one
            if current_size + word_size > max_chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_size = 0
            
            current_chunk.append(word)
            current_size += word_size
        
        # Add the last chunk if not empty
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks 