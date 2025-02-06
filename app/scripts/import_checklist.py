import os
import json
from pathlib import Path
from dotenv import load_dotenv
from app.models.checklist_item import ChecklistItem
from app.services.db_service import DatabaseService

def import_checklist_items():
    """Import checklist items from JSON file to database."""
    # Load environment variables
    load_dotenv()
    
    # Initialize database service
    db_service = DatabaseService(os.getenv("MONGODB_URI"))
    
    # Get path to checklist file
    checklist_path = Path(__file__).parent.parent / "checklists" / "nhb_checklist.txt"
    
    print(f"Reading checklist from: {checklist_path}")
    
    try:
        # Read and parse checklist file
        with open(checklist_path, 'r', encoding='utf-8') as f:
            items = json.load(f)
        
        print(f"Found {len(items)} items")
        
        # Convert to ChecklistItem objects
        checklist_items = []
        for item in items:
            checklist_item = ChecklistItem(
                item_id=item["checklist_item_id"],
                category=item.get("title", "Uncategorized"),
                question=item["question"],
                original=item.get("original", ""),
                section=item.get("section", "")
            )
            checklist_items.append(checklist_item)
        
        # Save to database
        print("Saving items to database...")
        db_service.save_checklist_items(checklist_items)
        
        # Verify items were saved
        saved_items = db_service.get_checklist_items()
        print(f"Successfully saved {len(saved_items)} items")
        
        # Print first few items as example
        print("\nExample items:")
        for item in saved_items[:3]:
            print(f"- {item['item_id']}: {item['question']}")
            print(f"  Category: {item['category']}")
            print(f"  Original: {item['original']}")
            print(f"  Section: {item['section']}")
            print()
        
    except Exception as e:
        print(f"Error importing checklist items: {str(e)}")
        raise

if __name__ == "__main__":
    import_checklist_items()
