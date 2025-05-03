"""
OpenAI API Client.

This module provides a client for interacting with OpenAI's API.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class OpenAIClient:
    """
    Client for interacting with OpenAI API.
    
    This class provides a simple interface for generating text using OpenAI models.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "o3"):
        """
        Initialize the OpenAI client.
        
        Args:
            api_key: Optional API key (will use environment variable if not provided)
            model: OpenAI model to use (default is o3)
        """
        # Get API key from parameter or environment variable
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set in OPENAI_API_KEY environment variable")
        
        # Store the model name
        self.model = model
        logger.info(f"Initializing OpenAI client with model: {self.model}")
        
        # Determine if this model needs max_completion_tokens instead of max_tokens (o-prefixed models)
        self.uses_completion_tokens = any(prefix in self.model.lower() for prefix in ["o1", "o2", "o3", "o4"])
        
        # Initialize the Async OpenAI client
        self.client = AsyncOpenAI(api_key=self.api_key)
        
    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Generate text using OpenAI.
        
        Args:
            prompt: The prompt to send to OpenAI
            system_instruction: Optional system instructions
            temperature: Sampling temperature (0.0 to 1.0)
            max_output_tokens: Maximum number of tokens to generate
            
        Returns:
            Dictionary containing the generated text and metadata
        """
        try:
            logger.info(f"Generating text with OpenAI model: {self.model}")
            
            # Prepare parameters
            params = {"model": self.model}
            # Only set temperature if the model supports it (not o4 models)
            if not self.uses_completion_tokens and temperature is not None:
                params["temperature"] = temperature
            # Use the correct parameter name based on model
            if self.uses_completion_tokens:
                if max_output_tokens is not None: params["max_completion_tokens"] = max_output_tokens
            else:
                if max_output_tokens is not None: params["max_tokens"] = max_output_tokens
            
            # Create messages array
            messages = []
            
            # Add system message if provided
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            
            # Add user message
            messages.append({"role": "user", "content": prompt})
            
            # Log the parameters being sent to the API
            logger.debug(f"Sending to OpenAI - Model: {params.get('model')}, Temp: {params.get('temperature')}, MaxTokensParam: {params.get('max_tokens')}, MaxCompletionTokensParam: {params.get('max_completion_tokens')}")
            logger.debug(f"Sending Messages: {messages}")
            
            # Call the OpenAI API asynchronously using the correct method for AsyncOpenAI
            response = await self.client.chat.completions.create(
                messages=messages,
                **params # Pass prepared parameters
            )
            
            logger.info(f"Received response from OpenAI: {response}")
            
            # Extract the response text
            response_text = response.choices[0].message.content
            
            return {
                "text": response_text,
                "model": self.model,
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating text with OpenAI: {str(e)}")
            return ""  # Return empty string on error

    async def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Generate a chat completion using OpenAI's chat API.
        
        Args:
            messages: List of message objects with 'role' and 'content'
            system_instruction: Optional system instructions
            temperature: Sampling temperature (0.0 to 1.0)
            max_output_tokens: Maximum number of tokens to generate
            
        Returns:
            Dictionary containing the generated text and metadata
        """
        try:
            logger.info(f"Generating chat completion with {self.model} using parameters: {messages}, {system_instruction}, {temperature}, {max_output_tokens}")
            
            # Prepare parameters
            params = {"model": self.model}
            # Only set temperature if the model supports it (not o4 models)
            if not self.uses_completion_tokens and temperature is not None:
                 params["temperature"] = temperature
            # Use the correct parameter name based on model
            if self.uses_completion_tokens:
                 if max_output_tokens is not None: params["max_completion_tokens"] = max_output_tokens
            else:
                if max_output_tokens is not None: params["max_tokens"] = max_output_tokens
            
            # Prepare complete messages array
            prepared_messages = []
            
            # Add system message if provided
            if system_instruction:
                prepared_messages.append({"role": "system", "content": system_instruction})
            
            # Add all other messages
            for message in messages:
                prepared_messages.append(message)
            
            # Use the async client and the correct method
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=prepared_messages,
                **params
            )
            
            # Extract the response text
            response_text = response.choices[0].message.content
            
            return {
                "text": response_text,
                "model": self.model,
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating chat completion: {str(e)}")
            return {
                "text": f"Error generating chat completion: {str(e)}",
                "model": self.model,
                "error": str(e)
            } 

# Create a default instance of the client for easy import
try:
    openai_client = OpenAIClient()
except ValueError as e:
    logger.error(f"Error initializing OpenAI client: {e}")
    # Handle the error appropriately, maybe exit or provide a dummy client
    openai_client = None # Or raise an exception, depending on desired behavior