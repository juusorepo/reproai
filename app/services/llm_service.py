"""
LLM Service
----------

This module provides functions for interacting with OpenAI's API for various
text analysis and generation tasks.
"""

import os
from openai import OpenAI
from typing import Dict, Any, List

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
    max_tokens_output: int = MAX_TOKENS_OUTPUT
) -> str:
    """
    Get a response from OpenAI's API.
    
    Args:
        prompt: The prompt to send to the API
        system_prompt: The system message to set the behavior of the assistant
        temperature: Controls randomness in the response (0 to 1)
        max_tokens_output: Maximum number of tokens in the response
        
    Returns:
        The API's response text
    """
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found in environment variables")
    
    try:
        # Initialize client with just API key
        client = OpenAI(api_key=api_key)
        
        # Truncate prompt if needed
        max_prompt_tokens = MAX_TOKENS_TOTAL - len(system_prompt) // CHARS_PER_TOKEN - max_tokens_output
        truncated_prompt = truncate_to_token_limit(prompt, max_prompt_tokens)
        
        # Create chat completion
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",  # Using the latest model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": truncated_prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens_output
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        raise Exception(f"Error getting LLM response: {str(e)}")
