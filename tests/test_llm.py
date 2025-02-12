"""
Test LLM functionality
"""

import os
from dotenv import load_dotenv
from app.services.llm_service import get_llm_response
from app.services.metadata_extractor import MetadataExtractor

def test_simple_math():
    print("\nTesting simple math:")
    print("-" * 40)
    try:
        # Test simple prompt
        response = get_llm_response(
            prompt="What is 2+2?",
            system_prompt="You are a helpful math assistant. Answer only with the number.",
            temperature=0,
            max_tokens_output=10
        )
        print("Response:", response)
        
    except Exception as e:
        print(f"Error: {str(e)}")
    print("-" * 40)

def test_metadata_extraction():
    print("\nTesting metadata extraction:")
    print("-" * 40)
    try:
        # Test metadata extraction with a simple example
        test_text = """
        Effects of Exercise on Mental Health: A Randomized Trial
        
        John Smith1, Jane Doe2
        1Department of Psychology, 2Department of Health Sciences
        
        https://doi.org/10.1234/abcd.123
        
        Abstract
        This study examined the effects of exercise on mental health in a sample of participants.
        The randomized controlled trial was conducted over 12 months with 100 participants.
        """
        
        metadata_extractor = MetadataExtractor(os.getenv("OPENAI_API_KEY"))
        metadata = metadata_extractor.extract_metadata(test_text)
        print("Metadata:", metadata)
        
    except Exception as e:
        print(f"Error: {str(e)}")
    print("-" * 40)

def main():
    # Load environment variables
    load_dotenv()

    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    print(f"API key found: {'Yes' if api_key else 'No'}")

    # Run tests
    test_simple_math()
    test_metadata_extraction()

if __name__ == "__main__":
    main()
