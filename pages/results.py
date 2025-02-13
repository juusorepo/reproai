"""
ReproAI - Results View
---------------------

This page provides a comprehensive view of manuscript analysis results including:
1. Manuscript selection and management
2. Results summary and compliance analysis
3. Detailed review and feedback options

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
from app.pages.compliance_analysis import compliance_analysis_page
from app.pages.summary_view import summary_view_page
from app.pages.checklist_view import checklist_view_page
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
if 'log_messages' not in st.session_state:
    st.session_state.log_messages = []
if 'db_service' not in st.session_state:
    st.session_state.db_service = db_service

def add_log(message: str):
    """Add a timestamped log message to session state."""
    if 'log_messages' not in st.session_state:
        st.session_state.log_messages = []
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.log_messages.append(f"{timestamp} - {message}")

def display_logs():
    """Display all log messages."""
    if st.session_state.log_messages:
        st.markdown("### Processing Log")
        for msg in st.session_state.log_messages:
            st.text(msg)

def get_error_details(e: Exception) -> str:
    """Get detailed error information."""
    error_type = type(e).__name__
    error_msg = str(e)
    if hasattr(e, 'response'):
        if hasattr(e.response, 'text'):
            error_msg += f"\nResponse: {e.response.text}"
    return f"{error_type}: {error_msg}"

def display_manuscript_selector():
    """Display a list of analyzed manuscripts and allow selection."""
    manuscripts = db_service.get_all_manuscripts()
    
    if not manuscripts:
        st.info("No manuscripts analyzed yet. Upload a manuscript to get started!")
        return None
    
    # Format options for selectbox
    manuscript_options = []
    for m in manuscripts:
        title = m.title if hasattr(m, 'title') else 'Untitled'
        doi = m.doi if hasattr(m, 'doi') else 'No DOI'
        manuscript_options.append(f"{title} ({doi})")
    
    # Display selector
    selected_idx = st.selectbox(
        "Select a manuscript to view results:",
        range(len(manuscript_options)),
        format_func=lambda x: manuscript_options[x]
    )
    
    if selected_idx is not None:
        st.session_state.current_manuscript = manuscripts[selected_idx]
        return manuscripts[selected_idx]
    return None

def process_uploaded_file(uploaded_file):
    """Process uploaded PDF file."""
    if not uploaded_file:
        return
    
    try:
        # Save uploaded file to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            pdf_path = tmp_file.name
        
        # Extract text from PDF
        add_log("Extracting text from PDF...")
        pdf_extractor = PDFExtractor()
        text = pdf_extractor.extract_text(pdf_path)
        
        if not text.strip():
            st.error("Could not extract text from PDF. Please ensure the file is not scanned/image-based.")
            return
        
        # Extract metadata
        add_log("Extracting metadata...")
        metadata = metadata_extractor.extract_metadata(text)
        
        # Create manuscript object
        manuscript = Manuscript(
            doi=metadata.get('doi', 'No DOI'),
            title=metadata.get('title', 'Untitled'),
            authors=metadata.get('authors', []),
            design=metadata.get('design', ''),
            text=text
        )
        
        # Save manuscript
        add_log("Saving manuscript...")
        db_service.save_manuscript(manuscript)
        
        # Analyze compliance
        add_log("Analyzing reproducibility compliance...")
        results = compliance_analyzer.analyze_manuscript(text)
        
        # Save results
        add_log("Saving analysis results...")
        db_service.save_compliance_results(results, manuscript.doi)
        
        # Generate summary
        add_log("Generating summary...")
        overview, category_summaries = summarize_service.summarize_results(results)
        db_service.save_summary(manuscript.doi, overview, category_summaries)
        
        st.success("✅ Manuscript processed successfully!")
        st.session_state.current_manuscript = manuscript.to_dict()
        
    except Exception as e:
        error_details = get_error_details(e)
        st.error(f"Error processing manuscript: {error_details}")
        add_log(f"ERROR: {error_details}")
    
    finally:
        # Clean up temp file
        if 'pdf_path' in locals():
            try:
                os.remove(pdf_path)
            except:
                pass

def main():
    """Main app function."""
    st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: baseline;">
            <h1 class="custom-title">Analysis Results</h1>
            <p class="custom-subtitle">View and Review Manuscript Analysis</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs([
        "Manuscript",
        "Results",
        "Review"
    ])
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown('<h2 class="section-title">Previous Manuscripts</h2>', unsafe_allow_html=True)
            selected_manuscript = display_manuscript_selector()
        
        with col2:
            st.markdown('<h3 class="section-subtitle">Upload New</h3>', unsafe_allow_html=True)
            st.markdown('<div class="secondary-button">', unsafe_allow_html=True)
            if st.button("Upload Manuscript", use_container_width=True):
                st.switch_page("streamlit_app.py")
            st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        if st.session_state.current_manuscript:
            st.markdown('<h2 class="section-title">Analysis Results</h2>', unsafe_allow_html=True)
            summary_view_page()
        else:
            st.markdown("""
                <div class="ai-insight">
                    Select a manuscript to view results
                </div>
            """, unsafe_allow_html=True)
    
    with tab3:
        if st.session_state.current_manuscript:
            st.markdown('<h2 class="section-title">Detailed Review</h2>', unsafe_allow_html=True)
            compliance_analysis_page()
            checklist_view_page(db_service)
        else:
            st.markdown("""
                <div class="ai-insight">
                    Select a manuscript to view detailed analysis
                </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
