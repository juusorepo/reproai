"""
LLM Service
----------

This module provides functions for interacting with OpenAI's API for various
text analysis and generation tasks.
"""

import os
import logging
from openai import OpenAI
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# GPT-4 Turbo has a 128K token context window
MAX_TOKENS_TOTAL = 128000  # Total tokens in context window
MAX_TOKENS_INPUT = 100000  # Reserve ~100K for input
MAX_TOKENS_OUTPUT = 4000   # Reserve 4K for output
CHARS_PER_TOKEN = 4        # Approximate characters per token

def estimate_tokens(text: str) -> int:
    """
    Estimate the number of tokens in a text.
    This is a rough estimate based on average characters per token.
    
    Args:
        text: Text to estimate tokens for
        
    Returns:
        Estimated number of tokens
    """
    return len(text) // CHARS_PER_TOKEN

def truncate_to_token_limit(text: str, max_tokens: int = MAX_TOKENS_INPUT) -> str:
    """
    Truncate text to fit within token limit.
    Takes text from the end as it often contains the most relevant information.
    
    Args:
        text: Text to truncate
        max_tokens: Maximum number of tokens allowed
        
    Returns:
        Truncated text
    """
    estimated_tokens = estimate_tokens(text)
    if estimated_tokens <= max_tokens:
        return text
        
    # Take text from the end as it often contains the most relevant information
    max_chars = max_tokens * CHARS_PER_TOKEN
    return text[-max_chars:]

def get_llm_response(
    prompt: str,
    system_prompt: str = "You are a helpful assistant that analyzes scientific manuscripts for reproducibility compliance.",
    temperature: float = 0,
    max_tokens_output: int = MAX_TOKENS_OUTPUT,
    functions: List[Dict[str, Any]] = None,
    function_call: Dict[str, str] = None,
    response_format: Dict[str, str] = None
) -> str:
    """
    Get a response from OpenAI's API.
    
    Args:
        prompt: The prompt to send to the API
        system_prompt: The system message to set the behavior of the assistant
        temperature: Controls randomness in the response (0 to 1)
        max_tokens_output: Maximum number of tokens in the response
        functions: Optional list of function definitions for function calling
        function_call: Optional dictionary specifying which function to call
        response_format: Optional dictionary specifying the response format (e.g., {"type": "json_object"})
        
    Returns:
        The API's response text, either direct content or function call result
    """
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OpenAI API key not found in environment variables")
        raise ValueError("OpenAI API key not found in environment variables")
    
    try:
        # Initialize client with just API key
        logger.info("Initializing OpenAI client")
        client = OpenAI(api_key=api_key)
        
        # Truncate prompt if needed
        logger.info("Preparing prompt")
        max_prompt_tokens = MAX_TOKENS_TOTAL - len(system_prompt) // CHARS_PER_TOKEN - max_tokens_output
        truncated_prompt = truncate_to_token_limit(prompt, max_prompt_tokens)
        
        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": truncated_prompt}
        ]
        
        # Prepare API call arguments
        logger.info("Creating chat completion arguments")
        completion_args = {
            "model": "gpt-4-turbo-preview",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens_output
        }
        
        # Add functions if provided
        if functions:
            completion_args["tools"] = [{"type": "function", "function": f} for f in functions]
        if function_call:
            completion_args["tool_choice"] = {"type": "function", "function": function_call}
        if response_format:
            completion_args["response_format"] = response_format
        
        # Make API call
        logger.info("Making API call to OpenAI")
        try:
            # Print input for debugging
            print("\nLLM Input:")
            print("-" * 80)
            for msg in messages:
                print(f"{msg['role'].upper()}: {msg['content'][:500]}...")
            print("-" * 80)

            response = client.chat.completions.create(**completion_args)
            logger.info("API call successful")
            
            # Process response
            logger.info("Processing API response")
            if functions and response.choices[0].message.tool_calls:
                # Return function call arguments
                content = response.choices[0].message.tool_calls[0].function.arguments
            else:
                logger.info("Extracting message content")
                content = response.choices[0].message.content

            # Print response for debugging
            print("\nLLM Response:")
            print("-" * 80)
            print(content)
            print("-" * 80)

            return content
            
        except Exception as e:
            logger.error(f"API call failed: {type(e).__name__}: {str(e)}")
            if hasattr(e, 'response'):
                logger.error(f"API response: {e.response}")
            raise Exception(f"OpenAI API call failed: {str(e)}")
        
    except Exception as e:
        logger.error(f"LLM service error: {type(e).__name__}: {str(e)}")
        if hasattr(e, '__traceback__'):
            logger.error("Traceback:", exc_info=True)
        raise Exception(f"Error getting LLM response: {str(e)}")
