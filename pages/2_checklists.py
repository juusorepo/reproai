"""
ReproAI - Checklists Page
-------------------------

This page provides the interface for managing reproducibility checklists.

Author: ReproAI Team
"""

import streamlit as st
import pandas as pd
from app.services.db_service import DatabaseService
from pages.views.checklist_manage_view import manage_checklist_items
from pages.views.checklist_stats_view import calculate_compliance_score, format_compliance_status, calculate_accuracy
import os

# Load CSS
def load_css():
    """Load custom CSS styles."""
    css_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'styles.css')
    with open(css_file, 'r') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def display_checklist_items(db_service: DatabaseService):
    """Display the checklist view."""
    st.markdown('<h2 class="section-title">Current checklist</h2>', unsafe_allow_html=True)
    
    st.markdown("""
        <div class="card">
            <p><strong>Title:</strong> Nature Research Reporting Summary</p>
            <p><strong>Section:</strong> Behavioural & social sciences study design</p>
            <p><strong>Source:</strong> <a href="https://www.nature.com/documents/nr-reporting-summary.pdf" target="_blank">www.nature.com/documents/nr-reporting-summary.pdf</a></p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class="ai-insight">
            Text from original source is shown in italics. The text is split to items for stepwise analysis.
        </div>
    """, unsafe_allow_html=True)
    
    # Get checklist items and all compliance results from database
    checklist_items = db_service.get_checklist_items()
    all_manuscripts = db_service.get_all_manuscripts()
    
    # Get all compliance results and feedback for statistics
    all_results = {}
    
    # Get all feedback in a single query
    all_feedback = db_service.get_all_feedback_by_item()
    
    # Get all compliance results
    for manuscript in all_manuscripts:
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
                        
                        # Calculate percentages
                        yes_count = compliances_dict["Yes"]
                        no_count = compliances_dict["No"]
                        partial_count = compliances_dict["Partial"]
                        na_count = compliances_dict["n/a"]
                        
                        # Calculate accuracy
                        feedback_list = all_feedback.get(item_id, [])
                        accuracy = calculate_accuracy(compliances, feedback_list)
                        
                        # Create table data
                        data.append({
                            "Item": item.get('question', ''),
                            "Yes": f"{int(yes_count/total_results*100)}%",
                            "No": f"{int(no_count/total_results*100)}%",
                            "Partial": f"{int(partial_count/total_results*100)}%",
                            "N/A": f"{int(na_count/total_results*100)}%",
                            "Compliance": f"{calculate_compliance_score([r.compliance for r in compliances])}%",
                            "Accuracy": f"{int(accuracy)}%" if accuracy is not None else "N/A"
                        })
                
                if data:
                    df = pd.DataFrame(data)
                    
                    # Add CSS classes for index hiding and table styling
                    st.markdown('<div class="hide-index data-table">', unsafe_allow_html=True)
                    
                    # Style the table
                    styled_df = df.style.set_table_styles([
                        {'selector': '.col0', 'props': [('width', '50%')]},  # Item column
                        {'selector': '.col1, .col2, .col3, .col4, .col5, .col6', 'props': [('width', '8.33%')]}  # Other columns
                    ])
                    
                    # Color compliance scores and accuracy
                    def color_score(val):
                        if val == "N/A":
                            return 'color: #95a5a6; font-weight: bold'  # Gray
                        try:
                            score = float(val.rstrip('%'))
                            if score >= 80:
                                return 'color: #2ecc71; font-weight: bold'  # Green
                            elif score >= 50:
                                return 'color: #f39c12; font-weight: bold'  # Orange
                            else:
                                return 'color: #e74c3c; font-weight: bold'  # Red
                        except ValueError:
                            return 'color: #95a5a6; font-weight: bold'  # Gray for non-numeric
                    
                    styled_df = styled_df.map(color_score, subset=['Compliance', 'Accuracy'])
                    
                    st.table(styled_df)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                st.write("---")  # Separator between groups
    else:
        st.warning("No checklist items found in database")

def main():
    """Main function to run the app."""
    st.set_page_config(
        page_title="ReproAI - Checklists",
        page_icon="📋",
        layout="wide"
    )
    
    load_css()
    
    # Initialize database service with MongoDB URI from secrets
    db_service = DatabaseService(st.secrets["MONGODB_URI"])
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["View Checklists", "Manage Checklists"])
    
    with tab1:
        display_checklist_items(db_service)
    
    with tab2:
        manage_checklist_items(db_service)

if __name__ == "__main__":
    main()
