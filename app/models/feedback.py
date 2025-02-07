from datetime import datetime
from typing import Dict, Any, Optional

class Feedback:
    """Model for storing user feedback on compliance results."""
    
    VALID_RATINGS = ["Yes", "No", "Partial", "N/A"]
    
    def __init__(
        self,
        doi: str,
        item_id: str,
        rating: str,
        comments: str = "",
        created_at: Optional[datetime] = None
    ):
        """Initialize a feedback entry.
        
        Args:
            doi: DOI of the manuscript
            item_id: ID of the checklist item
            rating: User's rating (Yes/No/Partial/N/A)
            comments: Optional user comments
            created_at: Timestamp of feedback creation
        """
        if rating not in self.VALID_RATINGS:
            raise ValueError(f"Rating must be one of: {', '.join(self.VALID_RATINGS)}")
            
        self.doi = doi
        self.item_id = item_id
        self.rating = rating
        self.comments = comments
        self.created_at = created_at or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        return {
            "doi": self.doi,
            "item_id": self.item_id,
            "rating": self.rating,
            "comments": self.comments,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Feedback':
        """Create a Feedback instance from a dictionary."""
        return cls(
            doi=data["doi"],
            item_id=data["item_id"],
            rating=data["rating"],
            comments=data.get("comments", ""),
            created_at=data.get("created_at")
        )
