from datetime import datetime
from typing import Dict, Any

class ChecklistItem:
    def __init__(
        self,
        item_id: str,
        category: str,
        question: str,
        original: str = "",
        section: str = "",
        created_at: datetime = None
    ):
        self.item_id = item_id
        self.category = category
        self.question = question
        self.original = original
        self.section = section
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary for MongoDB storage."""
        return {
            "item_id": self.item_id,
            "category": self.category,
            "question": self.question,
            "original": self.original,
            "section": self.section,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChecklistItem':
        """Create a ChecklistItem instance from a dictionary."""
        return cls(
            item_id=data["item_id"],
            category=data["category"],
            question=data["question"],
            original=data.get("original", ""),
            section=data.get("section", ""),
            created_at=data.get("created_at")
        )
