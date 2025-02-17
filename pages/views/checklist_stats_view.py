"""
ReproAI - Checklist Statistics View
---------------------------------

This module provides statistical analysis functions for checklist items.

Author: ReproAI Team
"""

def calculate_compliance_score(compliances: list) -> float:
    """Calculate compliance score from a list of compliance values."""
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

def calculate_accuracy(results, feedback_list) -> float:
    """Calculate accuracy of AI assessments based on user feedback.
    
    Args:
        results: List of compliance results
        feedback_list: List of feedback for the item
        
    Returns:
        float: Accuracy percentage or None if no reviewed items
    """
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
