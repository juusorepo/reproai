"""
Compliance Analysis Page
---------------

This module provides the detailed compliance analysis page for:
1. Reviewing individual compliance items
2. Providing feedback on AI analysis
3. Tracking review progress
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional
import plotly.graph_objects as go
import plotly.express as px
from app.models.manuscript import Manuscript
from app.models.feedback import Feedback

# Define severity indicators and order (global variables)
severity_colors = {
    'HIGH': '🔴',
    'MEDIUM': '🟡',
    'LOW': '🟢',
    'UNKNOWN': '⚪️'
}
severity_order = {
    'HIGH': 0,
    'MEDIUM': 1,
    'LOW': 2,
    'UNKNOWN': 3
}

def create_summary_chart(results: List[Dict[str, Any]]) -> go.Figure:
    """Create summary chart of compliance results."""
    # Count statuses
    status_counts = {"Yes": 0, "No": 0, "Partial": 0, "n/a": 0}
    for result in results:
        status_counts[result["compliance"]] += 1
    
    # Colors for each status
    colors = {
        "Yes": "#2ecc71",
        "No": "#e74c3c",
        "Partial": "#f39c12",
        "n/a": "#95a5a6"
    }
    
    # Create horizontal bar chart
    fig = go.Figure()
    
    # Add bars
    y_position = 0
    for status, count in status_counts.items():
        if count > 0:  # Only show non-zero values
            fig.add_trace(go.Bar(
                x=[count],
                y=[y_position],
                orientation='h',
                name=status,
                marker_color=colors[status],
                text=[f"{status}: {count}"],
                textposition='auto',
                hoverinfo='text',
                showlegend=False
            ))
            y_position += 1
    
    # Update layout
    fig.update_layout(
        height=100,
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        barmode='stack',
        xaxis=dict(showticklabels=False, showgrid=False),
        yaxis=dict(showticklabels=False, showgrid=False)
    )
    
    return fig

def create_summary_chart(results: list) -> go.Figure:
    """Create summary chart of compliance results."""
    # Count compliance statuses
    status_counts = {"Yes": 0, "No": 0, "Partial": 0}
    for result in results:
        # Handle both dict and ComplianceResult objects
        compliance = result.compliance if hasattr(result, 'compliance') else result.get('compliance')
        if compliance != "n/a":
            status_counts[compliance] += 1
            
    # Create horizontal bar chart
    fig = go.Figure()
    
    # Add bars for each status
    colors = {"Yes": "#2ecc71", "No": "#e74c3c", "Partial": "#f1c40f"}
    for status, count in status_counts.items():
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

def format_compliance_status(status: str) -> str:
    """Format compliance status with color."""
    colors = {
        "Yes": "green",
        "No": "red",
        "Partial": "orange",
        "n/a": "gray"
    }
    color = colors.get(status, "gray")
    return f":{color}[{status}]"

def calculate_compliance_score(results: List[Dict[str, Any]]) -> float:
    """Calculate overall compliance score."""
    scores = {
        "Yes": 1.0,
        "No": 0.0,
        "Partial": 0.5
    }
    valid_scores = [scores[r["compliance"]] for r in results if r["compliance"] != "n/a"]
    return int(round(sum(valid_scores) / len(valid_scores) * 100)) if valid_scores else 0

def display_feedback_ui(db_service, result, manuscript, existing_feedback=None):
    """Display the feedback UI for a compliance result."""
    # Get existing feedback
    if existing_feedback is None:
        existing_feedback = db_service.get_feedback(manuscript.doi, result["item_id"], user_email=st.session_state.user_email)
    
    # If no feedback exists or user wants to change
    if not existing_feedback or st.session_state.get(f"change_feedback_{result['item_id']}", False):
        comments = st.text_area(
            "Your explanation (optional)",
            value=existing_feedback.comments if existing_feedback else "",
            key=f"comments_{result['item_id']}"
        )
        
        # Show rating options
        rating = st.radio(
            "If you disagree, please provide your rating",
            ["Yes", "No", "Partial", "N/A"],
            key=f"rating_{result['item_id']}",
            index=None  # No default selection
        )
        
        # Action buttons
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("❌ Disagree", key=f"disagree_{result['item_id']}"):
                if not rating:
                    st.error("Please select your rating before disagreeing")
                else:
                    feedback = Feedback(
                        doi=manuscript.doi,
                        item_id=result["item_id"],
                        rating=rating,
                        review_status="disagreed",
                        comments=comments,
                        user_email=st.session_state.user_email
                    )
                    db_service.save_feedback(feedback)
                    st.session_state[f"change_feedback_{result['item_id']}"] = False
                    st.rerun()

        
        with col2:
            if st.button("✅ Agree", key=f"agree_{result['item_id']}"):
                feedback = Feedback(
                    doi=manuscript.doi,
                    item_id=result["item_id"],
                    review_status="agreed",
                    comments=comments,
                    user_email=st.session_state.user_email
                )
                db_service.save_feedback(feedback)
                st.session_state[f"change_feedback_{result['item_id']}"] = False
                st.rerun()
                               
        with col3:
            if st.button("❓ Unsure", key=f"unsure_{result['item_id']}"):
                feedback = Feedback(
                    doi=manuscript.doi,
                    item_id=result["item_id"],
                    review_status="unsure",
                    comments=comments,
                    user_email=st.session_state.user_email
                )
                db_service.save_feedback(feedback)
                st.session_state[f"change_feedback_{result['item_id']}"] = False
                st.rerun()
    
    # Show existing feedback
    else:
        
        if existing_feedback.review_status == "agreed":
            st.markdown("✅ You agreed")
        
        elif existing_feedback.review_status == "disagreed":
            st.markdown(f"❌ You disagreed: {format_compliance_status(existing_feedback.rating)}")
        
        else:  # unsure
            st.markdown("❓ You're unsure")
            
        # Show comments if any
        if existing_feedback.comments:
            st.markdown(f"_Comment: {existing_feedback.comments}_")
        
        if st.button("Change", key=f"change_{result['item_id']}"):
            st.session_state[f"change_feedback_{result['item_id']}"] = True
            st.rerun()

def display_compliance_results(results: List[Dict[str, Any]], checklist_items: List[Dict[str, Any]], manuscript):
    """Display compliance results in an interactive table."""
    if not results:
        st.warning("No compliance results found for this manuscript.")
        return
        
    # Convert ComplianceResult objects to dictionaries if needed
    results_data = []
    for result in results:
        if hasattr(result, '__dict__'):
            results_data.append({
                'item_id': result.item_id,
                'compliance': result.compliance,
                'explanation': result.explanation,
                'quote': result.quote,
                'section': result.section,
                'created_at': result.created_at,
                'question': result.question
            })
        else:
            results_data.append(result)
    
    # Create a lookup for checklist items
    checklist_lookup = {item["item_id"]: item for item in checklist_items}
    
    # Get all feedback for this manuscript and user
    user_email = st.session_state.get("user_email")
    manuscript_feedback = {
        feedback.item_id: feedback 
        for feedback in st.session_state.db_service.get_all_feedback(manuscript.doi, user_email=user_email)
    }
    
    # Group results by category
    results_by_category = {}
    for result in results_data:
        item = checklist_lookup.get(result['item_id'])
        if item:
            category = item.get('category', 'Uncategorized')
            if category not in results_by_category:
                results_by_category[category] = []
            results_by_category[category].append(result)
    
    # Get severity from summary if available
    summary = st.session_state.db_service.get_summary(manuscript.doi)
    category_severity = {}
    if summary:
        for cat in summary.get('category_summaries', []):
            category_severity[cat['category']] = cat['severity'].upper()
    
    # Sort categories by severity
    sorted_categories = sorted(
        results_by_category.keys(),
        key=lambda x: severity_order.get(category_severity.get(x, 'UNKNOWN'), 4)
    )
    
    # Display results by category
    for category in sorted_categories:
        severity = category_severity.get(category, 'UNKNOWN')
        severity_indicator = severity_colors.get(severity, '')
        category_results = results_by_category[category]
        
        # Count feedback statuses for this category
        category_feedback = {
            "agreed": "✅",
            "disagreed": "❌",
            "unsure": "❓"
        }
        feedback_counts = {status: 0 for status in category_feedback.keys()}
        
        for result in category_results:
            feedback = manuscript_feedback.get(result['item_id'])
            if feedback:
                feedback_counts[feedback.review_status] += 1
        
        # Create feedback status string with repeated icons
        feedback_status = "".join([
            icon * count for status, (icon, count) in 
            ((s, (i, feedback_counts[s])) for s, i in category_feedback.items())
            if count > 0
        ])
        
        # Create category expander with count and feedback status
        with st.expander(f"{severity_indicator} {category} ({len(category_results)} items) {feedback_status}", expanded=False):
            # Display results in this category
            for result in category_results:
                # Get feedback status for this item
                feedback = manuscript_feedback.get(result['item_id'])
                feedback_icon = ""
                if feedback:
                    if feedback.review_status == "agreed":
                        feedback_icon = "✅ "
                    elif feedback.review_status == "disagreed":
                        feedback_icon = "❌ "
                    else:  # unsure
                        feedback_icon = "❓ "
                
                # Show item header without compliance status
                st.markdown(f"#### {result['item_id']}: {result['question']}")
                
                # Create two columns
                col1, col2 = st.columns(2)
                
                # Left column: AI Analysis
                with col1:
                    st.markdown("##### AI Analysis")
                    st.markdown(f"**Status:** {format_compliance_status(result['compliance'])}")
                    if result['explanation']:
                        st.markdown(f"**Explanation:** {result['explanation']}")
                    if result['quote']:
                        st.markdown(f"**Quote:** _{result['quote']}_")
                    if result['section']:
                        st.markdown(f"**Section in text:** {result['section']}")
                
                # Right column: Feedback
                with col2:
                    st.markdown("##### Your feedback")
                    display_feedback_ui(st.session_state.db_service, result, manuscript, manuscript_feedback.get(result['item_id']))
                
                # Add separator between items
                st.markdown("---")


def compliance_analysis_page():
    """Main compliance analysis page."""
    
    # Validate user email
    if 'user_email' not in st.session_state:
        st.error("Please enter your email on the home page first.")
        st.stop()
    
    # Get current manuscript
    manuscript = st.session_state.get("current_manuscript")
    if not manuscript:
        st.warning("Please select a manuscript first.")
        return
    
    # Get database service
    db_service = st.session_state.get("db_service")
    if not db_service:
        st.error("Database service not initialized.")
        return
    
    # Get results and checklist items
    results = db_service.get_compliance_results(manuscript.doi)
    checklist_items = db_service.get_checklist_items()
    summary = db_service.get_summary(manuscript.doi)
    
    if not summary:
        st.warning("No summary found for this manuscript. Please process the manuscript first.")
        return
    
    # Table 1: Manuscript info and compliance score
    table1_col1, table1_col2 = st.columns([1, 1])
    
    with table1_col1:
        # Display manuscript info with smaller font
        st.markdown(f"<h3 style='font-size: 18px;'><b>Title:</b> {manuscript.title}</h3>", unsafe_allow_html=True)
        authors_str = ", ".join(manuscript.authors) if isinstance(manuscript.authors, list) else manuscript.authors
        st.markdown(f"<p style='font-size: 14px;'><b>Authors:</b> {authors_str}</p>", unsafe_allow_html=True)
        
        # Create a row for DOI and analysis date
        doi_col1, doi_col2 = st.columns([1, 1])
        with doi_col1:
            st.markdown(f"<p style='font-size: 14px;'><b>DOI:</b> {manuscript.doi}</p>", unsafe_allow_html=True)
        with doi_col2:
            # Get latest analysis date
            latest_result = max(results, key=lambda x: x.created_at) if results else None
            if latest_result and latest_result.created_at:
                st.markdown(f"<p style='font-size: 14px; text-align: right;'><b>Analysis Date:</b> {latest_result.created_at.strftime('%Y-%m-%d %H:%M')}</p>", unsafe_allow_html=True)
    
    with table1_col2:
        # Calculate and display compliance score
        if results:
            scores = {
                "Yes": 1.0,
                "No": 0.0,
                "Partial": 0.5
            }
            valid_scores = [scores[r.compliance] for r in results if r.compliance != "n/a"]
            compliance_score = int(round(sum(valid_scores) / len(valid_scores) * 100)) if valid_scores else 0
            
            # Create columns for score display
            score_col1, score_col2 = st.columns([2, 1])
            
            with score_col1:
                # Show summary chart
                st.plotly_chart(create_summary_chart(results), use_container_width=True)
                
            with score_col2:
                # Show compliance score with large number
                st.markdown(f"""
                <div style='text-align: center; padding: 10px; background-color: #f0f2f6; border-radius: 10px;'>
                    <div style='font-size: 14px; color: #666;'>Compliance Score</div>
                    <div style='font-size: 36px; font-weight: bold; color: #1f77b4;'>{compliance_score}%</div>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Table 2: Summary and checklist categories
    table2_col1, table2_col2 = st.columns([1, 1])
    
    with table2_col1:
        # Display category summaries in a table
        st.markdown("### Summary by checklist category")
        
        # Create DataFrame with category summaries
        if summary and "category_summaries" in summary:
            data = []
            for cat in summary["category_summaries"]:
                severity = cat['severity'].upper()
                severity_indicator = severity_colors.get(severity, '')
                data.append({
                    'Category': f"{severity_indicator} {cat['category']}",
                    'Summary': cat['summary']
                })
            
            df = pd.DataFrame(data)
            
            # Create a styled table with custom column widths
            st.markdown(
                """
                <style>
                .custom-table {
                    width: 100%;
                    table-layout: fixed;
                }
                .custom-table td:first-child {
                    width: 30%;
                    white-space: nowrap;
                    text-align: left !important;
                    padding-right: 15px;
                }
                .custom-table td:nth-child(2) {
                    width: 70%;
                }
                .custom-table th {
                    text-align: left !important;
                }
                .custom-table td {
                    word-wrap: break-word;
                    vertical-align: top;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
            
            # Convert DataFrame to HTML with the custom class
            html = df.to_html(classes=['custom-table', 'dataframe'], index=False, escape=False)
            st.markdown(html, unsafe_allow_html=True)
    
    with table2_col2:
        # Display overview
        st.markdown(summary["overview"])
    
    st.markdown("---")
    st.markdown("### Review & Feedback")
    st.markdown("Did AI get something wrong? Please provide your feedback.")
    
    # Add "Agree with all" button
    if st.button("I agree with all open items", use_container_width=True):
        # Get all existing feedback
        existing_feedback = {
            f.item_id: f 
            for f in st.session_state.db_service.get_all_feedback(manuscript.doi)
        }
        
        # Create "Agree" feedback for items without existing feedback
        new_feedback = []
        for result in results:
            if result.item_id not in existing_feedback:
                feedback = Feedback(
                    doi=manuscript.doi,
                    item_id=result.item_id,
                    review_status="agreed",
                    rating=None,
                    comments="",
                    created_at=datetime.now(),
                    user_email=st.session_state.user_email
                )
                new_feedback.append(feedback)
        
        # Save all new feedback
        if new_feedback:
            for feedback in new_feedback:
                st.session_state.db_service.save_feedback(feedback)
            st.success(f"Marked {len(new_feedback)} items as 'Agree'")
            # Force a page rerun to refresh all feedback
            st.rerun()
    
    # Display detailed results
    display_compliance_results(results, checklist_items, manuscript)

if __name__ == "__main__":
    st.set_page_config(page_title="Review", layout="wide")
    compliance_analysis_page()
