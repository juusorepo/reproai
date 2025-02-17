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
        email (str): Email of the corresponding/first author
        discipline (str): Academic field classification
        status (str): Status of the manuscript analysis
        analysis_date (datetime): When the manuscript was last analyzed
        pdf_path (str): Path to the manuscript PDF
        processed_at (datetime): When the manuscript was processed
        text (str): Full text content of the manuscript
    """
    
    def __init__(
        self,
        doi: str,
        title: str = "",
        authors: List[str] = None,
        abstract: str = "",
        design: str = "",
        email: str = "",
        discipline: str = "",
        status: str = "processed",
        analysis_date: Optional[datetime] = None,
        pdf_path: str = "",
        processed_at: Optional[datetime] = None,
        text: str = ""
    ):
        """Initialize a new Manuscript instance.
        
        Args:
            doi: Digital Object Identifier
            title: Title of the manuscript
            authors: List of author names
            abstract: Abstract of the manuscript
            design: Study design type
            email: Email of the corresponding/first author
            discipline: Academic field classification
            status: Analysis status
            analysis_date: When the manuscript was analyzed
            pdf_path: Path to the PDF file
            processed_at: When the manuscript was processed
            text: Full text content
        """
        self.doi = doi
        self.title = title
        self.authors = authors or []
        self.abstract = abstract
        self.design = design
        self.email = email
        self.discipline = discipline
        self.status = status
        self.analysis_date = analysis_date or datetime.now()
        self.pdf_path = pdf_path
        self.processed_at = processed_at or datetime.now()
        self.text = text

    def to_dict(self) -> Dict[str, Any]:
        """Convert the manuscript to a dictionary for database storage."""
        return {
            "doi": self.doi,
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "design": self.design,
            "email": self.email,
            "discipline": self.discipline,
            "status": self.status,
            "analysis_date": self.analysis_date,
            "pdf_path": self.pdf_path,
            "processed_at": self.processed_at,
            "text": self.text
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
            email=data.get("email", ""),
            discipline=data.get("discipline", ""),
            status=data.get("status", "processed"),
            analysis_date=data.get("analysis_date"),
            pdf_path=data.get("pdf_path", ""),
            processed_at=data.get("processed_at"),
            text=data.get("text", "")
        )
