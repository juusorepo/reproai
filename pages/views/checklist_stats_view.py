"""
ReproAI - Checklist Statistics View
---------------------------------

This module provides statistical analysis functions for checklist items.

Author: ReproAI Team
"""
from datetime import datetime
from typing import List, Dict, Optional, Any, Union

def filter_manuscripts(manuscripts: List[Any], filters: Dict[str, Any]) -> List[Any]:
    """Filter manuscripts based on provided criteria.
    
    Args:
        manuscripts: List of manuscripts to filter
        filters: Dictionary of filter criteria:
            - discipline: Optional[str] - Filter by discipline
            - design: Optional[str] - Filter by study design
            - processed_after: Optional[datetime] - Filter by processed_at date (after)
            - processed_before: Optional[datetime] - Filter by processed_at date (before)
            
    Returns:
        List[Any]: Filtered list of manuscripts
    """
    filtered = manuscripts
    
    if filters.get('discipline'):
        filtered = [m for m in filtered if m.discipline == filters['discipline']]
        
    if filters.get('design'):
        filtered = [m for m in filtered if m.design == filters['design']]
        
    if filters.get('processed_after'):
        filtered = [m for m in filtered if m.processed_at and m.processed_at >= filters['processed_after']]
        
    if filters.get('processed_before'):
        filtered = [m for m in filtered if m.processed_at and m.processed_at <= filters['processed_before']]
        
    return filtered

def get_unique_values(manuscripts: List[Any], field: str) -> List[str]:
    """Get list of unique values for a given field in manuscripts.
    
    Args:
        manuscripts: List of manuscripts
        field: Field name to get unique values for
        
    Returns:
        List[str]: List of unique values
    """
    values = set()
    for m in manuscripts:
        value = getattr(m, field, None)
        if value:
            values.add(value)
    return sorted(list(values))

def calculate_compliance_score(compliances: list, filters: Optional[Dict[str, Any]] = None) -> float:
    """Calculate compliance score from a list of compliance values.
    
    Args:
        compliances: List of compliance values
        filters: Optional dictionary of filter criteria
        
    Returns:
        float: Compliance score percentage
    """
    scores = {
        "Yes": 1.0,
        "No": 0.0,
        "Partial": 0.5,
        "n/a": None
    }
    valid_scores = [scores[c] for c in compliances if scores[c] is not None]
    return int(round(sum(valid_scores) / len(valid_scores) * 100)) if valid_scores else 0

def format_compliance_status(status: str) -> str:
    """Format compliance status with color."""
    colors = {
        "Yes": "#2ecc71",
        "No": "#e74c3c",
        "Partial": "#f1c40f",
        "n/a": "#95a5a6"
    }
    return f"<span style='color: {colors[status]}'>{status}</span>"

def calculate_accuracy(results: List[Any], feedback_list: List[Any], filters: Optional[Dict[str, Any]] = None) -> Optional[float]:
    """Calculate accuracy of AI assessments based on user feedback.
    
    Args:
        results: List of compliance results
        feedback_list: List of feedback for the item
        filters: Optional dictionary of filter criteria
        
    Returns:
        Optional[float]: Accuracy percentage or None if no reviewed items
    """
    # Filter results if filters provided
    if filters:
        results = filter_manuscripts(results, filters)
    
    total_reviewed = 0
    correct_assessments = 0
    
    # Create a map of feedback by DOI for faster lookup
    feedback_by_doi = {f.doi: f for f in feedback_list}
    
    # Check each compliance result
    for result in results:
        feedback = feedback_by_doi.get(result.doi)
        if not feedback or feedback.review_status == "skipped":
            continue
            
        total_reviewed += 1
        if feedback.review_status == "agreed":
            correct_assessments += 1
    
    if total_reviewed == 0:
        return None
        
    return (correct_assessments / total_reviewed) * 100

def get_stats_by_field(manuscripts: List[Any], field: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
    """Get statistics grouped by a specific field.
    
    Args:
        manuscripts: List of manuscripts
        field: Field to group by (e.g., 'discipline', 'design')
        filters: Optional dictionary of filter criteria
        
    Returns:
        Dict[str, int]: Count of manuscripts by field value
    """
    # Filter manuscripts if filters provided
    if filters:
        manuscripts = filter_manuscripts(manuscripts, filters)
        
    stats = {}
    for m in manuscripts:
        value = getattr(m, field, 'Unknown')
        if not value:
            value = 'Unknown'
        stats[value] = stats.get(value, 0) + 1
        
    return dict(sorted(stats.items()))
