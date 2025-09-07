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
    
    def __init__(self, api_key: Optional[str] = None, model: str | None = None):
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
        
        # Store the model name (env override)
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        logger.info(f"Initializing OpenAI client with model: {self.model}")
        
        # Determine if this model uses the new Responses API (o*-series)
        m = (self.model or "").lower()
        self.is_o_series = (
            m.startswith("o1") or m.startswith("o2") or m.startswith("o3") or m.startswith("o4")
            or m.startswith("gpt-5")
        )
        # Some o-models require max_completion_tokens param name; chat models use max_tokens
        self.uses_completion_tokens = self.is_o_series
        
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

            if self.is_o_series:
                # Responses API for o-series models
                params: Dict[str, Any] = {"model": self.model}
                if max_output_tokens is not None:
                    params["max_completion_tokens"] = max_output_tokens
                # Temperature may not be supported/has different semantics; omit unless explicitly needed
                if system_instruction:
                    # For responses, prepend system instruction to the input
                    input_text = f"[SYSTEM]\n{system_instruction}\n\n[USER]\n{prompt}"
                else:
                    input_text = prompt
                response = await self.client.responses.create(
                    input=input_text,
                    **params
                )
                # Extract text from responses payload
                response_text = None
                try:
                    # Newer SDKs expose .output_text
                    response_text = getattr(response, "output_text", None)
                except Exception:
                    response_text = None
                if not response_text:
                    try:
                        # Fallback to walking the output array
                        out = getattr(response, "output", None) or []
                        if out and isinstance(out, list):
                            first = out[0]
                            content = getattr(first, "content", None) or []
                            if content and isinstance(content, list):
                                # content items may have .text
                                response_text = getattr(content[0], "text", None)
                    except Exception:
                        response_text = None
                response_text = response_text or ""
                return {"text": response_text, "model": self.model}
            else:
                # Chat Completions API for chat-capable models
                params: Dict[str, Any] = {"model": self.model}
                if temperature is not None:
                    params["temperature"] = temperature
                if max_output_tokens is not None:
                    params["max_tokens"] = max_output_tokens

                messages = []
                if system_instruction:
                    messages.append({"role": "system", "content": system_instruction})
                messages.append({"role": "user", "content": prompt})

                response = await self.client.chat.completions.create(
                    messages=messages,
                    **params
                )
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
            return {"text": f"", "model": self.model, "error": str(e)}

    async def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: int = 1000,
        response_format: Optional[Dict[str, Any]] = None
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
            
            if self.is_o_series:
                # Use Responses API pathway for o-series, join messages into a single input
                user_parts = []
                for msg in prepared_messages:
                    role = msg.get("role", "user").upper()
                    content = msg.get("content", "")
                    user_parts.append(f"[{role}]\n{content}")
                input_text = "\n\n".join(user_parts)
                params: Dict[str, Any] = {"model": self.model}
                if max_output_tokens is not None:
                    params["max_completion_tokens"] = max_output_tokens
                response = await self.client.responses.create(input=input_text, **params)
                response_text = getattr(response, "output_text", None) or ""
                return {"text": response_text, "model": self.model}
            else:
                # Use the async client and the Chat Completions API
                kwargs: Dict[str, Any] = {
                    "model": self.model,
                    "messages": prepared_messages,
                    **params,
                }
                if response_format is not None:
                    kwargs["response_format"] = response_format
                response = await self.client.chat.completions.create(**kwargs)
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