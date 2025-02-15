import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List
import plotly.graph_objects as go
import plotly.express as px
from app.models.manuscript import Manuscript
from app.models.feedback import Feedback

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

def display_feedback_ui(db_service, result, manuscript, existing_feedback=None):
    """Display the feedback UI for a compliance result."""
    # Get existing feedback
    if existing_feedback is None:
        existing_feedback = db_service.get_feedback(manuscript.doi, result["item_id"])
    
    # If no feedback exists or user wants to change
    if not existing_feedback or st.session_state.get(f"change_feedback_{result['item_id']}", False):
        comments = st.text_area(
            "Comments (optional)",
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
                        comments=comments
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
                    comments=comments
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
                    comments=comments
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
    
    # Get all feedback for this manuscript
    manuscript_feedback = {
        feedback.item_id: feedback 
        for feedback in st.session_state.db_service.get_all_feedback(manuscript.doi)
    }
    
    # Calculate compliance score
    compliance_score = calculate_compliance_score(results_data)
    
    # Create columns for dashboard
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        # Show summary chart
        st.plotly_chart(create_summary_chart(results_data), use_container_width=True)
    
    with col2:
        # Show compliance score with large number
        st.markdown(f"""
        <div style='text-align: center; padding: 10px; background-color: #f0f2f6; border-radius: 10px;'>
            <div style='font-size: 14px; color: #666;'>Compliance Score</div>
            <div style='font-size: 36px; font-weight: bold; color: #1f77b4;'>{compliance_score}%</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        # Show analysis timestamp
        latest_result = max(results_data, key=lambda x: x["created_at"]) if results_data else None
        if latest_result and latest_result.get("created_at"):
            st.markdown(f"""
            <div style='text-align: center; padding: 10px; background-color: #f0f2f6; border-radius: 10px;'>
                <div style='font-size: 14px; color: #666;'>Analysis Date</div>
                <div style='font-size: 16px; color: #666;'>{latest_result["created_at"].strftime("%Y-%m-%d %H:%M")}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
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
    
    # Define severity indicators and order
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
    
    # Sort categories by severity
    sorted_categories = sorted(
        results_by_category.keys(),
        key=lambda x: severity_order.get(category_severity.get(x, 'UNKNOWN'), 4)
    )
    
    # Display results by category
    for category in sorted_categories:
        severity = category_severity.get(category, 'UNKNOWN')
        severity_indicator = severity_colors.get(severity, '⚪️')
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
                
                # Right column: Review & Feedback
                with col2:
                    st.markdown("##### Review & Feedback")
                    display_feedback_ui(st.session_state.db_service, result, manuscript, manuscript_feedback.get(result['item_id']))
                
                # Add separator between items
                st.markdown("---")

def compliance_analysis_page():
    """Main compliance analysis page."""
    # Use smaller font for title
    st.markdown("<h2 style='font-size: 24px;'>Review Results</h2>", unsafe_allow_html=True)
    
    # Get current manuscript
    manuscript = st.session_state.get("current_manuscript")
    if not manuscript:
        st.warning("Please select a manuscript first.")
        return
        
    # Display manuscript info with smaller font
    st.markdown(f"<h3 style='font-size: 18px;'>Analyzing: {manuscript.title}</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size: 14px;'><b>DOI:</b> {manuscript.doi}</p>", unsafe_allow_html=True)
    
    # Get database service
    db_service = st.session_state.get("db_service")
    if not db_service:
        st.error("Database service not initialized.")
        return
    
    # Get results and checklist items
    results = db_service.get_compliance_results(manuscript.doi)
    checklist_items = db_service.get_checklist_items()
    
    # Display results
    display_compliance_results(results, checklist_items, manuscript)

if __name__ == "__main__":
    st.set_page_config(page_title="Review", layout="wide")
    compliance_analysis_page()
