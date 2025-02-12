"""
Metadata Extractor Service
-------------------------

This module provides functionality to extract metadata from manuscript text using LLM.
"""

from typing import Dict, Any
import json
import re
import logging
from pathlib import Path
from jsonschema import validate
from .llm_service import get_llm_response, MAX_TOKENS_INPUT, CHARS_PER_TOKEN

# Configure logging
logger = logging.getLogger(__name__)

# Define JSON schema for metadata
METADATA_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "authors": {
            "type": "array",
            "items": {"type": "string"}
        },
        "design": {"type": "string"},
        "doi": {"type": "string"},
        "abstract": {"type": "string"}
    },
    "required": ["title", "authors"]
}

class MetadataExtractor:
    def __init__(self, api_key: str):
        self.api_key = api_key
        prompt_file = Path(__file__).parent.parent / "prompts" / "metadata_extraction.txt"
        with open(prompt_file, 'r', encoding='utf-8') as f:
            self.prompt_template = f.read()

    def _clean_llm_response(self, response: str) -> str:
        """
        Clean the LLM response by removing any markdown formatting.
        
        Args:
            response: Raw response from LLM
            
        Returns:
            Cleaned response with only the JSON content
        """
        # Remove markdown code block markers if present
        response = re.sub(r'^```json\s*', '', response)
        response = re.sub(r'\s*```$', '', response)
        
        # Remove any leading/trailing whitespace
        response = response.strip()
        
        return response

    def extract_metadata(self, text: str) -> Dict[str, Any]:
        """
        Extract metadata from text using LLM.
        
        Args:
            text: Text content from the PDF
            
        Returns:
            Dictionary containing title, authors, abstract, and study design
        """
        try:
            # For metadata extraction, we only need the first part of the manuscript
            # This typically contains the title, authors, abstract, and study design
            # Use approximately 25% of our max input tokens
            max_chars = (MAX_TOKENS_INPUT // 4) * CHARS_PER_TOKEN
            text_for_metadata = text[:max_chars]
            
            # Format the prompt with the manuscript text
            try:
                prompt = self.prompt_template.replace("{text}", text_for_metadata)
                logger.info("Prompt preparation successful")
            except Exception as e:
                logger.error(f"Error during prompt preparation: {type(e).__name__}: {str(e)}")
                if isinstance(e, UnicodeEncodeError):
                    logger.error(f"Encoding error at position {e.start}-{e.end}")
                    logger.error(f"Problematic character: {e.object[e.start:e.end]}")
                    logger.error(f"Unicode value: {hex(ord(e.object[e.start]))}")
                raise

            # Get response from LLM service using function calling
            functions = [{
                "name": "extract_metadata",
                "description": "Extract metadata from manuscript text",
                "parameters": METADATA_SCHEMA
            }]
            
            try:
                raw_response = get_llm_response(
                    prompt=prompt,
                    system_prompt="Extract metadata from scientific manuscripts. Return only the requested fields as a valid JSON object.",
                    temperature=0.1,
                    max_tokens_output=2000,  # Metadata response should be relatively short
                    functions=functions,
                    function_call={"name": "extract_metadata"}
                )
                logger.info("LLM response received successfully")
            except Exception as e:
                logger.error(f"Error during LLM call: {type(e).__name__}: {str(e)}")
                if isinstance(e, UnicodeEncodeError):
                    logger.error(f"Encoding error at position {e.start}-{e.end}")
                    logger.error(f"Problematic character: {e.object[e.start:e.end]}")
                    logger.error(f"Unicode value: {hex(ord(e.object[e.start]))}")
                raise

            # Clean and parse the JSON response
            try:
                cleaned_response = self._clean_llm_response(raw_response)
                logger.info("Response cleaned successfully")
            except Exception as e:
                logger.error(f"Error during response cleaning: {type(e).__name__}: {str(e)}")
                raise
            
            try:
                result = json.loads(cleaned_response)
                logger.info("JSON parsing successful")
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error at position {e.pos}, line {e.lineno}, column {e.colno}")
                logger.error(f"Problematic JSON: {cleaned_response}")
                raise Exception("Failed to parse LLM response as JSON") from e
                
            try:
                # Validate against schema
                validate(instance=result, schema=METADATA_SCHEMA)
                logger.info("Schema validation successful")
            except Exception as e:
                logger.error(f"JSON schema validation error: {str(e)}")
                logger.error(f"Invalid JSON: {json.dumps(result, indent=2)}")
                raise Exception("LLM response failed schema validation") from e
            
            return {
                "doi": result.get("doi", ""),
                "title": result.get("title", ""),
                "authors": result.get("authors", []),
                "abstract": result.get("abstract", ""),
                "design": result.get("design", "")
            }
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {type(e).__name__}: {str(e)}")
            if isinstance(e, UnicodeEncodeError):
                logger.error(f"Encoding error at position {e.start}-{e.end}")
                logger.error(f"Problematic character: {e.object[e.start:e.end]}")
                logger.error(f"Unicode value: {hex(ord(e.object[e.start]))}")
            raise
