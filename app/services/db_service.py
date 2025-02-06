from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from typing import Dict, Any, List, Optional
from app.models.manuscript import Manuscript
from app.models.compliance_result import ComplianceResult
from app.models.checklist_item import ChecklistItem
from datetime import datetime

class DatabaseService:
    def __init__(self, uri: str):
        self.client = MongoClient(uri)
        self.db: Database = self.client.manuscript_db
        
        # Initialize collections
        self.manuscripts: Collection = self.db.manuscripts
        self.compliance_results: Collection = self.db.compliance_results
        self.checklist_items: Collection = self.db.checklist_items
        
        # Create indexes
        self._create_indexes()
    
    def _create_indexes(self):
        """Create necessary indexes for collections."""
        # Manuscript collection indexes
        self.manuscripts.create_index("doi", unique=True)
        
        # Compliance results collection indexes
        self.compliance_results.create_index([("doi", 1), ("item_id", 1)], unique=True)
        self.compliance_results.create_index("created_at")
        
        # Checklist items collection indexes
        self.checklist_items.create_index("item_id", unique=True)
        self.checklist_items.create_index("category")
    
    def save_manuscript(self, manuscript: Manuscript) -> str:
        """
        Save a manuscript to the database.
        
        Args:
            manuscript: Manuscript object to save
            
        Returns:
            DOI of the saved manuscript
        """
        data = manuscript.to_dict()
        
        # Update if exists, insert if not
        self.manuscripts.update_one(
            {"doi": data["doi"]},
            {"$set": data},
            upsert=True
        )
        
        return data["doi"]
    
    def save_compliance_result(self, doi: str, result: Dict[str, Any]) -> None:
        """
        Save a single compliance result to the database.
        
        Args:
            doi: DOI of the manuscript these results belong to
            result: ComplianceResult object to save
        """
        # Verify manuscript exists
        if not self.manuscripts.find_one({"doi": doi}):
            raise ValueError(f"No manuscript found with DOI: {doi}")
        
        # Add DOI and timestamp
        result["doi"] = doi
        if "created_at" not in result:
            result["created_at"] = datetime.now()
            
        # Update or insert
        self.compliance_results.update_one(
            {"doi": doi, "item_id": result["item_id"]},
            {"$set": result},
            upsert=True
        )
    
    def save_compliance_results(self, results: List[Dict[str, Any]], doi: str) -> None:
        """
        Save compliance results to the database.
        
        Args:
            results: List of ComplianceResult objects to save
            doi: DOI of the manuscript these results belong to
        """
        # Verify manuscript exists
        if not self.manuscripts.find_one({"doi": doi}):
            raise ValueError(f"No manuscript found with DOI: {doi}")
        
        # Save each result
        for result in results:
            self.save_compliance_result(doi, result)
    
    def save_checklist_item(self, item: ChecklistItem) -> str:
        """Save a checklist item to the database."""
        data = item.to_dict()
        self.checklist_items.update_one(
            {"item_id": data["item_id"]},
            {"$set": data},
            upsert=True
        )
        return data["item_id"]
    
    def save_checklist_items(self, items: List[ChecklistItem]) -> None:
        """Save multiple checklist items to the database."""
        for item in items:
            self.save_checklist_item(item)
    
    def get_checklist_items(self, category: str = None) -> List[Dict[str, Any]]:
        """Get all checklist items, optionally filtered by category."""
        query = {"category": category} if category else {}
        return list(self.checklist_items.find(query).sort("item_id", 1))
    
    def get_compliance_results(self, doi: str) -> List[Dict[str, Any]]:
        """
        Get all compliance results for a manuscript.
        
        Args:
            doi: DOI of the manuscript
            
        Returns:
            List of compliance results
        """
        return list(self.compliance_results.find({"doi": doi}))
    
    def get_manuscript(self, doi: str) -> Optional[Manuscript]:
        """
        Retrieve a manuscript by its DOI.
        
        Args:
            doi: Digital Object Identifier
            
        Returns:
            Manuscript object if found, None otherwise
        """
        data = self.manuscripts.find_one({"doi": doi})
        return Manuscript.from_dict(data) if data else None

    def list_manuscripts(self) -> list:
        """
        List all manuscripts in the database.
        
        Returns:
            List of manuscript documents
        """
        return list(self.manuscripts.find())
