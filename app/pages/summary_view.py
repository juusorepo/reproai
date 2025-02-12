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
import plotly.graph_objects as go

def format_compliance_status(status: str):
    """Format compliance status with color."""
    colors = {
        "Yes": "#2ecc71",
        "No": "#e74c3c",
        "Partial": "#f1c40f",
        "n/a": "#95a5a6"
    }
    return f"<span style='color: {colors[status]}'>{status}</span>"

def create_summary_chart(results: list) -> go.Figure:
    """Create summary chart of compliance results."""
    # Count compliance statuses
    status_counts = {"Yes": 0, "No": 0, "Partial": 0, "n/a": 0}  
    for result in results:
        status_counts[result.compliance] += 1
            
    # Create horizontal bar chart
    fig = go.Figure()
    
    # Add bars for each status
    colors = {"Yes": "#2ecc71", "No": "#e74c3c", "Partial": "#f1c40f", "n/a": "#95a5a6"}  
    for status, count in status_counts.items():
        if count > 0:  
            fig.add_trace(go.Bar(
                name=status,
                y=[1],
                x=[count],
                orientation='h',
                marker=dict(color=colors[status]),
                text=[f"{status}: {count}"],
                hoverinfo='text',
                hovertemplate='%{text}'
            ))
    
    # Update layout
    fig.update_layout(
        height=100,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        barmode='stack',
        xaxis=dict(showticklabels=False, showgrid=False),
        yaxis=dict(showticklabels=False, showgrid=False)
    )
    
    return fig

def summary_view_page():
    """Display the summary view page."""
    
    st.markdown("<h2 style='font-size: 24px;'>View Results</h2>", unsafe_allow_html=True)
    
    if not st.session_state.current_manuscript:
        st.warning("Please select a manuscript to view results")
        return
        
    manuscript = st.session_state.current_manuscript
    db_service = st.session_state.db_service
    
    # Get summary and results from database
    summary = db_service.get_summary(manuscript.doi)
    results = db_service.get_compliance_results(manuscript.doi)
    
    if not summary:
        st.warning("No summary found for this manuscript. Please process the manuscript first.")
        return
    
    # Display manuscript info
    st.markdown(f"<h3 style='font-size: 18px;'>{manuscript.title}</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size: 14px;'><b>DOI:</b> {manuscript.doi}</p>", unsafe_allow_html=True)
    
    # Calculate and display compliance score
    if results:
        scores = {
            "Yes": 1.0,
            "No": 0.0,
            "Partial": 0.5,
            "n/a": None  
        }
        valid_scores = [scores[r.compliance] for r in results if scores[r.compliance] is not None]
        compliance_score = int(round(sum(valid_scores) / len(valid_scores) * 100)) if valid_scores else 0
        
        # Create columns for score display
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            # Show summary chart
            st.plotly_chart(create_summary_chart(results), use_container_width=True)
            
        with col2:
            # Show compliance score with large number
            st.markdown(f"""
            <div style='text-align: center; padding: 10px; background-color: #f0f2f6; border-radius: 10px;'>
                <div style='font-size: 14px; color: #666;'>Compliance Score</div>
                <div style='font-size: 36px; font-weight: bold; color: #1f77b4;'>{compliance_score}%</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.write("---")
    
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
        'LOW': '🟢',
        'NONE': '⚫'  # For categories with all n/a
    }
    severity_order = {
        'HIGH': 0,
        'MEDIUM': 1,
        'LOW': 2,
        'NONE': 3
    }
    
    # Create DataFrame for categories
    data = []
    for cat in summary["category_summaries"]:
        # Get all compliance values for this category
        compliances = [r['compliance'] for r in cat['original_results']]
        
        # Determine severity based on compliance values
        if all(c == 'n/a' for c in compliances):
            severity = 'NONE'
        elif all(c in ['Yes', 'n/a'] for c in compliances) and any(c == 'Yes' for c in compliances):
            severity = 'LOW'  
        elif all(c in ['No', 'n/a'] for c in compliances) and any(c == 'No' for c in compliances):
            severity = 'HIGH'  
        else:
            severity = 'MEDIUM'  
            
        severity_indicator = severity_colors.get(severity, '')
        data.append({
            'Category': f"{severity_indicator} {cat['category']}",
            'Summary': cat['summary'],
            'SeverityOrder': severity_order.get(severity, 4)  
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
        key=lambda x: severity_order.get(x['severity'].upper(), 4)
    )
    
    for cat in sorted_categories:
        # Get all compliance values for this category
        compliances = [r['compliance'] for r in cat['original_results']]
        
        # Determine severity based on compliance values - same logic as above
        if all(c == 'n/a' for c in compliances):
            severity = 'NONE'
        elif all(c in ['Yes', 'n/a'] for c in compliances) and any(c == 'Yes' for c in compliances):
            severity = 'LOW'  # All Yes or n/a, with at least one Yes
        elif all(c in ['No', 'n/a'] for c in compliances) and any(c == 'No' for c in compliances):
            severity = 'HIGH'  # All No or n/a, with at least one No
        else:
            severity = 'MEDIUM'  # Mixed results
            
        severity_indicator = severity_colors.get(severity, '')
        
        with st.expander(f"{severity_indicator} {cat['category']} ({len(cat['original_results'])} items)"):
            if cat['original_results']:
                for result in cat['original_results']:
                    st.markdown(f"**Item:** {result['question']}")
                    st.markdown(f"**Compliance:** {format_compliance_status(result['compliance'])}", unsafe_allow_html=True)
                    st.markdown(f"**Explanation:** {result['explanation']}")
                    if result.get('quote'):
                        st.markdown(f"**Quote:** {result['quote']}")
                    if result.get('section'):
                        st.markdown(f"**Section:** {result['section']}")
                    st.markdown("---")
            else:
                st.info("No issues found in this category.")
