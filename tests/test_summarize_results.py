"""Test summarization of compliance results."""

import os
from dotenv import load_dotenv
from app.models.manuscript import Manuscript
from app.services.db_service import DatabaseService
from app.services.summarize_service import SummarizeService

# Load environment variables
load_dotenv()

def test_summarize_results():
    """Test generating and storing a summary of compliance results."""
    
    # Initialize services
    db_service = DatabaseService(os.getenv("MONGODB_URI"))
    summarize_service = SummarizeService(os.getenv("OPENAI_API_KEY"), db_service)
    
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
        if result.quote:
            print(f"Quote: {result.quote}")
        if result.section:
            print(f"Section: {result.section}")
        print()
    
    print("Generating summary...")
    
    # Generate and save summary
    summary = summarize_service.generate_summary(manuscript, results)
    
    print("\nGenerated Summary:")
    print("-" * 80)
    print(summary)
    print("-" * 80)
    
    print("\nSaving summary to database...")
    
    # Verify the saved summary
    print("\nVerifying saved summary...")
    saved_summary = db_service.get_summary(doi)
    
    if not saved_summary:
        raise Exception("Failed to save and retrieve summary")
        
    print("Summary successfully saved and retrieved\n")
    
    # Verify structure
    required_fields = ["overview", "category_summaries", "created_at"]
    for field in required_fields:
        if field not in saved_summary:
            raise Exception(f"Missing required field: {field}")
            
    # Verify category summaries structure
    for category in saved_summary["category_summaries"]:
        required_category_fields = ["category", "summary", "severity", "original_results"]
        for field in required_category_fields:
            if field not in category:
                raise Exception(f"Missing required category field: {field}")
                
    # Print saved summary for verification
    print("Saved Summary:")
    print("-" * 80)
    
    # Print overview
    print(saved_summary["overview"])
    print("\n### CATEGORY-BASED ISSUES:\n")
    
    # Print category summaries
    for category in saved_summary["category_summaries"]:
        print(f"**{category['category']}** (Severity: {category['severity'].upper()}):")
        print(f"- {category['summary']}")
        print(f"- Original results: {len(category['original_results'])} items\n")
    
    print("-" * 80)

if __name__ == "__main__":
    test_summarize_results()
