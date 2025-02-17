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
    page_icon="🔍",
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
from datetime import datetime
import tempfile

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

def process_uploaded_file(uploaded_file):
    """Process uploaded PDF file."""
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        # Extract text from PDF
        pdf_extractor = PDFExtractor()
        text = pdf_extractor.extract_text(tmp_file_path)
        
        if not text:
            st.error("Could not extract text from the PDF. Please ensure the file is not corrupted or password protected.")
            return None

        # Extract metadata
        metadata = metadata_extractor.extract_metadata(text)
        if not metadata:
            st.error("Could not extract metadata from the manuscript.")
            return None

        # Create manuscript object
        manuscript = Manuscript(
            title=metadata.get('title', 'Unknown Title'),
            authors=metadata.get('authors', []),
            doi=metadata.get('doi', ''),
            abstract=metadata.get('abstract', ''),
            design=metadata.get('design', ''),
            discipline=metadata.get('discipline', ''),
            email=metadata.get('email', ''),
            text=text,
            processed_at=datetime.now()
        )

        # Save manuscript to database
        db_service.save_manuscript(manuscript)

        # Run compliance analysis
        checklist_items = db_service.get_checklist_items()
        try:
            with st.spinner("Analyzing manuscript compliance..."):
                results = compliance_analyzer.analyze_manuscript(
                    manuscript=manuscript,
                    text=text,
                    checklist_items=checklist_items
                )
                if not results:
                    st.error("Could not analyze manuscript compliance. No results were generated.")
                    return None
                
                if len(results) < len(checklist_items):
                    st.warning(f"⚠️ Analysis completed but only {len(results)} out of {len(checklist_items)} items were analyzed successfully. Some items may need to be reanalyzed.")

                # Save results to database
                for result in results:
                    db_service.save_compliance_result(doi=manuscript.doi, result=result)

        except Exception as e:
            st.error(f"Error during compliance analysis: {str(e)}")
            if hasattr(e, '__cause__') and e.__cause__:
                st.error(f"Caused by: {str(e.__cause__)}")
            return None

        # Generate and save summary
        overview, category_summaries = summarize_service.summarize_results(results)
        if overview and category_summaries:
            db_service.save_summary(
                doi=manuscript.doi,
                overview=overview,
                category_summaries=category_summaries
            )
        else:
            st.warning("Could not generate complete summary. Some information may be missing.")

        # Store current manuscript in session state
        st.session_state.current_manuscript = manuscript

        # Clean up temporary file
        os.unlink(tmp_file_path)

        return manuscript

    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return None

def main():
    """Main app function."""
    # Title
    st.title("🔍 ReproAI Analyzer")
    
    # Initialize session state for user email if not exists
    if 'user_email' not in st.session_state:
        st.markdown("### Sign in")
        st.markdown("Please enter your email address to continue:")
        email = st.text_input("Email address")
        
        if email:
            # Validate email
            if db_service._validate_email(email):
                # Save user to database
                db_service.save_user(email)
                st.session_state.user_email = email
                st.experimental_rerun()
            else:
                st.error("Please enter a valid email address.")
        return
    
    # Show current user
    st.sidebar.markdown(f"**User:** {st.session_state.user_email}")
    
    # Rest of the main function
    st.markdown("Upload a manuscript (PDF) for analysis (~5min) or view previous results.")
    
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if uploaded_file:
        # Check if this file has already been processed in this session
        file_key = f"processed_{uploaded_file.name}"
        if file_key not in st.session_state:
            with st.spinner('Processing manuscript...'):
                manuscript = process_uploaded_file(uploaded_file)
                if manuscript:
                    st.session_state[file_key] = True
                    st.success("Manuscript processed successfully! You can now view the results in the Results page.")
        else:
            st.info("This file has already been processed. You can view the results in the Results page.")

if __name__ == "__main__":
    main()
