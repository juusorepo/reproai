from datetime import datetime
from typing import Dict, Any
from datetime import timezone

class ChecklistItem:
    def __init__(
        self,
        item_id: str,
        category: str,
        question: str,
        description: str = "",
        original: str = "",
        section: str = "",
        created_at: datetime = None,
        updated_at: datetime = None
    ):
        self.item_id = item_id
        self.category = category
        self.question = question
        self.description = description
        self.original = original
        self.section = section
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary for MongoDB storage."""
        return {
            "item_id": self.item_id,
            "category": self.category,
            "question": self.question,
            "description": self.description,
            "original": self.original,
            "section": self.section,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChecklistItem':
        """Create a ChecklistItem instance from a dictionary."""
        # Ensure timestamps are timezone-aware
        created_at = data.get("created_at")
        updated_at = data.get("updated_at")
        
        if created_at and created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        if updated_at and updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        
        return cls(
            item_id=data["item_id"],
            category=data["category"],
            question=data["question"],
            description=data.get("description", ""),
            original=data.get("original", ""),
            section=data.get("section", ""),
            created_at=created_at,
            updated_at=updated_at
        )
