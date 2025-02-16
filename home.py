"""
ReproAI - Manuscript Reproducibility Analysis Tool
------------------------------------------------

This is the main Streamlit application file that provides the web interface for:
1. Uploading and processing scientific manuscripts
2. Viewing compliance analysis results
3. Providing feedback on the analysis

Author: ReproAI Team
"""

import streamlit as st

# Page configuration - Must be the first Streamlit command
st.set_page_config(
    page_title="ReproAI Analyzer",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

import os
from app.services.pdf_extractor import PDFExtractor
from app.services.metadata_extractor import MetadataExtractor
from app.services.db_service import DatabaseService
from app.services.compliance_analyzer import ComplianceAnalyzer
from app.services.summarize_service import SummarizeService
from app.models.manuscript import Manuscript
from app.models.compliance_result import ComplianceResult
from app.models.feedback import Feedback
import json
from datetime import datetime
import tempfile
import pandas as pd

# Load custom CSS
with open('static/styles.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Initialize services
api_key = st.secrets["OPENAI_API_KEY"]
if not api_key:
    st.error("OpenAI API key not found in secrets!")
    st.stop()

db_service = DatabaseService(st.secrets["MONGODB_URI"])
metadata_extractor = MetadataExtractor(api_key)
compliance_analyzer = ComplianceAnalyzer(api_key, db_service)
summarize_service = SummarizeService(api_key, db_service)

# Initialize session state
if 'current_manuscript' not in st.session_state:
    st.session_state.current_manuscript = None
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'db_service' not in st.session_state:
    st.session_state.db_service = db_service

def add_log(message: str):
    """Add a timestamped log message to session state and display it."""
    if 'logs' not in st.session_state:
        st.session_state.logs = []
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    st.session_state.logs.append(log_message)
    
    # Update the log display
    if 'log_placeholder' in st.session_state:
        with st.session_state.log_placeholder:
            st.empty()  # Clear previous content
            for log in st.session_state.logs:
                st.markdown(f"```\n{log}\n```")

def display_logs():
    """Display all log messages."""
    if 'logs' in st.session_state and st.session_state.logs:
        for log in st.session_state.logs:
            st.markdown(f"```\n{log}\n```")

def get_error_details(e: Exception) -> str:
    """Get detailed error information."""
    error_type = type(e).__name__
    error_msg = str(e)
    if hasattr(e, 'response'):
        if hasattr(e.response, 'text'):
            error_msg += f"\nResponse: {e.response.text}"
    return f"{error_type}: {error_msg}"

def process_uploaded_file(uploaded_file):
    """Process uploaded PDF file."""
    try:
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            pdf_path = tmp_file.name

        add_log("Starting manuscript processing...")
        
        # Extract text from PDF
        pdf_extractor = PDFExtractor()
        text_content = pdf_extractor.extract_text(pdf_path)
        if not text_content:
            st.error("Could not extract text from PDF. Please ensure the file is not corrupted or password-protected.")
            return
        add_log("Text extracted from PDF")
        
        # Extract metadata
        metadata = metadata_extractor.extract_metadata(text_content)
        if not metadata:
            st.error("Could not extract metadata from manuscript. Please ensure the file contains standard manuscript sections.")
            return
        add_log("Metadata extracted")
        
        # Check if analysis exists for this DOI
        doi = metadata.get('doi', '')
        if doi:
            existing_results = db_service.get_compliance_results(doi)
            existing_summary = db_service.get_summary(doi)
            
            if existing_results and existing_summary:
                st.info(f"An existing analysis was found for DOI: {doi}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("View Previous Results", use_container_width=True):
                        st.session_state.current_doi = doi
                        st.switch_page("pages/results.py")
                        return
                with col2:
                    reanalyze = st.button("Re-analyze Manuscript", use_container_width=True)
                    if not reanalyze:
                        return
                    add_log("Starting re-analysis...")
        
        # Create manuscript object
        manuscript = Manuscript(
            doi=metadata.get('doi', ''),
            title=metadata.get('title', ''),
            authors=metadata.get('authors', []),
            abstract=metadata.get('abstract', ''),
            design=metadata.get('design', ''),
            email=metadata.get('email', ''),
            text=text_content
        )
        
        # Save manuscript to database
        db_service.save_manuscript(manuscript)
        add_log("Manuscript saved to database")
        
        # Analyze compliance
        checklist_items = db_service.get_checklist_items()
        results = compliance_analyzer.analyze_manuscript(manuscript, manuscript.text, checklist_items)
        if not results:
            st.error("Could not analyze manuscript compliance. Please try again later.")
            return
        add_log(f"Compliance analysis complete: {len(results)} items checked")
        
        # Save results to database
        db_service.save_compliance_results(results, manuscript.doi)
        add_log("Compliance results saved to database")
        
        # Generate and save summary
        overview, category_summaries = summarize_service.summarize_results(results)
        if overview and category_summaries:
            db_service.save_summary(manuscript.doi, overview, category_summaries)
            add_log("Summary generated and saved")
        else:
            add_log("Warning: Could not generate summary")
            
        # Store DOI in session state for other pages
        st.session_state.current_doi = manuscript.doi
        
        # Success message and redirect
        st.success("Analysis complete! View the results in the Results tab.")
        st.switch_page("pages/results.py")
        
    except Exception as e:
        error_details = get_error_details(e)
        st.error(f"Error processing manuscript: {error_details}")
        add_log(f"ERROR: {error_details}")
        # Print full stack trace for debugging
        import traceback
        print("Full error:", traceback.format_exc())
    
    finally:
        # Clean up temp file
        if 'pdf_path' in locals():
            try:
                os.remove(pdf_path)
            except:
                pass

def main():
    """Main app function."""
    st.title("ReproAI Analyzer")
    st.markdown("Enhancing reproducibility with AI-assisted analysis.")
    
    # Initialize session state for user email if not exists
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    
    # Email input section
    if not st.session_state.user_email:
        st.markdown("### Sign in")
        st.markdown("Please enter your email address to continue:")
        email = st.text_input("Email address")
        
        if st.button("Continue"):
            try:
                if email:
                    # Validate and save user
                    db_service.save_user(email)
                    st.session_state.user_email = email
                    st.success("Email verified successfully!")
                    st.experimental_rerun()
                else:
                    st.error("Please enter your email address")
            except ValueError as e:
                st.error(str(e))
        return
    
    # Show current user
    st.sidebar.markdown(f"**User:** {st.session_state.user_email}")
    
    # Rest of the main function
    st.markdown("Upload a manuscript (PDF) for analysis or view previous results.")
    
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if uploaded_file:
        process_uploaded_file(uploaded_file)

if __name__ == "__main__":
    main()
