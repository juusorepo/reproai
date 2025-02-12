"""
Manuscript Model
--------------

This module defines the Manuscript class which represents a scientific manuscript
in the system. It includes metadata about the manuscript and methods for database
operations.

The Manuscript class is used to:
1. Store manuscript metadata (title, authors, DOI, etc.)
2. Convert between Python objects and MongoDB documents
3. Track manuscript analysis status and timestamps
"""

from datetime import datetime
from typing import List, Dict, Any, Optional

class Manuscript:
    """A class representing a scientific manuscript.
    
    This class stores both the metadata about a manuscript (title, authors, etc.)
    and the extracted text content. It also tracks when the manuscript was created
    and last analyzed.
    
    Attributes:
        doi (str): Digital Object Identifier
        title (str): The title of the manuscript
        authors (List[str]): List of author names
        abstract (str): Abstract of the manuscript
        design (str): Study design type
        status (str): Status of the manuscript analysis
        analysis_date (datetime): When the manuscript was last analyzed
        pdf_path (str): Path to the manuscript PDF
        processed_at (datetime): When the manuscript was processed
    """
    
    def __init__(
        self,
        doi: str,
        title: str = "",
        authors: List[str] = None,
        abstract: str = "",
        design: str = "",
        status: str = "processed",
        analysis_date: Optional[datetime] = None,
        pdf_path: str = "",
        processed_at: Optional[datetime] = None
    ):
        """Initialize a new Manuscript instance.
        
        Args:
            doi: Digital Object Identifier
            title: The manuscript title
            authors: List of author names
            abstract: Abstract of the manuscript
            design: Study design type
            status: Status of the manuscript analysis
            analysis_date: When the manuscript was analyzed
            pdf_path: Path to the manuscript PDF
            processed_at: When the manuscript was processed
        """
        self.doi = doi
        self.title = title
        self.authors = authors or []
        self.abstract = abstract
        self.design = design
        self.status = status
        self.analysis_date = analysis_date or datetime.utcnow()
        self.pdf_path = pdf_path
        self.processed_at = processed_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the manuscript to a dictionary for MongoDB storage.
        
        Returns:
            Dict containing all manuscript data in a format suitable for MongoDB
        """
        return {
            "doi": self.doi,
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "design": self.design,
            "status": self.status,
            "analysis_date": self.analysis_date,
            "pdf_path": self.pdf_path,
            "processed_at": self.processed_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Manuscript':
        """Create a Manuscript instance from a dictionary.
        
        This is typically used when retrieving data from MongoDB.
        
        Args:
            data: Dictionary containing manuscript data
            
        Returns:
            A new Manuscript instance
        """
        return cls(
            doi=data["doi"],
            title=data.get("title", ""),
            authors=data.get("authors", []),
            abstract=data.get("abstract", ""),
            design=data.get("design", ""),
            status=data.get("status", "processed"),
            analysis_date=data.get("analysis_date"),
            pdf_path=data.get("pdf_path", ""),
            processed_at=data.get("processed_at")
        )
