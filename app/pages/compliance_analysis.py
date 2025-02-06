import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List
import plotly.graph_objects as go
import plotly.express as px

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

def display_compliance_results(results: List[Dict[str, Any]], checklist_items: List[Dict[str, Any]]):
    """Display compliance results in an interactive table."""
    if not results:
        st.warning("No compliance results found for this manuscript.")
        return
        
    # Create a lookup for checklist items
    checklist_lookup = {item["item_id"]: item for item in checklist_items}
    
    # Calculate compliance score
    compliance_score = calculate_compliance_score(results)
    
    # Create summary dashboard
    st.markdown("### Summary Dashboard")
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
        
    with col3:
        # Show analysis timestamp
        latest_result = max(results, key=lambda x: x["created_at"]) if results else None
        if latest_result and latest_result.get("created_at"):
            st.markdown(f"""
            <div style='text-align: center; padding: 10px; background-color: #f0f2f6; border-radius: 10px;'>
                <div style='font-size: 14px; color: #666;'>Analysis Date</div>
                <div style='font-size: 16px; color: #666;'>{latest_result["created_at"].strftime("%Y-%m-%d %H:%M")}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Prepare data for display
    display_data = []
    for result in results:
        item = checklist_lookup.get(result["item_id"], {})
        display_data.append({
            "ID": result["item_id"],
            "Category": item.get("category", "Uncategorized"),
            "Question": item.get("question", result.get("question", "Unknown")),
            "Status": format_compliance_status(result["compliance"]),
            "Explanation": result["explanation"],
            "Quote": result["quote"],
            "Section Found": result["section"],
            "Section": item.get("section", ""),
            "Original": item.get("original", ""),
            "Last Updated": result["created_at"].strftime("%Y-%m-%d %H:%M") if result.get("created_at") else "Unknown"
        })
    
    # Convert to DataFrame for easier filtering
    df = pd.DataFrame(display_data)
    
    # Add filters
    st.markdown("### Filters")
    col1, col2, col3 = st.columns(3)
    with col1:
        category_filter = st.multiselect(
            "Filter by Category",
            options=sorted(df["Category"].unique()),
            default=[]
        )
    with col2:
        section_filter = st.multiselect(
            "Filter by Section",
            options=sorted(set(item.get("section", "") for item in checklist_items if item.get("section"))),
            default=[]
        )
    with col3:
        status_filter = st.multiselect(
            "Filter by Status",
            options=["Yes", "No", "Partial", "n/a"],
            default=[]
        )
    
    # Apply filters
    if category_filter:
        df = df[df["Category"].isin(category_filter)]
    if section_filter:
        df = df[df["Section"].isin(section_filter)]
    if status_filter:
        df = df[df["Status"].isin([format_compliance_status(s) for s in status_filter])]
    
    # Display results
    st.markdown("### Detailed Results")
    for _, row in df.iterrows():
        with st.expander(f"{row['ID']} - {row['Question']}", expanded=False):
            cols = st.columns([2, 1])
            with cols[0]:
                st.markdown(f"**Status:** {row['Status']}")
                st.markdown(f"**Category:** {row['Category']}")
                st.markdown(f"**Explanation:** {row['Explanation']}")
                if row['Quote']:
                    st.markdown(f"**Quote:** _{row['Quote']}_")
                if row['Section Found']:
                    st.markdown(f"**Section Found:** {row['Section Found']}")
                if row['Section']:
                    st.markdown(f"**Section:** {row['Section']}")
                if row['Original']:
                    st.markdown(f"**Original Item:** {row['Original']}")
            with cols[1]:
                st.markdown(f"**Last Updated:** {row['Last Updated']}")
                
                # Placeholder for future feedback buttons
                st.markdown("---")
                st.markdown("_Feedback options will be added here_")

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
    display_compliance_results(results, checklist_items)

if __name__ == "__main__":
    st.set_page_config(page_title="Detailed Results", layout="wide")
    compliance_analysis_page()
