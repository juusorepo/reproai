from datetime import datetime
from typing import Dict, Any, Optional

class ComplianceResult:
    def __init__(
        self,
        doi: str,
        item_id: str,
        question: str,
        compliance: str,
        explanation: str,
        quote: str = "",
        section: str = "",
        created_at: Optional[datetime] = None
    ):
        """Initialize a compliance result."""
        self.doi = doi
        self.item_id = item_id
        self.question = question
        self.compliance = compliance
        self.explanation = explanation
        self.quote = quote
        self.section = section
        self.created_at = created_at or datetime.now()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ComplianceResult':
        """Create a ComplianceResult from a dictionary."""
        return cls(
            doi=data["doi"],
            item_id=data["item_id"],
            question=data["question"],
            compliance=data["compliance"],
            explanation=data["explanation"],
            quote=data.get("quote", ""),
            section=data.get("section", ""),
            created_at=data.get("created_at", datetime.now())
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "doi": self.doi,
            "item_id": self.item_id,
            "question": self.question,
            "compliance": self.compliance,
            "explanation": self.explanation,
            "quote": self.quote,
            "section": self.section,
            "created_at": self.created_at
        }
