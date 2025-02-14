"""
Test Summarize Script
-------------------

This script tests the summarization functionality for a given DOI.
It retrieves compliance results from the database and generates a new summary.
"""

import os
import streamlit as st
from app.services.db_service import DatabaseService
from app.services.summarize_service import SummarizeService
import json
from datetime import datetime
from bson import ObjectId
from app.models.compliance_result import ComplianceResult

class MongoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, ObjectId)):
            return str(obj)
        if isinstance(obj, ComplianceResult):
            return {
                "doi": obj.doi,
                "item_id": obj.item_id,
                "question": obj.question,
                "compliance": obj.compliance,
                "explanation": obj.explanation,
                "quote": obj.quote,
                "section": obj.section,
                "created_at": str(obj.created_at)
            }
        return super().default(obj)

def test_summarize(doi: str):
    """Test summarization for a given DOI."""
    print(f"\nGenerating summary for DOI: {doi}")
    
    # Initialize services
    db_service = DatabaseService(st.secrets["MONGODB_URI"])
    summarize_service = SummarizeService(st.secrets["OPENAI_API_KEY"], db_service)
    
    try:
        # Get compliance results for the DOI
        results = db_service.get_compliance_results(doi)
        if not results:
            print(f"No results found for DOI: {doi}")
            return
            
        print(f"\nFound {len(results)} compliance results")
        
        # Convert ComplianceResult objects to dicts
        results_dicts = [vars(result) for result in results]
        
        # Generate summaries
        overview, category_summaries = summarize_service.summarize_results(results_dicts)
        
        print("\n=== OVERVIEW ===")
        print(overview)
        
        print("\n=== CATEGORY SUMMARIES ===")
        for summary in category_summaries:
            category = summary['category']
            severity = summary['severity']
            content = summary['summary']
            
            # Print with color based on severity
            color = {
                'high': '\033[91m',    # Red
                'medium': '\033[93m',  # Yellow
                'low': '\033[92m'      # Green
            }.get(severity.lower(), '\033[0m')
            
            print(f"\n{color}{category} (Severity: {severity})\033[0m")
            print(f"Summary: {content}")
            
            # Save to database
            db_service.save_summary(doi, overview, category_summaries)
            
        # Save summaries as JSON for inspection
        output_dir = "test_output"
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, f"summary_{doi.replace('/', '_')}.json")
        with open(output_file, "w") as f:
            json.dump({
                "doi": doi,
                "overview": overview,
                "categories": category_summaries
            }, f, cls=MongoJSONEncoder, indent=2)
            
        print(f"\nSaved summary to {output_file}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print("Full error:", traceback.format_exc())

if __name__ == "__main__":
    # Get DOI from command line
    import sys
    if len(sys.argv) < 2:
        print("Usage: python test_summarize.py <doi>")
        exit(1)
        
    doi = sys.argv[1]
    test_summarize(doi)
