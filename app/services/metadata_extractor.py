import openai
from typing import Dict, Any
import json
from pathlib import Path

class MetadataExtractor:
    def __init__(self, api_key: str):
        openai.api_key = api_key
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
            # Format the prompt with the manuscript text
            # Use str.replace instead of format to avoid issues with special characters
            prompt = self.prompt_template.replace("{text}", text[:5000])
            
            print("\nPrompt sent to LLM:")
            print("-" * 80)
            print(prompt)
            print("-" * 80)

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Extract metadata from scientific manuscripts. Return only the requested fields as a valid JSON object."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )

            # Get and log the raw response
            raw_response = response.choices[0].message.content
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
