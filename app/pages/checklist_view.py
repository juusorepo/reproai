"""Checklist view page."""
import streamlit as st
from app.services.db_service import DatabaseService

def checklist_view_page(db_service: DatabaseService):
    """Display the checklist view."""
    st.header("Checklist")
    st.markdown("Title: Nature Research Reporting Summary")
    st.markdown("Section: Behavioural & social sciences study design")
    st.markdown("Source: [www.nature.com/documents/nr-reporting-summary.pdf](https://www.nature.com/documents/nr-reporting-summary.pdf)")
    st.write("---")
    st.markdown("Original guidance is shown in italics. That is split to items for AI-assisted analysis.")
    
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
                
                # Then list all questions related to this original text
                for item in sorted(grouped_items, key=lambda x: x.get('item_id', '')):
                    st.markdown(f"**{item.get('item_id', '')}. {item.get('question', '')}**")
                
                st.write("---")  # Separator between groups
    else:
        st.warning("No checklist items found in database")
