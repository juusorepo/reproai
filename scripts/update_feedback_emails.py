"""
Update Feedback Emails Script
---------------------------

This script updates all feedback entries in the database that don't have an email
to use the specified default email.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

import streamlit as st
from app.services.db_service import DatabaseService

def update_feedback_emails(db_service: DatabaseService, default_email: str) -> None:
    """
    Update all feedback entries without email to use the default email.
    
    Args:
        db_service: Database service instance
        default_email: Email to set for entries without email
    """
    # Validate email first
    if not db_service._validate_email(default_email):
        raise ValueError(f"Invalid email format: {default_email}")
    
    # Ensure user exists
    db_service.save_user(default_email)
    
    # Update all feedback entries where user_email is null or doesn't exist
    result = db_service.feedback.update_many(
        {"user_email": {"$exists": False}},
        {"$set": {"user_email": default_email}}
    )
    
    print(f"Updated {result.modified_count} feedback entries with email: {default_email}")

if __name__ == "__main__":
    # Get MongoDB URI from Streamlit secrets
    db_service = DatabaseService(st.secrets["MONGODB_URI"])
    
    # Update with specified email
    default_email = "juuso.repo@utu.fi"
    
    try:
        update_feedback_emails(db_service, default_email)
        print("Successfully updated feedback emails")
    except Exception as e:
        print(f"Error updating feedback emails: {str(e)}")
