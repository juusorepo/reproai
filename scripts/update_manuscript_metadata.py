"""
Script to update existing manuscripts with missing discipline, study design, and email metadata.
"""

import os
import sys
import json
import time
from pathlib import Path

# Add the parent directory to sys.path to import app modules
parent_dir = str(Path(__file__).parent.parent)
sys.path.append(parent_dir)

from app.services.db_service import DatabaseService
from app.services.llm_service import get_llm_response, truncate_to_token_limit, MAX_TOKENS_INPUT
from app.models.manuscript import Manuscript

METADATA_PROMPT = """You are extracting metadata from a scientific manuscript.
Return ONLY a valid JSON object with no additional text or formatting.

Required fields:
1. "design" (string): a concise 3-5 word phrase summarizing the study design / methodology. Be generic, not too specific.
2. "discipline" (string): A detailed classification of the manuscript's academic field. Use a specific term that best describes the study's field (e.g., "Cognitive Psychology", "Molecular Biology", "Educational Technology", "Biomedical Engineering"). If uncertain, provide the best possible match.
3. "email" (string): Email address of the corresponding or first author, leave empty if not found.

Example:
{"design":"Randomized controlled trial","discipline":"Clinical Psychology","email":"john.smith@university.edu"}

Important:
- Return ONLY a valid JSON object
- Do not include any explanations or additional text
- Focus only on design, discipline and email fields
- Use the manuscript's content to determine these fields
- If a field cannot be determined, use an empty string
"""

def update_manuscript_metadata(manuscript: Manuscript, text: str, db_service: DatabaseService) -> bool:
    """Update a manuscript's metadata if discipline, design, or email is missing."""
    needs_update = False
    
    # Check if any field is missing or empty
    if not manuscript.discipline or not manuscript.design or not manuscript.email:
        needs_update = True
    
    if not needs_update:
        return False
        
    try:
        # Use text if available, otherwise use abstract
        content_to_analyze = text if text else manuscript.abstract
        if not content_to_analyze:
            print(f"No text or abstract found for manuscript {manuscript.doi}")
            return False
            
        # Truncate text to fit token limit
        content_to_analyze = truncate_to_token_limit(content_to_analyze, MAX_TOKENS_INPUT)
        
        # Call LLM to extract metadata
        response = get_llm_response(
            prompt=content_to_analyze,
            system_prompt=METADATA_PROMPT,
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        # Parse the response
        metadata = json.loads(response)
        
        # Update only if fields are missing
        if not manuscript.discipline and metadata.get('discipline'):
            manuscript.discipline = metadata['discipline']
        if not manuscript.design and metadata.get('design'):
            manuscript.design = metadata['design']
        if not manuscript.email and metadata.get('email'):
            manuscript.email = metadata['email']
            
        # Save the updated manuscript
        db_service.save_manuscript(manuscript)
        return True
        
    except Exception as e:
        print(f"Error updating metadata for manuscript {manuscript.doi}: {str(e)}")
        return False

def main():
    # Initialize Streamlit secrets (even though we're not running a Streamlit app)
    import streamlit as st
    
    # Get MongoDB URI from secrets
    mongodb_uri = st.secrets["MONGODB_URI"]
    if not mongodb_uri:
        print("Error: MONGODB_URI not found in Streamlit secrets!")
        sys.exit(1)
    
    # Initialize services
    db_service = DatabaseService(mongodb_uri)
    
    # Get all manuscripts
    manuscripts = db_service.get_all_manuscripts()
    total = len(manuscripts)
    updated = 0
    errors = 0
    skipped = 0
    
    print(f"Found {total} manuscripts to process")
    
    for i, manuscript in enumerate(manuscripts, 1):
        print(f"\nProcessing manuscript {i}/{total}: {manuscript.doi}")
        print(f"Current discipline: {manuscript.discipline}")
        print(f"Current design: {manuscript.design}")
        print(f"Current email: {manuscript.email}")
        
        # Skip if no text and no abstract
        if (not hasattr(manuscript, 'text') or not manuscript.text) and not manuscript.abstract:
            print(f"Skipping manuscript {manuscript.doi} - no text or abstract content")
            skipped += 1
            continue
        
        # Skip if all fields are already populated
        if manuscript.discipline and manuscript.design and manuscript.email:
            print("Skipping - all fields already set")
            skipped += 1
            continue
            
        try:
            # Add delay to respect rate limits
            time.sleep(1)
            
            # Update metadata
            if update_manuscript_metadata(manuscript, manuscript.text if hasattr(manuscript, 'text') else None, db_service):
                print(f"Updated metadata:")
                print(f"New discipline: {manuscript.discipline}")
                print(f"New design: {manuscript.design}")
                print(f"New email: {manuscript.email}")
                updated += 1
            else:
                print("No update needed or update failed")
                
        except Exception as e:
            print(f"Error processing manuscript {manuscript.doi}: {str(e)}")
            errors += 1
            
    print(f"\nProcessing complete!")
    print(f"Total manuscripts: {total}")
    print(f"Successfully updated: {updated}")
    print(f"Skipped (no content/already complete): {skipped}")
    print(f"Errors: {errors}")

if __name__ == "__main__":
    main()
