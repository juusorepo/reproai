import os
from dotenv import load_dotenv
from app.services.pdf_extractor import PDFExtractor
from app.services.compliance_analyzer import ComplianceAnalyzer
from app.services.db_service import DatabaseService
from app.models.manuscript import Manuscript
from app.models.compliance_result import ComplianceResult
import json
from datetime import datetime
from bson import ObjectId

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

def analyze_manuscript(pdf_path: str, doi: str):
    """Analyze a manuscript for compliance with first two checklist items."""
    print(f"\nProcessing: {os.path.basename(pdf_path)}")
    
    # Extract text from PDF
    print("Extracting text from PDF...")
    pdf_text = PDFExtractor.extract_text(pdf_path)
    print(f"Extracted {len(pdf_text)} characters\n")
    
    # Print first 200 characters as sample
    print("First 200 characters of text:")
    print("-" * 80)
    print(pdf_text[:200])
    print("-" * 80 + "\n")
    
    # Create manuscript object
    manuscript = Manuscript(
        doi=doi,
        title="Equitable Shifts in Youth Resilience?",
        authors=["Juuso Repo", "Sanna Herkama", "Christina Salmivalli"],
        abstract="",
        design="",
        pdf_path=pdf_path
    )
    
    print(f"Analyzing compliance for manuscript with DOI: {manuscript.doi}\n")
    
    # Get first two checklist items
    checklist_items = db_service.get_checklist_items()[:2]
    print(f"Testing with first {len(checklist_items)} checklist items")
    
    # Analyze compliance for each item
    print("\nAnalyzing compliance...")
    successful_analyses = 0
    failed_analyses = 0
    results = []
    
    for item in checklist_items:
        try:
            print(f"\nAnalyzing item {item['item_id']}: {item['question']}")
            result = compliance_analyzer.analyze_item(manuscript, pdf_text, item)
            results.append(result)
            
            # Save result to database
            db_service.save_compliance_result(manuscript.doi, result)
            print(f"Saved result for item {item['item_id']} to database")
            successful_analyses += 1
            
            # Print result details
            print(f"Compliance: {result['compliance']}")
            print(f"Explanation: {result['explanation']}")
            if result.get('quote'):
                print(f"Quote: {result['quote']}")
            if result.get('section'):
                print(f"Section: {result['section']}")
                
        except Exception as e:
            print(f"Error analyzing item {item['item_id']}: {str(e)}")
            failed_analyses += 1
            continue
    
    # Print analysis summary
    print(f"\nCompliance analysis complete:")
    print(f"- Successful analyses: {successful_analyses}")
    print(f"- Failed analyses: {failed_analyses}")
    print(f"- Total items processed: {len(results)}")
    
    # Verify saved results
    print("\nVerifying saved results...")
    saved_results = db_service.get_compliance_results(manuscript.doi)
    print(f"Found {len(saved_results)} saved results")
    print("Latest two results:")
    print(json.dumps(saved_results[:2], indent=2, cls=MongoJSONEncoder))

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Initialize services
    db_service = DatabaseService(os.getenv("MONGODB_URI"))
    compliance_analyzer = ComplianceAnalyzer(os.getenv("OPENAI_API_KEY"), db_service)
    
    # Test manuscript
    pdf_path = "data/manuscripts/test/Repoetal_orig.pdf"
    doi = "10.1037/dev0001913"
    
    # Run analysis
    analyze_manuscript(pdf_path, doi)
