"""
Test Metadata Extraction
-----------------------

This script tests the metadata extraction functionality by:
1. Loading a PDF file
2. Extracting text
3. Extracting metadata
4. Creating a manuscript object

Usage:
    python scripts/test_metadata_extract.py path/to/manuscript.pdf
"""

import os
import sys
import streamlit as st
from app.services.pdf_extractor import PDFExtractor
from app.services.metadata_extractor import MetadataExtractor
from app.models.manuscript import Manuscript

def test_metadata_extraction(pdf_path: str):
    """Test metadata extraction from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file to test
    """
    print(f"\nTesting metadata extraction for: {pdf_path}")
    print("-" * 80)
    
    # 1. Extract text from PDF
    print("\n1. Extracting text from PDF...")
    pdf_extractor = PDFExtractor()
    text = pdf_extractor.extract_text(pdf_path)
    
    if not text:
        print("ERROR: Could not extract text from PDF")
        return
    
    print(f"Successfully extracted {len(text)} characters")
    
    # 2. Extract metadata
    print("\n2. Extracting metadata...")
    api_key = st.secrets["OPENAI_API_KEY"]
    metadata_extractor = MetadataExtractor(api_key)
    metadata = metadata_extractor.extract_metadata(text)
    
    if not metadata:
        print("ERROR: Could not extract metadata")
        return
    
    print("\nExtracted metadata:")
    for key, value in metadata.items():
        print(f"{key}: {value}")
    
    # 3. Create manuscript object
    print("\n3. Creating manuscript object...")
    try:
        manuscript = Manuscript(
            title=metadata.get('title', 'Unknown Title'),
            authors=metadata.get('authors', []),
            doi=metadata.get('doi', ''),
            abstract=metadata.get('abstract', ''),
            text=text
        )
        print("Successfully created manuscript object")
        
        # Print manuscript details
        print("\nManuscript details:")
        print(f"Title: {manuscript.title}")
        print(f"Authors: {manuscript.authors}")
        print(f"DOI: {metadata.get('doi', 'Not found')}")
        print(f"Abstract: {metadata.get('abstract', 'Not found')[:100]}...")
        print(f"Email: {metadata.get('email', 'Not found')}")
        print(f"Discipline: {metadata.get('discipline', 'Not found')}")
        print(f"Abstract length: {len(manuscript.abstract)} chars")
        print(f"Text length: {len(manuscript.text)} chars")
        
    except Exception as e:
        print(f"ERROR creating manuscript: {str(e)}")
        return

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_metadata_extract.py path/to/manuscript.pdf")
        sys.exit(1)
        
    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"ERROR: File not found: {pdf_path}")
        sys.exit(1)
        
    test_metadata_extraction(pdf_path)
