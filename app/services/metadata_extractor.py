from typing import Dict, Any
import json
from pathlib import Path
from .llm_service import get_llm_response, MAX_TOKENS_INPUT, CHARS_PER_TOKEN

class MetadataExtractor:
    def __init__(self, api_key: str):
        self.api_key = api_key
        prompt_file = Path(__file__).parent.parent / "prompts" / "metadata_extraction.txt"
        with open(prompt_file, 'r', encoding='utf-8') as f:
            self.prompt_template = f.read()

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
            # Use str.replace instead of format to avoid issues with special characters
            prompt = self.prompt_template.replace("{text}", text_for_metadata)
            
            print("\nPrompt sent to LLM:")
            print("-" * 80)
            print(prompt)
            print("-" * 80)

            # Get response from LLM service
            raw_response = get_llm_response(
                prompt=prompt,
                system_prompt="Extract metadata from scientific manuscripts. Return only the requested fields as a valid JSON object.",
                temperature=0.1,
                max_tokens_output=2000  # Metadata response should be relatively short
            )

            print("\nRaw LLM response:")
            print("-" * 80)
            print(raw_response)
            print("-" * 80)

            # Parse the JSON response
            result = json.loads(raw_response)
            
            return {
                "doi": result.get("doi", ""),
                "title": result.get("title", ""),
                "authors": result.get("authors", []),
                "abstract": result.get("abstract", ""),
                "design": result.get("design", "")
            }
            
        except Exception as e:
            print("\nError details:")
            print(f"Type: {type(e).__name__}")
            print(f"Message: {str(e)}")
            if isinstance(e, json.JSONDecodeError):
                print(f"JSON error at position: {e.pos}")
                print(f"Line number: {e.lineno}")
                print(f"Column: {e.colno}")
            raise Exception(f"Error extracting metadata: {str(e)}")
