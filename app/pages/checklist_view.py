"""Checklist view page."""
import streamlit as st
import pandas as pd
from app.services.db_service import DatabaseService

def checklist_view_page(db_service: DatabaseService):
    """Display the checklist view."""
    st.header("Checklist")
    st.markdown("Title: Nature Research Reporting Summary")
    st.markdown("Section: Behavioural & social sciences study design")
    st.markdown("Source: [www.nature.com/documents/nr-reporting-summary.pdf](https://www.nature.com/documents/nr-reporting-summary.pdf)")
    st.write("---")
    st.markdown("Original guidance is shown in italics. That is split to items for AI-assisted analysis.")
    
    # Add custom table styling
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
    
    # Get checklist items from database
    checklist_items = db_service.get_checklist_items()
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
                
                # Create DataFrame for the grouped items
                data = []
                for item in sorted(grouped_items, key=lambda x: x.get('item_id', '')):
                    data.append({
                        'Item': f"{item.get('item_id', '')}. {item.get('question', '')}",
                        'Description': item.get('description', '') if item.get('description', '') else ''
                    })
                
                df = pd.DataFrame(data)
                
                # Convert DataFrame to HTML with the custom class
                html = df.to_html(classes=['custom-table', 'dataframe'], index=False, escape=False)
                st.markdown(html, unsafe_allow_html=True)
                
                st.write("---")  # Separator between groups
    else:
        st.warning("No checklist items found in database")
