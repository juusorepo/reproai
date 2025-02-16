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
    page_title="Analysis results",
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
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "Select manuscript"

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
    st.markdown('<h2 class="section-title"> Current manuscript </h2>', unsafe_allow_html=True)
    
    # Get list of analyzed manuscripts
    manuscripts = db_service.get_all_manuscripts()
    
    if not manuscripts:
        st.info("No analyzed manuscripts found. Please upload a manuscript first.")
        return None

    # Sort manuscripts by analysis date
    manuscripts = sorted(manuscripts, key=lambda m: m.analysis_date if hasattr(m, 'analysis_date') else datetime.min, reverse=True)
    
    # Auto-select latest manuscript if none selected
    if st.session_state.current_manuscript is None:
        st.session_state.current_manuscript = manuscripts[0]
    
    # Display current selection at the top
    if st.session_state.current_manuscript:
        st.success(f"📖: {st.session_state.current_manuscript.title}")
       
    
    # Initialize index based on current selection
    current_index = 0
    if st.session_state.current_manuscript:
        try:
            current_index = manuscripts.index(st.session_state.current_manuscript)
        except ValueError:
            current_index = 0
    
    st.write("---")
    st.markdown(f'<h2 class="section-title"> Select manuscript ({len(manuscripts)} analyzed) </h2>', unsafe_allow_html=True)
    
    # Filtering options in an expander
    with st.expander("🔍 Filter manuscripts", expanded=False):
        # Get unique designs for filter
        designs = sorted(set(m.design for m in manuscripts if hasattr(m, 'design') and m.design))
        selected_design = st.selectbox(
            "Study design:",
            ["All"] + designs,
            index=0
        )
        
        # Filter manuscripts by design
        if selected_design != "All":
            manuscripts = [m for m in manuscripts if hasattr(m, 'design') and m.design == selected_design]
        
        # Search by title or DOI
        search_term = st.text_input("🔎 Search by title or DOI:", "")
        if search_term:
            search_term = search_term.lower()
            manuscripts = [m for m in manuscripts if 
                         search_term in m.title.lower() or 
                         (hasattr(m, 'doi') and search_term in m.doi.lower())]
    
    # Create a selection box with a clear format
    manuscript_options = [f"{m.title} ({m.doi})" for m in manuscripts]
    
    def on_select():
        if "manuscript_selector" in st.session_state:
            idx = st.session_state.manuscript_selector
            st.session_state.current_manuscript = manuscripts[idx]
    
    selected_index = st.selectbox(
        "Select to view results:",
        range(len(manuscripts)),
        index=current_index,
        format_func=lambda i: manuscript_options[i],
        key="manuscript_selector",
        on_change=on_select,
        help="Choose a manuscript to view its analysis results"
    )
    
    if st.session_state.current_manuscript:
        
        return st.session_state.current_manuscript
    
    return None

def main():
    """Main function for the results page."""
    # Initialize session state for user email if not exists
    if 'user_email' not in st.session_state:
        st.error("Please enter your email on the home page first.")
        st.stop()
        
    # Initialize database service if not exists
    if 'db_service' not in st.session_state:
        st.session_state.db_service = DatabaseService(st.secrets["MONGODB_URI"])
    
    st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: baseline;">
            <h1>Analysis Results</h1>
        </div>
    """, unsafe_allow_html=True)
    
    # Initialize active tab in session state if not present
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "Select manuscript"
    
    # Create tabs for different views
    tabs = ["Select manuscript", "View Results"]
    tab1, tab2 = st.tabs(tabs)
    
    # Set active tab if changed
    active_tab_index = tabs.index(st.session_state.active_tab)
    
    with tab1:
        display_manuscript_selector()
    
    with tab2:
        if st.session_state.current_manuscript:
            st.markdown('<h2 class="section-title">Analysis Results</h2>', unsafe_allow_html=True)
            compliance_analysis_page()
        else:
            st.markdown("""
                <div class="ai-insight">
                    Please select a manuscript first to view analysis results.
                </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
