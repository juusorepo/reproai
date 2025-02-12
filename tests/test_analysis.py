"""
Test analysis functionality
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from app.services.pdf_extractor import PDFExtractor
from app.services.metadata_extractor import MetadataExtractor
from app.services.db_service import DatabaseService
from app.models.manuscript import Manuscript
import json
import traceback

def main():
    # Load environment variables
    load_dotenv()

    # Initialize services
    metadata_extractor = MetadataExtractor(os.getenv("OPENAI_API_KEY"))
    db_service = DatabaseService(os.getenv("MONGODB_URI"))

    # Get the first PDF from test folder
    test_dir = Path("data/manuscripts/test")
    pdf_files = list(test_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in data/manuscripts/test")
        return
    
    test_pdf = pdf_files[0]
    print(f"Processing: {test_pdf.name}")

    try:
        # Extract text from PDF
        print("Extracting text...")
        pdf_text = PDFExtractor.extract_text(str(test_pdf))
        print(f"Extracted {len(pdf_text)} characters")
        
        # Save first 200 chars for debugging
        print("\nFirst 200 characters of text:")
        print(pdf_text[:200])
        print("-" * 80)

        # Extract metadata using LLM
        print("\nExtracting metadata...")
        try:
            # Add more debugging output
            print("\nTesting metadata extraction with a small sample first:")
            test_text = """
            Test Title
            
            Test Author
            
            Abstract
            This is a test abstract.
            """
            print("\nTest metadata extraction:")
            test_metadata = metadata_extractor.extract_metadata(test_text)
            print("Test metadata result:", test_metadata)
            print("-" * 80)
            
            print("\nNow trying with actual manuscript text...")
            metadata = metadata_extractor.extract_metadata(pdf_text)
            print("Actual metadata result:", metadata)
            print("-" * 80)
            
            # Create Manuscript object
            manuscript = Manuscript(
                doi=metadata["doi"],
                title=metadata["title"],
                authors=metadata["authors"],
                abstract=metadata.get("abstract", ""),
                design=metadata.get("design", ""),
                pdf_path=str(test_pdf)
            )
        except Exception as e:
            print(f"Metadata extraction error details:")
            print(traceback.format_exc())
            raise e
        
        # Save to database
        print("\nSaving to database...")
        doi = db_service.save_manuscript(manuscript)
        
        # Print results
        print("\nResults:")
        print(json.dumps(metadata, indent=2))
        print(f"\nSaved with DOI: {doi}")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
