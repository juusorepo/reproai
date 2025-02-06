import streamlit as st
import os
from dotenv import load_dotenv
from app.services.pdf_extractor import PDFExtractor
from app.services.metadata_extractor import MetadataExtractor
from app.services.db_service import DatabaseService
from app.services.compliance_analyzer import ComplianceAnalyzer
from app.models.manuscript import Manuscript
from app.pages.compliance_analysis import compliance_analysis_page
import json
from datetime import datetime
import tempfile

# Load environment variables
load_dotenv()

# Initialize services
metadata_extractor = MetadataExtractor(os.getenv("OPENAI_API_KEY"))
db_service = DatabaseService(os.getenv("MONGODB_URI"))
compliance_analyzer = ComplianceAnalyzer(os.getenv("OPENAI_API_KEY"), db_service)

# Initialize session state
if 'log_messages' not in st.session_state:
    st.session_state.log_messages = []
if 'current_manuscript' not in st.session_state:
    st.session_state.current_manuscript = None
if 'db_service' not in st.session_state:
    st.session_state.db_service = db_service

def add_log(message: str):
    """Add a timestamped message to the log"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.log_messages.append(f"[{timestamp}] {message}")

# App title and description
st.title("ReproAI Analyzer")
st.write("Analysing manuscripts against reproducibility standards")

# Create tabs
tab1, tab2 = st.tabs(["Manuscript", "Detailed Results"])

with tab1:
    # File uploader
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file:
        # Create columns for better layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Manuscript Details")
            
            # Process button
            if st.button("Process Manuscript"):
                try:
                    # Clear previous log messages
                    st.session_state.log_messages = []
                    
                    # Save uploaded file to temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name
                    
                    try:
                        # Extract text from PDF
                        add_log("Extracting text from PDF...")
                        pdf_text = PDFExtractor.extract_text(tmp_path)
                        add_log(f"Extracted {len(pdf_text)} characters")
                        
                        # Extract metadata
                        add_log("Analyzing manuscript with LLM...")
                        metadata = metadata_extractor.extract_metadata(pdf_text)
                        
                        # Check if results already exist
                        existing_results = db_service.get_compliance_results(metadata["doi"])
                        if existing_results:
                            st.info(f"Analysis results already exist for DOI: {metadata['doi']}. View them in the Detailed Results tab.")
                            
                            # Create manuscript object and store in session
                            manuscript = Manuscript(
                                doi=metadata["doi"],
                                title=metadata["title"],
                                authors=metadata["authors"],
                                abstract=metadata.get("abstract", ""),
                                design=metadata.get("design", ""),
                                pdf_path=uploaded_file.name
                            )
                            st.session_state.current_manuscript = manuscript
                            
                            # Display metadata
                            st.json(metadata)
                            
                            # Add info about existing results
                            st.markdown("---")
                            st.markdown("### Existing Analysis Results")
                            st.write(f"Found {len(existing_results)} compliance results.")
                            
                            # Show reanalysis option
                            if st.button("Run Analysis Again"):
                                add_log("Starting new analysis...")
                                run_analysis = True
                            else:
                                run_analysis = False
                        else:
                            run_analysis = True
                        
                        if run_analysis:
                            # Create manuscript object
                            manuscript = Manuscript(
                                doi=metadata["doi"],
                                title=metadata["title"],
                                authors=metadata["authors"],
                                abstract=metadata.get("abstract", ""),
                                design=metadata.get("design", ""),
                                pdf_path=uploaded_file.name
                            )
                            
                            # Save to database
                            add_log("Saving to database...")
                            doi = db_service.save_manuscript(manuscript)
                            add_log(f"Successfully saved with DOI: {doi}")
                            
                            # Store manuscript in session state
                            st.session_state.current_manuscript = manuscript
                            
                            # Display results
                            st.json(metadata)
                            
                            # Add success message
                            st.success("Manuscript processed successfully! Go to the Detailed Results tab to view results.")
                        
                    finally:
                        # Clean up temporary file
                        os.unlink(tmp_path)
                    
                except Exception as e:
                    add_log(f"Error: {str(e)}")
                    st.error(f"Error processing manuscript: {str(e)}")
        
        with col2:
            # Log section
            with st.expander("Processing Log", expanded=True):
                # Display log messages
                for msg in st.session_state.log_messages:
                    st.text(msg)

with tab2:
    # Run compliance analysis page
    compliance_analysis_page()
