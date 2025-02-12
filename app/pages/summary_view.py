"""
Summary View Page
---------------

This module provides the summary view page for displaying:
1. Overview of compliance analysis
2. Category-based issues table
3. Detailed results by category
"""

import streamlit as st
import pandas as pd

def summary_view_page():
    """Display the summary view page."""
    
    if not st.session_state.current_manuscript:
        st.warning("Please select a manuscript to view results")
        return
        
    manuscript = st.session_state.current_manuscript
    db_service = st.session_state.db_service
    
    # Get summary from database
    summary = db_service.get_summary(manuscript.doi)
    
    if not summary:
        st.warning("No summary found for this manuscript. Please process the manuscript first.")
        return
    
    # Display overview
    st.markdown(summary["overview"])
    
    # Display category summaries in a table
    st.markdown("### Summary by Category")
    
    # Get checklist items to map categories to original text
    checklist_items = db_service.get_checklist_items()
    category_originals = {}
    for item in checklist_items:
        category = item['category']
        if category not in category_originals:
            category_originals[category] = item.get('original', '')
    
    # Define severity indicators and order
    severity_colors = {
        'HIGH': '🔴',
        'MEDIUM': '🟡',
        'LOW': '🟢'
    }
    severity_order = {
        'HIGH': 0,
        'MEDIUM': 1,
        'LOW': 2
    }
    
    # Create DataFrame for categories
    data = []
    for cat in summary["category_summaries"]:
        severity = cat['severity'].upper()
        severity_indicator = severity_colors.get(severity, '')
        data.append({
            'Category': f"{severity_indicator} {cat['category']}",
            'Summary': cat['summary'],
            'SeverityOrder': severity_order.get(severity, 3)  # For sorting
        })
        
    df = pd.DataFrame(data)
    
    # Sort by severity
    df = df.sort_values('SeverityOrder').drop('SeverityOrder', axis=1)
    
    # Style the table and hide index
    styled_df = df.style.set_properties(**{
        'text-align': 'left',
        'white-space': 'normal',
        'font-size': '1em',
        'padding': '10px',
        'max-width': '400px',
        'overflow-wrap': 'break-word'
    })
    
    # Display the table with hidden index
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Show original results in expandable sections
    st.markdown("### Detailed Results by Items")
    st.markdown("Each category has been evaluated against several items shown below.")
    
    # Sort categories by severity for detailed results
    sorted_categories = sorted(
        summary["category_summaries"],
        key=lambda x: severity_order.get(x['severity'].upper(), 3)
    )
    
    for cat in sorted_categories:
        severity = cat['severity'].upper()
        severity_indicator = severity_colors.get(severity, '')
        
        with st.expander(f"{severity_indicator} {cat['category']} ({len(cat['original_results'])} items)"):
            if cat['original_results']:
                for result in cat['original_results']:
                    st.markdown(f"**Question:** {result['question']}")
                    st.markdown(f"**Compliance:** {result['compliance']}")
                    st.markdown(f"**Explanation:** {result['explanation']}")
                    if result.get('quote'):
                        st.markdown(f"**Quote:** {result['quote']}")
                    if result.get('section'):
                        st.markdown(f"**Section:** {result['section']}")
                    st.markdown("---")
            else:
                st.info("No issues found in this category.")
