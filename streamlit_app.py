import streamlit as st
import os
from dotenv import load_dotenv
from app.services.pdf_extractor import PDFExtractor
from app.services.metadata_extractor import MetadataExtractor
from app.services.db_service import DatabaseService
from app.services.compliance_analyzer import ComplianceAnalyzer
from app.models.manuscript import Manuscript
from app.models.compliance_result import ComplianceResult
from app.models.feedback import Feedback
from app.pages.compliance_analysis import compliance_analysis_page
import json
from datetime import datetime
import tempfile
import pandas as pd

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

def display_manuscript_selector():
    """Display a list of analyzed manuscripts and allow selection."""
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
    
    selected_title = st.selectbox("", titles)
    if selected_title:
        selected_manuscript = manuscript_map[selected_title]
        st.session_state.current_manuscript = selected_manuscript
        return selected_manuscript
    
    return None

def process_uploaded_file(uploaded_file):
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
                        
                        # Run compliance analysis
                        add_log("Running compliance analysis...")
                        results = compliance_analyzer.analyze_compliance(pdf_text, doi)
                        add_log(f"Analysis complete. Found {len(results)} results.")
                        
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

def display_compliance_results(manuscript: Manuscript):
    """Display compliance analysis results."""
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
                "Comments",
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
    manuscript_tab, summary_tab, results_tab = st.tabs([
        "📄 Manuscript", 
        "📊 Results Summary",
        "🔍 Detailed Results"
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
            process_uploaded_file(uploaded_file)
    
    with summary_tab:
        st.header("Results Summary")
        if st.session_state.current_manuscript:
            st.info("""
            This section will provide a high-level summary of the compliance analysis results including:
            - Overall compliance statistics
            - Key areas needing improvement
            - Design-specific recommendations based on the manuscript type
            
            The summary will help you quickly understand the main findings before diving into the detailed results.
            """)
        else:
            st.warning("Please select a manuscript to view results")
    
    with results_tab:
        if st.session_state.current_manuscript:
            compliance_analysis_page()
        else:
            st.warning("Please select a manuscript to view results")

if __name__ == "__main__":
    main()
