"""Test summarization of compliance results."""

import streamlit as st
from app.models.manuscript import Manuscript
from app.services.db_service import DatabaseService
from app.services.summarize_service import SummarizeService

def test_summarize_results():
    """Test generating and storing a summary of compliance results."""
    
    # Initialize services
    db_service = DatabaseService(st.secrets["MONGODB_URI"])
    summarize_service = SummarizeService(st.secrets["OPENAI_API_KEY"], db_service)
    
    # Test DOI
    doi = "10.1037/dev0001913"
    
    # Create test manuscript
    manuscript = Manuscript(
        doi=doi,
        title="Examining the Relationship Between Student Wellbeing and Academic Achievement",
        authors=["John Smith", "Jane Doe"]
    )
    
    # Get compliance results from database
    results = db_service.get_compliance_results(doi)
    print(f"\nFound {len(results)} compliance results\n")
    
    # Print sample of results
    print("Sample of compliance results:\n")
    for result in results[:2]:
        print(f"Item {result.item_id}:")
        print(f"Question: {result.question}")
        print(f"Compliance: {result.compliance}")
        print(f"Explanation: {result.explanation}")
        if hasattr(result, 'quote'):
            print(f"Quote: {result.quote}")
        if hasattr(result, 'section'):
            print(f"Section: {result.section}")
        print()
    
    print("Generating summary...")
    
    # Convert ComplianceResult objects to dictionaries
    results_dicts = [result.to_dict() for result in results]
    
    # Generate and save summary
    overview, category_summaries = summarize_service.summarize_results(results_dicts)
    
    print("\nGenerated Overview:")
    print(overview)
    print("\nCategory Summaries:")
    for summary in category_summaries:
        print(f"\n{summary['category']} (Severity: {summary['severity']}):")
        print(summary['summary'])
        print(f"Original Results: {len(summary['original_results'])} items")
    
    # Save summary to database
    db_service.save_summary(doi, overview, category_summaries)
    
    print("\nSummary saved to database.")
    
    # Verify saved summary
    saved_summary = db_service.get_summary(doi)
    if saved_summary:
        print("\nVerified saved summary:")
        print(f"Overview: {saved_summary['overview'][:100]}...")
        print("\nCategories:")
        for summary in saved_summary['category_summaries']:
            print(f"- {summary['category']} (Severity: {summary['severity']})")
            print(f"  Original Results: {len(summary['original_results'])} items")
    else:
        print("\nError: Could not retrieve saved summary")

if __name__ == "__main__":
    test_summarize_results()
