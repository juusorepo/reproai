"""
ReproAI - Checklists Page
-------------------------

This page provides the interface for managing reproducibility checklists.

Author: ReproAI Team
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from app.services.db_service import DatabaseService
from pages.views.checklist_manage_view import manage_checklist_items
from pages.views.checklist_stats_view import (
    calculate_compliance_score, 
    format_compliance_status, 
    calculate_accuracy,
    get_unique_values,
    get_stats_by_field,
    filter_manuscripts
)
import os

# Load CSS
def load_css():
    """Load custom CSS styles."""
    css_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'styles.css')
    with open(css_file, 'r') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def display_filter_sidebar(manuscripts):
    """Display filter controls in the sidebar."""
    st.sidebar.markdown("## Filter Manuscripts")
    
    # Discipline filter
    disciplines = ["All"] + get_unique_values(manuscripts, 'discipline')
    selected_discipline = st.sidebar.selectbox("Discipline", disciplines)
    
    # Design filter
    designs = ["All"] + get_unique_values(manuscripts, 'design')
    selected_design = st.sidebar.selectbox("Study Design", designs)
    
    # Date range filter
    st.sidebar.markdown("### Processing Date Range")
    
    # Get min and max dates from manuscripts
    dates = [m.processed_at for m in manuscripts if m.processed_at]
    min_date = min(dates) if dates else datetime.now()
    max_date = max(dates) if dates else datetime.now()
    
    start_date = st.sidebar.date_input("From", min_date)
    end_date = st.sidebar.date_input("To", max_date)
    
    # Build filters dict
    filters = {}
    if selected_discipline != "All":
        filters['discipline'] = selected_discipline
    if selected_design != "All":
        filters['design'] = selected_design
    
    # Convert dates to datetime
    filters['processed_after'] = datetime.combine(start_date, datetime.min.time())
    filters['processed_before'] = datetime.combine(end_date, datetime.max.time())
    
    return filters

def display_stats_summary(manuscripts, filters):
    """Display summary statistics based on current filters."""
    st.sidebar.markdown("## Summary Statistics")
    
    # Filter manuscripts
    filtered_manuscripts = filter_manuscripts(manuscripts, filters)
    total_filtered = len(filtered_manuscripts)
    
    st.sidebar.metric("Total Manuscripts", total_filtered)

def display_checklist_items(db_service: DatabaseService):
    """Display the checklist view."""
    
    st.markdown("""
        <div class="card">
            <h4>Current Checklist</h4>
            <p><strong>Title:</strong> Nature Research Reporting Summary</p>
            <p><strong>Section:</strong> Behavioural & social sciences study design</p>
            <p><strong>Source:</strong> <a href="https://www.nature.com/documents/nr-reporting-summary.pdf" target="_blank">www.nature.com/documents/nr-reporting-summary.pdf</a></p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<h2 class="section-title">Checklist Statistics</h2>', unsafe_allow_html=True)
    
    st.markdown("""
        <div>
            Text from original source is shown in italics. The text is split to items and descriptions for stepwise analysis.
        </div>
    """, unsafe_allow_html=True)
    
    # Get checklist items and all manuscripts from database
    checklist_items = db_service.get_checklist_items()
    all_manuscripts = db_service.get_all_manuscripts()
    
    # Display filters in sidebar and get filter settings
    filters = display_filter_sidebar(all_manuscripts)
    
    # Display summary statistics
    display_stats_summary(all_manuscripts, filters)
    
    # Get all compliance results and feedback for statistics
    all_results = {}
    
    # Get all feedback in a single query
    all_feedback = db_service.get_all_feedback_by_item()
    
    # Filter manuscripts based on criteria
    filtered_manuscripts = filter_manuscripts(all_manuscripts, filters)
    
    # Get all compliance results for filtered manuscripts
    for manuscript in filtered_manuscripts:
        results = db_service.get_compliance_results(manuscript.doi)
        for result in results:
            if result.item_id not in all_results:
                all_results[result.item_id] = []
            all_results[result.item_id].append(result)
    
    if checklist_items:
        # First group by category while maintaining order
        items_by_category = {}
        category_order = []
        for item in checklist_items:
            category = item.get('category', 'Uncategorized')
            if category not in items_by_category:
                items_by_category[category] = []
                category_order.append(category)
            items_by_category[category].append(item)
        
        # Display items by category in database order
        for i, category in enumerate(dict.fromkeys(category_order), 1):
            items = items_by_category[category]
            st.subheader(f"{i}. {category}")
            
            # Group items by original text
            items_by_original = {}
            for item in items:
                original = item.get('original', '')
                if original not in items_by_original:
                    items_by_original[original] = []
                items_by_original[original].append(item)
            
            # Display grouped items
            for original, grouped_items in items_by_original.items():
                # Show original text first
                st.markdown(f"*{original}*")
                st.write("")  # Add some spacing
                
                # Create table data for items
                data = []
                for item in sorted(grouped_items, key=lambda x: x.get('item_id', '')):
                    item_id = item.get('item_id', '')
                    compliances = all_results.get(item_id, [])
                    total_results = len(compliances)
                    
                    if total_results > 0:
                        # Count compliance types
                        compliances_dict = {"Yes": 0, "No": 0, "Partial": 0, "n/a": 0}
                        for result in compliances:
                            compliances_dict[result.compliance] += 1
                            
                        # Calculate statistics
                        compliance_score = calculate_compliance_score([r.compliance for r in compliances])
                        accuracy = calculate_accuracy(compliances, all_feedback.get(item_id, []))
                        
                        # Format row data
                        row = {
                            "Item": item.get('question', ''),
                            "N": total_results,
                            "Yes": f"{int(compliances_dict['Yes']/total_results*100)}%",
                            "No": f"{int(compliances_dict['No']/total_results*100)}%",
                            "Partial": f"{int(compliances_dict['Partial']/total_results*100)}%",
                            "N/A": f"{int(compliances_dict['n/a']/total_results*100)}%",
                            "Compliance": f"{calculate_compliance_score([r.compliance for r in compliances])}%",
                            "AI Accuracy": f"{int(accuracy)}%" if accuracy is not None else "N/A"
                        }
                        data.append(row)
                
                if data:
                    df = pd.DataFrame(data)
                    
                    # Add custom table styling
                    st.markdown(
                        """
                        <style>
                        .custom-table {
                            width: 100%;
                            table-layout: fixed;
                        }
                        .custom-table td:first-child {
                            width: 40% !important;
                            white-space: normal;
                            text-align: left !important;
                            padding-right: 15px;
                        }
                        .custom-table td:not(:first-child) {
                            width: 10% !important;
                            text-align: center !important;
                            vertical-align: top;
                        }
                        .custom-table th {
                            text-align: center !important;
                            background-color: #f0f2f6;
                            padding: 8px !important;
                        }
                        .custom-table th:first-child {
                            text-align: left !important;
                            width: 40% !important;
                        }
                        .custom-table th:not(:first-child) {
                            width: 10% !important;
                        }
                        .score-high {
                            color: #2ecc71 !important;
                            font-weight: bold;
                        }
                        .score-medium {
                            color: #f39c12 !important;
                            font-weight: bold;
                        }
                        .score-low {
                            color: #e74c3c !important;
                            font-weight: bold;
                        }
                        .score-na {
                            color: #95a5a6 !important;
                            font-weight: bold;
                        }
                        </style>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    # Color the compliance scores
                    def color_score(val):
                        if val == "N/A":
                            return f'<span class="score-na">{val}</span>'
                        try:
                            score = float(val.rstrip('%'))
                            if score >= 80:
                                return f'<span class="score-high">{val}</span>'
                            elif score >= 50:
                                return f'<span class="score-medium">{val}</span>'
                            else:
                                return f'<span class="score-low">{val}</span>'
                        except ValueError:
                            return f'<span class="score-na">{val}</span>'

                    # Apply coloring only to Compliance and AI Accuracy columns
                    for col in ['Compliance', 'AI Accuracy']:
                        if col in df.columns:
                            df[col] = df[col].apply(color_score)
                    
                    # Convert DataFrame to HTML with the custom class
                    html = df.to_html(classes=['custom-table', 'dataframe'], index=False, escape=False)
                    st.markdown(html, unsafe_allow_html=True)
                
                st.write("---")  # Separator between groups

def main():
    """Main function to run the app."""
    st.set_page_config(
        page_title="ReproAI - Checklist Statistics",
        page_icon="✓",
        layout="wide"
    )
    
    load_css()
    
    # Initialize database service
    db_service = DatabaseService(st.secrets["MONGODB_URI"])
    
    st.title("✓ Checklists")
    st.markdown("""
View checklist overall stats and edit checklist items. 
""")

    # Create tabs for different views
    tab1, tab2 = st.tabs(["View Checklist", "Manage Items"])
    
    with tab1:
        display_checklist_items(db_service)
    
    with tab2:
        manage_checklist_items(db_service)

if __name__ == "__main__":
    main()
