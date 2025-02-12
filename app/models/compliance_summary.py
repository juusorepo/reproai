from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base

class ComplianceSummary(Base):
    __tablename__ = 'compliance_summaries'

    id = Column(Integer, primary_key=True)
    manuscript_id = Column(Integer, ForeignKey('manuscripts.id'), nullable=False)
    category_summaries = Column(JSON, nullable=False)  # Store category-wise summaries
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    manuscript = relationship("Manuscript", back_populates="compliance_summaries")

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'manuscript_id': self.manuscript_id,
            'category_summaries': self.category_summaries,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
