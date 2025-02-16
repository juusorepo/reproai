from datetime import datetime
from typing import Dict, Any, Optional

class Feedback:
    """Model for storing user feedback on compliance results."""
    
    VALID_RATINGS = ["Yes", "No", "Partial", "N/A"]
    VALID_REVIEW_STATUS = ["agreed", "disagreed", "unsure"]
    
    def __init__(
        self,
        doi: str,
        item_id: str,
        review_status: str,
        rating: Optional[str] = None,
        comments: str = "",
        user_email: Optional[str] = None,
        created_at: Optional[datetime] = None
    ):
        """Initialize a feedback entry.
        
        Args:
            doi: DOI of the manuscript
            item_id: ID of the checklist item
            review_status: Review status (agreed/disagreed/unsure)
            rating: Optional user's rating (Yes/No/Partial/N/A)
            comments: Optional user comments
            user_email: Optional user email
            created_at: Timestamp of feedback creation
        """
        if rating is not None and rating not in self.VALID_RATINGS:
            raise ValueError(f"Rating must be one of: {', '.join(self.VALID_RATINGS)}")
        
        if review_status not in self.VALID_REVIEW_STATUS:
            raise ValueError(f"Review status must be one of: {', '.join(self.VALID_REVIEW_STATUS)}")
            
        self.doi = doi
        self.item_id = item_id
        self.rating = rating
        self.review_status = review_status
        self.comments = comments
        self.user_email = user_email
        self.created_at = created_at or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        return {
            "doi": self.doi,
            "item_id": self.item_id,
            "rating": self.rating,
            "review_status": self.review_status,
            "comments": self.comments,
            "user_email": self.user_email,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Feedback':
        """Create a Feedback instance from a dictionary."""
        return cls(
            doi=data["doi"],
            item_id=data["item_id"],
            rating=data.get("rating"),
            review_status=data.get("review_status", "disagreed"),  # Default for backward compatibility
            comments=data.get("comments", ""),
            user_email=data.get("user_email"),
            created_at=data.get("created_at", datetime.utcnow())
        )
