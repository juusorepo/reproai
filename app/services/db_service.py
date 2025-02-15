"""
Database Service
--------------

This module provides database functionality for storing and retrieving
manuscript data, compliance results, and summaries.
"""

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from typing import Dict, Any, List, Optional
from app.models.manuscript import Manuscript
from app.models.compliance_result import ComplianceResult
from app.models.checklist_item import ChecklistItem
from app.models.feedback import Feedback
from datetime import datetime
from bson import ObjectId

class DatabaseService:
    def __init__(self, uri: str):
        self.client = MongoClient(uri)
        self.db: Database = self.client.manuscript_db
        
        # Initialize collections
        self.manuscripts: Collection = self.db.manuscripts
        self.compliance_results: Collection = self.db.compliance_results
        self.checklist_items: Collection = self.db.checklist_items
        self.feedback: Collection = self.db.feedback
        self.compliance_summaries: Collection = self.db.compliance_summaries
        
        # Create indexes
        self._create_indexes()
    
    def _create_indexes(self):
        """Create database indexes."""
        # Manuscript collection indexes
        self.manuscripts.create_index("doi", unique=True)
        
        # Compliance results collection indexes
        self.compliance_results.create_index([("doi", 1), ("item_id", 1)], unique=True)
        self.compliance_results.create_index("created_at")
        
        # Checklist items collection indexes
        self.checklist_items.create_index("item_id", unique=True)
        self.checklist_items.create_index("category")
        
        # New feedback indexes
        self.feedback.create_index([("doi", 1), ("item_id", 1)])
        self.feedback.create_index("created_at")
        
        # Compliance summaries indexes
        self.compliance_summaries.create_index("doi", unique=True)
        self.compliance_summaries.create_index("created_at")
    
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
    
    def get_compliance_results(self, doi: str) -> List[ComplianceResult]:
        """Get compliance results for a manuscript.
        
        Args:
            doi: DOI of the manuscript
            
        Returns:
            List of ComplianceResult objects
        """
        try:
            results = []
            cursor = self.compliance_results.find({"doi": doi})
            for doc in cursor:
                results.append(ComplianceResult.from_dict(doc))
            return results
        except Exception as e:
            print(f"Error getting compliance results: {str(e)}")
            return []
    
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

    def get_all_manuscripts(self) -> List[Manuscript]:
        """Get all manuscripts from the database.
        
        Returns:
            List of Manuscript objects
        """
        try:
            manuscripts = []
            cursor = self.manuscripts.find()
            for doc in cursor:
                manuscripts.append(Manuscript.from_dict(doc))
            return manuscripts
        except Exception as e:
            print(f"Error getting manuscripts: {str(e)}")
            return []

    def save_feedback(self, feedback: Feedback) -> bool:
        """Save user feedback for a compliance result.
        
        Args:
            feedback: Feedback instance to save
            
        Returns:
            bool: True if successful, False if error
        """
        try:
            # Convert to dict and save
            feedback_dict = feedback.to_dict()
            self.feedback.update_one(
                {"doi": feedback.doi, "item_id": feedback.item_id},
                {"$set": feedback_dict},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Error saving feedback: {str(e)}")
            return False
    
    def get_feedback(self, doi: str, item_id: str) -> Optional[Feedback]:
        """Get feedback for a specific compliance result.
        
        Args:
            doi: Manuscript DOI
            item_id: Checklist item ID
            
        Returns:
            Feedback instance if found, None otherwise
        """
        try:
            feedback_dict = self.feedback.find_one({"doi": doi, "item_id": item_id})
            if feedback_dict:
                return Feedback.from_dict(feedback_dict)
            return None
        except Exception as e:
            print(f"Error getting feedback: {str(e)}")
            return None
    
    def get_all_feedback(self, doi: str) -> List[Feedback]:
        """Get all feedback for a manuscript.
        
        Args:
            doi: Manuscript DOI
            
        Returns:
            List of Feedback instances
        """
        try:
            feedback_list = []
            cursor = self.feedback.find({"doi": doi})
            for feedback_dict in cursor:
                feedback_list.append(Feedback.from_dict(feedback_dict))
            return feedback_list
        except Exception as e:
            print(f"Error getting all feedback: {str(e)}")
            return []

    def get_all_feedback_by_item(self) -> Dict[str, List[Feedback]]:
        """Get all feedback grouped by item_id.
        
        Returns:
            Dictionary where key is item_id and value is list of Feedback instances
        """
        try:
            feedback_by_item = {}
            # Get all feedback in a single query
            cursor = self.feedback.find()
            for feedback_dict in cursor:
                feedback = Feedback.from_dict(feedback_dict)
                if feedback.item_id not in feedback_by_item:
                    feedback_by_item[feedback.item_id] = []
                feedback_by_item[feedback.item_id].append(feedback)
            return feedback_by_item
        except Exception as e:
            print(f"Error getting all feedback by item: {str(e)}")
            return {}

    def save_summary(self, doi: str, overview: str, category_summaries: List[Dict[str, Any]]) -> None:
        """Save a compliance summary to database.
        
        Args:
            doi: DOI of the manuscript
            overview: Overview section of the summary
            category_summaries: List of dictionaries containing:
                - category: Category name
                - summary: Category-specific summary
                - severity: Severity level (low, medium, high)
                - original_results: List of original compliance results
        """
        summary_doc = {
            "doi": doi,
            "overview": overview,
            "category_summaries": category_summaries,
            "created_at": datetime.now()
        }
        
        self.compliance_summaries.update_one(
            {"doi": doi},
            {"$set": summary_doc},
            upsert=True
        )
        
    def get_summary(self, doi: str) -> Optional[Dict[str, Any]]:
        """Get the compliance summary for a manuscript.
        
        Args:
            doi: DOI of the manuscript
            
        Returns:
            Dictionary containing:
                - overview: Overview section
                - category_summaries: List of dictionaries containing:
                    - category: Category name
                    - summary: Category-specific summary
                    - severity: Severity level (low, medium, high)
                    - original_results: List of original compliance results
                - created_at: Timestamp
            Returns None if not found
        """
        try:
            return self.compliance_summaries.find_one({"doi": doi})
        except Exception as e:
            print(f"Error getting summary: {str(e)}")
            return None
