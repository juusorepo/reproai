"""
Compliance Summary Model
----------------------

This module defines the ComplianceSummary class which represents a summary
of compliance analysis results for a manuscript.
"""

from datetime import datetime
from typing import Dict, Any, Optional

class ComplianceSummary:
    """A class representing a summary of compliance analysis results.
    
    This class stores both an overview summary and category-specific summaries
    of the compliance analysis results for a manuscript.
    
    Attributes:
        doi (str): Digital Object Identifier of the manuscript
        overview (str): Overall summary of compliance analysis
        category_summaries (Dict[str, str]): Mapping of categories to their summaries
        created_at (datetime): When the summary was created
    """
    
    def __init__(
        self,
        doi: str,
        overview: str,
        category_summaries: Dict[str, str],
        created_at: Optional[datetime] = None
    ):
        """Initialize a new ComplianceSummary instance.
        
        Args:
            doi: Digital Object Identifier of the manuscript
            overview: Overall summary of compliance analysis
            category_summaries: Dictionary mapping categories to their summaries
            created_at: When the summary was created, defaults to now
        """
        self.doi = doi
        self.overview = overview
        self.category_summaries = category_summaries
        self.created_at = created_at or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the summary to a dictionary for MongoDB storage.
        
        Returns:
            Dictionary containing summary data
        """
        return {
            'doi': self.doi,
            'overview': self.overview,
            'category_summaries': self.category_summaries,
            'created_at': self.created_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ComplianceSummary':
        """Create a ComplianceSummary instance from a dictionary.
        
        Args:
            data: Dictionary containing summary data
            
        Returns:
            ComplianceSummary instance
        """
        return cls(
            doi=data['doi'],
            overview=data['overview'],
            category_summaries=data['category_summaries'],
            created_at=data.get('created_at')
        )
