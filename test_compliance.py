import os
from dotenv import load_dotenv
from app.services.pdf_extractor import PDFExtractor
from app.services.compliance_analyzer import ComplianceAnalyzer
from app.services.db_service import DatabaseService
from app.models.manuscript import Manuscript
import json
from datetime import datetime
from bson import ObjectId

class MongoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, ObjectId)):
            return str(obj)
        return super().default(obj)

def analyze_manuscript(pdf_path: str, doi: str):
    """Analyze a manuscript for compliance with checklist items."""
    print(f"Processing: {os.path.basename(pdf_path)}")
    
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
    
    # Get all checklist items
    checklist_items = db_service.get_checklist_items()
    print(f"Found {len(checklist_items)} checklist items to analyze")
    
    # Analyze compliance for each item
    print("\nAnalyzing compliance...")
    results = []
    for item in checklist_items:
        print(f"\nAnalyzing item {item['item_id']}: {item['question']}")
        result = compliance_analyzer.analyze_item(manuscript, pdf_text, item)
        results.append(result)
        
        # Save result to database
        db_service.save_compliance_result(manuscript.doi, result)
    
    # Verify saved results
    print("\nVerifying saved results...")
    saved_results = db_service.get_compliance_results(manuscript.doi)
    print(f"Found {len(saved_results)} saved results")
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
