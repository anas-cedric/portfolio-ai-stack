"""
Claude API Client.

This module provides a client for interacting with Anthropic's Claude API.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
import anthropic

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class ClaudeClient:
    """
    Client for interacting with Anthropic's Claude API.
    
    This class provides a simple interface for generating text using Claude models.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-sonnet-20240229"):
        """
        Initialize the Claude client.
        
        Args:
            api_key: Optional API key (will use environment variable if not provided)
            model: Claude model to use (default is claude-3-sonnet)
        """
        # Get API key from parameter or environment variable
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Claude API key must be provided or set in ANTHROPIC_API_KEY environment variable")
        
        # Store the model name
        self.model = model
        logger.info(f"Initializing Claude client with model: {self.model}")
        
        # Initialize the Anthropic client
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Generate text using Claude.
        
        Args:
            prompt: The prompt to send to Claude
            system_instruction: Optional system instructions
            temperature: Sampling temperature (0.0 to 1.0)
            max_output_tokens: Maximum number of tokens to generate
            
        Returns:
            Dictionary containing the generated text and metadata
        """
        try:
            logger.info(f"Generating text with Claude model: {self.model}")
            
            # Create the messages array
            messages = [{"role": "user", "content": prompt}]
            
            # Call the Claude API
            response = self.client.messages.create(
                model=self.model,
                system=system_instruction,
                messages=messages,
                temperature=temperature,
                max_tokens=max_output_tokens
            )
            
            # Extract the response text
            response_text = response.content[0].text
            
            return {
                "text": response_text,
                "model": self.model,
                "finish_reason": response.stop_reason,
                "usage": {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating text with Claude: {str(e)}")
            return {
                "text": f"Error generating text: {str(e)}",
                "model": self.model,
                "error": str(e)
            }
            
    def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Generate a chat completion using Claude's message API.
        
        Args:
            messages: List of message objects with 'role' and 'content'
            system_instruction: Optional system instructions
            temperature: Sampling temperature (0.0 to 1.0)
            max_output_tokens: Maximum number of tokens to generate
            
        Returns:
            Dictionary containing the generated text and metadata
        """
        try:
            logger.info(f"Generating chat completion with Claude model: {self.model}")
            
            # Call the Claude API
            response = self.client.messages.create(
                model=self.model,
                system=system_instruction,
                messages=messages,
                temperature=temperature,
                max_tokens=max_output_tokens
            )
            
            # Extract the response text
            response_text = response.content[0].text
            
            return {
                "text": response_text,
                "model": self.model,
                "finish_reason": response.stop_reason,
                "usage": {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating chat completion with Claude: {str(e)}")
            return {
                "text": f"Error generating chat completion: {str(e)}",
                "model": self.model,
                "error": str(e)
            } 