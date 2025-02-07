from datetime import datetime
from typing import List, Optional

class Manuscript:
    def __init__(
        self,
        doi: str,
        title: str,
        authors: List[str],
        abstract: str,
        design: Optional[str] = None,
        status: str = "processed",
        analysis_date: datetime = None,
        pdf_path: str = None,
        processed_at: datetime = None
    ):
        self.doi = doi
        self.title = title
        self.authors = authors
        self.abstract = abstract
        self.design = design
        self.status = status
        self.analysis_date = analysis_date or datetime.utcnow()
        self.pdf_path = pdf_path
        self.processed_at = processed_at

    def to_dict(self) -> dict:
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
    def from_dict(cls, data: dict) -> 'Manuscript':
        """Create a Manuscript instance from a dictionary.
        
        Args:
            data: Dictionary containing manuscript data
            
        Returns:
            Manuscript instance
        """
        return cls(
            doi=data["doi"],
            title=data["title"],
            authors=data["authors"],
            abstract=data.get("abstract", ""),
            design=data.get("design"),
            status=data.get("status", "processed"),
            analysis_date=data.get("analysis_date"),
            pdf_path=data.get("pdf_path"),
            processed_at=data.get("processed_at")
        )
