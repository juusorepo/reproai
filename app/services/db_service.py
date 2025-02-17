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
from datetime import datetime, timezone, UTC
from bson import ObjectId
import re

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
        self.users: Collection = self.db.users
        
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
        self.feedback.create_index("user_email")  # New index for user email
        
        # Compliance summaries indexes
        self.compliance_summaries.create_index("doi", unique=True)
        self.compliance_summaries.create_index("created_at")
        
        # Users collection indexes
        self.users.create_index("email", unique=True)
        self.users.create_index("created_at")

    def _validate_email(self, email: str) -> bool:
        """
        Validate email format using regex.
        
        Args:
            email: Email address to validate
            
        Returns:
            bool: True if email is valid, False otherwise
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def save_user(self, email: str) -> bool:
        """
        Save or update a user in the database.
        
        Args:
            email: User's email address
            
        Returns:
            bool: True if successful, False if email is invalid
            
        Raises:
            ValueError: If email is invalid
        """
        if not self._validate_email(email):
            raise ValueError("Invalid email format")
            
        user_data = {
            "email": email,
            "last_login": datetime.now(UTC)
        }
        
        # Update if exists, insert if not
        result = self.users.update_one(
            {"email": email},
            {
                "$set": {"last_login": user_data["last_login"]},
                "$setOnInsert": {"created_at": datetime.now(UTC)}
            },
            upsert=True
        )
        
        return True

    def get_user(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user data from database.
        
        Args:
            email: User's email address
            
        Returns:
            Optional[Dict]: User data if found, None otherwise
        """
        if not self._validate_email(email):
            raise ValueError("Invalid email format")
            
        return self.users.find_one({"email": email})
    
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
            result["created_at"] = datetime.now(UTC)
            
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
    
    def save_checklist_item(self, item: Dict[str, Any]) -> str:
        """
        Save a checklist item to the database.
        
        Args:
            item: Dictionary containing checklist item data
            
        Returns:
            str: ID of the saved item
        """
        # Generate item_id if not present
        if 'item_id' not in item:
            # Get highest existing item_id number
            latest_item = self.checklist_items.find_one(
                sort=[("item_id", -1)]
            )
            if latest_item and 'item_id' in latest_item:
                try:
                    last_num = float(latest_item['item_id'])
                    item['item_id'] = f"{last_num + 0.1:.1f}"
                except ValueError:
                    item['item_id'] = "1.1"
            else:
                item['item_id'] = "1.1"
        
        # Add timestamps if not present
        if 'created_at' not in item:
            item['created_at'] = datetime.now(UTC)
        item['updated_at'] = datetime.now(UTC)
        
        # Ensure required fields
        required_fields = ['category', 'question', 'description', 'section']
        missing_fields = [field for field in required_fields if field not in item]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        self.checklist_items.update_one(
            {"item_id": item["item_id"]},
            {"$set": item},
            upsert=True
        )
        return item["item_id"]
    
    def update_checklist_item(self, item: Dict[str, Any]) -> bool:
        """
        Update an existing checklist item.
        
        Args:
            item: Dictionary containing checklist item data with item_id
            
        Returns:
            bool: True if update was successful
            
        Raises:
            ValueError: If item_id is missing or required fields are not present
        """
        if 'item_id' not in item:
            raise ValueError("item_id is required for updating checklist item")
        
        # Ensure required fields
        required_fields = ['category', 'question', 'description', 'section']
        missing_fields = [field for field in required_fields if field not in item]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            
        # Add update timestamp
        item['updated_at'] = datetime.now(UTC)
        
        # Preserve created_at if it exists
        existing_item = self.checklist_items.find_one({"item_id": item["item_id"]})
        if existing_item and 'created_at' in existing_item:
            item['created_at'] = existing_item['created_at']
        
        result = self.checklist_items.update_one(
            {"item_id": item["item_id"]},
            {"$set": item}
        )
        
        return result.modified_count > 0
        
    def save_checklist_items(self, items: List[Dict[str, Any]]) -> None:
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

    def save_feedback(self, feedback: Feedback) -> None:
        """
        Save feedback to the database.
        
        Args:
            feedback: Feedback object to save
        """
        # Verify manuscript exists
        if not self.manuscripts.find_one({"doi": feedback.doi}):
            raise ValueError(f"No manuscript found with DOI: {feedback.doi}")
        
        # Verify user exists if email is provided
        if feedback.user_email and not self.users.find_one({"email": feedback.user_email}):
            raise ValueError(f"No user found with email: {feedback.user_email}")
        
        # Save feedback
        data = feedback.to_dict()
        self.feedback.insert_one(data)

    def get_feedback(self, doi: str, item_id: str, user_email: Optional[str] = None) -> Optional[Feedback]:
        """Get feedback for a specific compliance result.
        
        Args:
            doi: DOI of the manuscript
            item_id: ID of the checklist item
            user_email: Optional email of the user. If provided, only return feedback from this user
            
        Returns:
            Optional[Feedback]: Feedback if found, None otherwise
        """
        query = {"doi": doi, "item_id": item_id}
        if user_email:
            if not self._validate_email(user_email):
                raise ValueError("Invalid email format")
            query["user_email"] = user_email
            
        feedback_dict = self.feedback.find_one(query)
        if feedback_dict:
            return Feedback.from_dict(feedback_dict)
        return None
    
    def get_all_feedback(self, doi: str, user_email: Optional[str] = None) -> List[Feedback]:
        """Get all feedback for a manuscript.
        
        Args:
            doi: Manuscript DOI
            user_email: Optional email of the user. If provided, only return feedback from this user
            
        Returns:
            List[Feedback]: List of feedback instances
        """
        try:
            query = {"doi": doi}
            if user_email:
                if not self._validate_email(user_email):
                    raise ValueError("Invalid email format")
                query["user_email"] = user_email
                
            feedback_list = list(self.feedback.find(query))
            return [Feedback.from_dict(f) for f in feedback_list]
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

    def get_feedback_by_user(self, email: str) -> List[Dict[str, Any]]:
        """
        Get all feedback by a specific user.
        
        Args:
            email: User's email address
            
        Returns:
            List[Dict]: List of feedback items
        """
        if not self._validate_email(email):
            raise ValueError("Invalid email format")
            
        return list(self.feedback.find({"user_email": email}).sort("created_at", -1))

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
            "created_at": datetime.now(UTC)
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
