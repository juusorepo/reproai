"""
ReproAI - Manuscript Reproducibility Analysis Tool
------------------------------------------------

This is the main Streamlit application file that provides the web interface for:
1. Uploading and processing scientific manuscripts
2. Viewing compliance analysis results
3. Providing feedback on the analysis

The app uses a tab-based interface with three main sections:
- Manuscript: For uploading and selecting manuscripts
- Results Summary: High-level overview of compliance
- Detailed Results: In-depth analysis with feedback options

Author: ReproAI Team
"""

import streamlit as st
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

# Initialize services
api_key = st.secrets["OPENAI_API_KEY"]
if not api_key:
    st.error("OpenAI API key not found in Streamlit secrets.")
    st.stop()

metadata_extractor = MetadataExtractor(api_key)
db_service = DatabaseService(st.secrets["MONGODB_URI"])
compliance_analyzer = ComplianceAnalyzer(api_key, db_service)
summarize_service = SummarizeService(api_key, db_service)

# Initialize session state variables if they don't exist
if 'current_manuscript' not in st.session_state:
    st.session_state.current_manuscript = None
if 'log_messages' not in st.session_state:
    st.session_state.log_messages = []
if 'db_service' not in st.session_state:
    st.session_state.db_service = db_service

def add_log(message: str):
    """Add a timestamped log message to session state."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.log_messages.append(f"[{timestamp}] {message}")

def display_logs():
    """Display all log messages."""
    if st.session_state.log_messages:
        for msg in st.session_state.log_messages:
            st.text(msg)

def get_error_details(e: Exception) -> str:
    """Get detailed error information."""
    error_details = []
    error_details.append(f"Error type: {type(e).__name__}")
    error_details.append(f"Error message: {str(e)}")
    
    # Get the full traceback
    import traceback
    tb = traceback.format_exc()
    error_details.append("\nTraceback:")
    error_details.append(tb)
    
    return "\n".join(error_details)

def display_manuscript_selector():
    """Display a list of analyzed manuscripts and allow selection.
    
    Returns:
        Manuscript: The selected manuscript or None if no selection made
    """
    # Get all manuscripts from database
    manuscripts = db_service.get_all_manuscripts()
    
    if not manuscripts:
        st.info("No manuscripts have been analyzed yet. Upload a new manuscript to start.")
        return None
    
    # Create manuscript selection
    st.markdown("### Select a manuscript to view results")
    
    # Create options for selectbox
    options = [(m.title, m) for m in manuscripts]
    titles = [title for title, _ in options]
    manuscript_map = {title: m for title, m in options}
    
    selected_title = st.selectbox(
        "Select manuscript",
        titles,
        label_visibility="collapsed"
    )
    if selected_title:
        selected_manuscript = manuscript_map[selected_title]
        st.session_state.current_manuscript = selected_manuscript
        return selected_manuscript
    
    return None

def process_uploaded_file(uploaded_file):
    """Process uploaded PDF file.
    
    This function:
    1. Saves the uploaded file temporarily
    2. Extracts text using PDFExtractor
    3. Extracts metadata using OpenAI
    4. Creates and saves a Manuscript object
    5. Runs compliance analysis
    
    Args:
        uploaded_file: The uploaded PDF file from Streamlit
    """
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
                        st.info(f"Analysis results already exist for DOI: {metadata['doi']}")
                        
                        # Create manuscript object
                        manuscript = Manuscript(
                            doi=metadata["doi"],
                            title=metadata["title"],
                            authors=metadata["authors"],
                            abstract=metadata.get("abstract", ""),
                            design=metadata.get("design", ""),
                            pdf_path=uploaded_file.name
                        )
                        
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
                            st.session_state.current_manuscript = manuscript
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
                        
                        # Run compliance analysis
                        add_log("Running compliance analysis...")
                        
                        # Get checklist items from database
                        add_log("Getting checklist items from database...")
                        checklist_items = db_service.get_checklist_items()
                        if not checklist_items:
                            add_log("Error: No checklist items found in database")
                            st.error("No checklist items found in database. Please add checklist items first.")
                            return
                        
                        add_log(f"Analyzing {len(checklist_items)} compliance items...")
                        results = compliance_analyzer.analyze_manuscript(manuscript, pdf_text, checklist_items)
                        add_log(f"Analysis complete. Found {len(results)} results.")
                        
                        # Convert results to ComplianceResult objects
                        add_log("Converting results to ComplianceResult objects...")
                        compliance_results = []
                        for result in results:
                            try:
                                compliance_results.append(ComplianceResult.from_dict(result))
                            except Exception as e:
                                add_log(f"Error converting result: {str(e)}")
                                continue
                        
                        # Run summarize service
                        add_log("Generating summary of compliance results...")
                        try:
                            summary = summarize_service.generate_summary(manuscript, compliance_results)
                            add_log("Summary generated successfully.")
                        except Exception as e:
                            add_log(f"Error generating summary: {str(e)}")
                            st.error("Error generating summary. Please check the logs.")
                            return
                        
                        # Store results in session state
                        st.session_state.current_manuscript = manuscript
                        st.session_state.compliance_results = compliance_results
                        st.session_state.compliance_summary = summary
                        
                        # Add success message
                        st.success("Manuscript processed successfully! Go to the Detailed Results tab to view results.")
                    
                finally:
                    # Clean up temporary file
                    os.unlink(tmp_path)
                
            except Exception as e:
                error_details = get_error_details(e)
                add_log(f"Error: {str(e)}")
                add_log("Full error details:")
                for line in error_details.split('\n'):
                    add_log(line)
                st.error(f"Error processing manuscript: {str(e)}")
    
    with col2:
        pass
    
    # Display processing status
    st.subheader("Processing Status")
    display_logs()

def display_compliance_results(manuscript: Manuscript):
    """Display compliance analysis results.
    
    Args:
        manuscript: The manuscript object
    """
    if not manuscript:
        st.warning("No manuscript selected")
        return
        
    # Get results from database
    results = db_service.get_compliance_results(manuscript.doi)
    if not results:
        st.warning("No compliance results found")
        return
        
    # Display results with feedback options
    for result in results:
        with st.expander(f"Item {result.item_id}: {result.question}"):
            # Display result
            st.write(f"**Compliance:** {result.compliance}")
            if result.explanation:
                st.write(f"**Explanation:** {result.explanation}")
            if result.quote:
                st.write(f"**Supporting Quote:** {result.quote}")
            if result.section:
                st.write(f"**Section:** {result.section}")
            
            # Get existing feedback
            feedback = db_service.get_feedback(manuscript.doi, result.item_id)
            
            # Feedback section
            st.divider()
            st.write("**Your Feedback**")
            
            # Feedback buttons in columns
            cols = st.columns(4)
            selected_rating = None
            
            for i, rating in enumerate(Feedback.VALID_RATINGS):
                with cols[i]:
                    button_type = "primary" if feedback and feedback.rating == rating else "secondary"
                    if st.button(
                        rating,
                        key=f"btn_{result.item_id}_{rating}",
                        type=button_type,
                        use_container_width=True
                    ):
                        selected_rating = rating
            
            # Comments field
            comments = st.text_area(
                "Feedback comments",
                value=feedback.comments if feedback else "",
                key=f"comments_{result.item_id}",
                placeholder="Add your comments here..."
            )
            
            # Save feedback if rating changed or comments updated
            if selected_rating or (
                feedback and (
                    selected_rating != feedback.rating or
                    comments != feedback.comments
                )
            ):
                new_feedback = Feedback(
                    doi=manuscript.doi,
                    item_id=result.item_id,
                    rating=selected_rating or feedback.rating,
                    comments=comments
                )
                if db_service.save_feedback(new_feedback):
                    st.success("Feedback saved!")
                else:
                    st.error("Error saving feedback")

def main():
    """Main app function."""
    st.title("ReproAI Analyzer")
    st.write("Analysing manuscripts against reproducibility standards")
    
    # Initialize session state
    if 'current_manuscript' not in st.session_state:
        st.session_state.current_manuscript = None
    if 'log_messages' not in st.session_state:
        st.session_state.log_messages = []
    
    # Create tabs for different views
    manuscript_tab, summary_tab, results_tab, checklist_tab = st.tabs([
        "📄 Manuscript", 
        "📊 Results",
        "🔍 Review",
        "📋 Checklist"
    ])
    
    with manuscript_tab:
        # Add manuscript selector above the upload section
        st.write("---")
        selected_manuscript = display_manuscript_selector()
        
        st.write("---")
        st.subheader("Upload New Manuscript")
        
        # File uploader
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
        
        if uploaded_file:
            if st.button("Process Manuscript"):
                # Clear previous log messages
                st.session_state.log_messages = []
                try:
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
                            st.info(f"Analysis results already exist for DOI: {metadata['doi']}")
                            
                            # Create manuscript object
                            manuscript = Manuscript(
                                doi=metadata["doi"],
                                title=metadata["title"],
                                authors=metadata["authors"],
                                abstract=metadata.get("abstract", ""),
                                design=metadata.get("design", ""),
                                pdf_path=uploaded_file.name
                            )
                            
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
                                st.session_state.current_manuscript = manuscript
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
                            
                            # Run compliance analysis
                            add_log("Running compliance analysis...")
                            
                            # Get checklist items from database
                            add_log("Getting checklist items from database...")
                            checklist_items = db_service.get_checklist_items()
                            if not checklist_items:
                                add_log("Error: No checklist items found in database")
                                st.error("No checklist items found in database. Please add checklist items first.")
                                return
                            
                            add_log(f"Analyzing {len(checklist_items)} compliance items...")
                            results = compliance_analyzer.analyze_manuscript(manuscript, pdf_text, checklist_items)
                            add_log(f"Analysis complete. Found {len(results)} results.")
                            
                            # Convert results to ComplianceResult objects
                            add_log("Converting results to ComplianceResult objects...")
                            compliance_results = []
                            for result in results:
                                try:
                                    compliance_results.append(ComplianceResult.from_dict(result))
                                except Exception as e:
                                    add_log(f"Error converting result: {str(e)}")
                                    continue
                            
                            # Run summarize service
                            add_log("Generating summary of compliance results...")
                            try:
                                summary = summarize_service.generate_summary(manuscript, compliance_results)
                                add_log("Summary generated successfully.")
                            except Exception as e:
                                add_log(f"Error generating summary: {str(e)}")
                                st.error("Error generating summary. Please check the logs.")
                                return
                            
                            # Store results in session state
                            st.session_state.current_manuscript = manuscript
                            st.session_state.compliance_results = compliance_results
                            st.session_state.compliance_summary = summary
                            
                            # Add success message
                            st.success("Manuscript processed successfully! Go to the Detailed Results tab to view results.")
                        
                    finally:
                        # Clean up temporary file
                        os.unlink(tmp_path)
                    
                except Exception as e:
                    error_details = get_error_details(e)
                    add_log(f"Error: {str(e)}")
                    add_log("Full error details:")
                    for line in error_details.split('\n'):
                        add_log(line)
                    st.error(f"Error processing manuscript: {str(e)}")
    
    with summary_tab:
        summary_view_page()

    with results_tab:
        if st.session_state.current_manuscript:
            compliance_analysis_page()
        else:
            st.warning("Please select a manuscript to view results")
            
    with checklist_tab:
        checklist_view_page(db_service)

if __name__ == "__main__":
    main()
