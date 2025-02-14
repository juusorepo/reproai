"""
ReproAI - Upload Page
--------------------

This page provides the interface for uploading and processing new manuscripts.

Author: ReproAI Team
"""

import streamlit as st
from app.services.db_service import DatabaseService
from app.services.pdf_extractor import PDFExtractor
from app.services.metadata_extractor import MetadataExtractor
from app.services.compliance_analyzer import ComplianceAnalyzer
from app.services.summarize_service import SummarizeService
from app.models.manuscript import Manuscript
import tempfile
import os
from datetime import datetime

# Load CSS
def load_css():
    """Load custom CSS styles."""
    css_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'styles.css')
    with open(css_file, 'r') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Initialize session state
if 'log_messages' not in st.session_state:
    st.session_state.log_messages = []

def add_log(message: str):
    """Add a timestamped log message to session state."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.log_messages.append(f"{timestamp} - {message}")

def display_logs():
    """Display all log messages."""
    for msg in st.session_state.log_messages:
        st.text(msg)

def process_uploaded_file(uploaded_file, db_service):
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
        metadata_extractor = MetadataExtractor(st.secrets["OPENAI_API_KEY"])
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
        compliance_analyzer = ComplianceAnalyzer(st.secrets["OPENAI_API_KEY"], db_service)
        results = compliance_analyzer.analyze_manuscript(text)
        
        # Save results
        add_log("Saving analysis results...")
        db_service.save_compliance_results(results, manuscript.doi)
        
        # Generate summary
        add_log("Generating summary...")
        summarize_service = SummarizeService(st.secrets["OPENAI_API_KEY"], db_service)
        overview, category_summaries = summarize_service.summarize_results(results)
        db_service.save_summary(manuscript.doi, overview, category_summaries)
        
        st.markdown("""
            <div class="status-success">
                ✅ Manuscript processed successfully!
            </div>
        """, unsafe_allow_html=True)
        
        st.session_state.current_manuscript = manuscript.to_dict()
        
        st.markdown('<div class="primary-button">', unsafe_allow_html=True)
        if st.button("View Results", use_container_width=True):
            st.switch_page("pages/results.py")
        st.markdown('</div>', unsafe_allow_html=True)
        
    except Exception as e:
        error_details = str(e)
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            error_details += f"\nResponse: {e.response.text}"
        st.markdown(f"""
            <div class="status-error">
                ❌ Error processing manuscript: {error_details}
            </div>
        """, unsafe_allow_html=True)
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
    # Load CSS
    load_css()
    
    # Sidebar Navigation
    st.sidebar.title("Navigation")
    st.sidebar.write("Use the navigation below to move between different sections of the analysis.")
    
    # Main content
    st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: baseline;">
            <h1 class="custom-title">Upload Manuscript</h1>
            <p class="custom-subtitle">Process New Scientific Papers</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<h2 style="font-size: 24px; margin-bottom: 1rem;">Upload New Manuscript</h2>', unsafe_allow_html=True)
        st.markdown("""
            Welcome to the manuscript upload page! Here you can:
            - Upload scientific manuscripts in PDF format
            - Process them for reproducibility analysis
            - View detailed results and compliance scores
            
            Get started by selecting a PDF file below.
        """)
        
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=['pdf'],
            help="Upload a scientific manuscript in PDF format",
            key="manuscript_uploader"
        )
        
        if uploaded_file:
            st.markdown(f"""
                <div class="uploadedFile">
                    <span class="status-success">✓</span> Selected file: {uploaded_file.name}
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown('<div class="primary-button">', unsafe_allow_html=True)
            if st.button("Process Manuscript", use_container_width=True):
                process_uploaded_file(uploaded_file, st.session_state.db_service)
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        if st.session_state.log_messages:
            st.markdown('<h3 style="font-size: 18px; margin-bottom: 1rem;">Processing Log</h3>', unsafe_allow_html=True)
            st.markdown('<div class="css-1r6slb0">', unsafe_allow_html=True)
            display_logs()
            st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    api_key = st.secrets["OPENAI_API_KEY"]
    if not api_key:
        st.error("OpenAI API key not found in Streamlit secrets.")
        st.stop()

    db_service = DatabaseService(st.secrets["MONGODB_URI"])
    st.session_state.db_service = db_service
    main()
