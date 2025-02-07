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
    return round(sum(valid_scores) / len(valid_scores) * 100, 1) if valid_scores else 0.0

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
    
    # Display results with feedback options
    for result in results_data:
        with st.expander(f"Item {result['item_id']}: {result['question']}", expanded=False):
            # Display result
            st.markdown(f"**Status:** {format_compliance_status(result['compliance'])}")
            if result['explanation']:
                st.markdown(f"**Explanation:** {result['explanation']}")
            if result['quote']:
                st.markdown(f"**Quote:** _{result['quote']}_")
            if result['section']:
                st.markdown(f"**Section Found:** {result['section']}")
            
            # Get existing feedback
            feedback = st.session_state.db_service.get_feedback(manuscript.doi, result['item_id'])
            
            # Feedback section
            st.divider()
            st.write("**Your Feedback**")
            
            # Feedback buttons in columns
            cols = st.columns(4)
            selected_rating = None
            
            # Define feedback options with their colors
            feedback_options = [
                ("Yes", "#2ecc71"),  # Green
                ("No", "#e74c3c"),  # Red
                ("Partial", "#f39c12"),  # Orange
                ("N/A", "#95a5a6")  # Gray
            ]
            
            for i, (rating, color) in enumerate(feedback_options):
                with cols[i]:
                    button_style = f"""
                        <style>
                            div[data-testid="stButton"] button {{
                                background-color: {color if feedback and feedback.rating == rating else 'white'};
                                color: {color if feedback and feedback.rating != rating else 'black'};
                                border: 1px solid {color};
                                width: 100%;
                            }}
                            div[data-testid="stButton"] button:hover {{
                                background-color: {color};
                                color: white;
                                border: 1px solid {color};
                            }}
                        </style>
                    """
                    st.markdown(button_style, unsafe_allow_html=True)
                    if st.button(
                        rating,
                        key=f"btn_{result['item_id']}_{rating}",
                        use_container_width=True
                    ):
                        selected_rating = rating
            
            # Comments field and submit button in columns
            comment_col, button_col = st.columns([3, 1])
            with comment_col:
                comments = st.text_area(
                    "Comments",
                    value=feedback.comments if feedback else "",
                    key=f"comments_{result['item_id']}",
                    placeholder="Add your comments here..."
                )
            
            with button_col:
                submit_clicked = st.button(
                    "Submit Feedback",
                    key=f"submit_{result['item_id']}",
                    type="primary",
                    use_container_width=True
                )
            
            # Save feedback if rating changed or submit clicked
            if selected_rating or submit_clicked:
                if not selected_rating and not feedback:
                    st.warning("Please select a rating before submitting feedback.")
                else:
                    new_feedback = Feedback(
                        doi=manuscript.doi,
                        item_id=result['item_id'],
                        rating=selected_rating or (feedback.rating if feedback else None),
                        comments=comments
                    )
                    if st.session_state.db_service.save_feedback(new_feedback):
                        st.success("Feedback saved!")
                    else:
                        st.error("Error saving feedback")

def compliance_analysis_page():
    """Main compliance analysis page."""
    # Use smaller font for title
    st.markdown("<h2 style='font-size: 24px;'>Detailed Results</h2>", unsafe_allow_html=True)
    
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
    st.set_page_config(page_title="Detailed Results", layout="wide")
    compliance_analysis_page()
