"""Checklist view page."""
import streamlit as st
import pandas as pd
from app.services.db_service import DatabaseService

def calculate_compliance_score(compliances: list) -> float:
    """Calculate compliance score from a list of compliance values."""
    scores = {
        "Yes": 1.0,
        "No": 0.0,
        "Partial": 0.5,
        "n/a": None
    }
    valid_scores = [scores[c] for c in compliances if scores[c] is not None]
    return int(round(sum(valid_scores) / len(valid_scores) * 100)) if valid_scores else 0

def format_compliance_status(status: str):
    """Format compliance status with color."""
    colors = {
        "Yes": "#2ecc71",
        "No": "#e74c3c",
        "Partial": "#f1c40f",
        "n/a": "#95a5a6"
    }
    return f"<span style='color: {colors[status]}'>{status}</span>"

def checklist_view_page(db_service: DatabaseService):
    """Display the checklist view."""
    st.markdown("<h2 style='font-size: 24px;'>Checklist</h2>", unsafe_allow_html=True)
    st.markdown("Title: Nature Research Reporting Summary")
    st.markdown("Section: Behavioural & social sciences study design")
    st.markdown("Source: [www.nature.com/documents/nr-reporting-summary.pdf](https://www.nature.com/documents/nr-reporting-summary.pdf)")
    st.write("---")
    st.markdown("Original guidance is shown in italics. That is split to items for AI-assisted analysis.")
    
    # Get checklist items and all compliance results from database
    checklist_items = db_service.get_checklist_items()
    all_manuscripts = db_service.get_all_manuscripts()
    
    # Get all compliance results for statistics
    all_results = {}
    for manuscript in all_manuscripts:
        results = db_service.get_compliance_results(manuscript.doi)
        for result in results:
            if result.item_id not in all_results:
                all_results[result.item_id] = []
            all_results[result.item_id].append(result.compliance)
    
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
                    total = len(compliances)
                    
                    if total > 0:
                        yes_count = compliances.count("Yes")
                        no_count = compliances.count("No")
                        partial_count = compliances.count("Partial")
                        na_count = compliances.count("n/a")
                        
                        data.append({
                            "Item": item.get('text', item.get('question', '')),
                            "Yes": f"{int(yes_count/total*100)}%",
                            "No": f"{int(no_count/total*100)}%",
                            "Partial": f"{int(partial_count/total*100)}%",
                            "N/A": f"{int(na_count/total*100)}%",
                            "Compliance": f"{calculate_compliance_score(compliances)}%"
                        })
                
                if data:
                    df = pd.DataFrame(data)
                    
                    # Style the table
                    styled_df = df.style.set_properties(**{
                        'text-align': 'left',
                        'font-size': '0.9em',
                        'padding': '8px'
                    })
                    
                    # Color compliance scores
                    def color_compliance(val):
                        score = int(val.rstrip('%'))
                        if score >= 80:
                            color = '#2ecc71'  # Green
                        elif score >= 50:
                            color = '#f1c40f'  # Yellow
                        else:
                            color = '#e74c3c'  # Red
                        return f'color: {color}; font-weight: bold'
                    
                    styled_df = styled_df.map(color_compliance, subset=['Compliance'])
                    
                    # Display the table with column configuration
                    st.dataframe(
                        styled_df,
                        column_config={
                            "Item": st.column_config.TextColumn(
                                "Item",
                                width="large",  
                                help="Checklist item text"
                            ),
                            "Yes": st.column_config.TextColumn(
                                "Yes",
                                width="extra-small"  
                            ),
                            "No": st.column_config.TextColumn(
                                "No",
                                width="extra-small"
                            ),
                            "Partial": st.column_config.TextColumn(
                                "Partial",
                                width="extra-small"
                            ),
                            "N/A": st.column_config.TextColumn(
                                "N/A",
                                width="extra-small"
                            ),
                            "Compliance": st.column_config.TextColumn(
                                "Compliance",
                                width="extra-small"
                            )
                        },
                        use_container_width=True,
                        hide_index=True
                    )
                
                st.write("---")  # Separator between groups
    else:
        st.warning("No checklist items found in database")
