"""
ReproAI - Checklist Management View
----------------------------------

This module provides the interface for managing checklist items.

Author: ReproAI Team
"""

import streamlit as st
from app.services.db_service import DatabaseService

def manage_checklist_items(db_service: DatabaseService):
    """Form to add or edit checklist items."""
    st.markdown('<h2 class="section-title">Manage Checklist Items</h2>', unsafe_allow_html=True)
    
    # Get existing categories and items
    checklist_items = db_service.get_checklist_items()
    categories = sorted(list(set(item.get('category', '') for item in checklist_items if item.get('category'))))
    sections = sorted(list(set(item.get('section', '') for item in checklist_items if item.get('section'))))
    
    items_by_category = {}
    for item in checklist_items:
        cat = item.get('category', '')
        if cat not in items_by_category:
            items_by_category[cat] = {
                'original': item.get('original', ''),
                'items': []
            }
        items_by_category[cat]['items'].append(item)
    
    # Initialize session state
    if 'adding_new_item' not in st.session_state:
        st.session_state.adding_new_item = False
    
    # Select existing category
    category = st.selectbox("Category", categories, help="Select the category this item belongs to")
    
    # Select item to edit if category is selected
    current_item = None
    if category and category in items_by_category:
        items = sorted(items_by_category[category]['items'], key=lambda x: x.get('question', ''))
        selected_item = st.selectbox(
            "Select Item to Edit",
            options=items,
            format_func=lambda x: x.get('question', ''),
            help="Choose an item to edit"
        )
        if selected_item:
            current_item = selected_item
    
    # Show the original text for the selected category
    original = ""
    if category and category in items_by_category:
        original = items_by_category[category]['original']
        if original:
            st.markdown("**Original Text:**")
            st.markdown(f"*{original}*")
            st.write("---")
    
    # Toggle for adding new item
    col1, col2 = st.columns([0.85, 0.15])
    with col2:
        if st.button("Add New" if not st.session_state.adding_new_item else "Edit Existing", use_container_width=True):
            st.session_state.adding_new_item = not st.session_state.adding_new_item
            st.experimental_rerun()
    
    if st.session_state.adding_new_item:
        with st.form("add_item_form"):
            st.markdown('<h3 class="section-subtitle">Add New Item</h3>', unsafe_allow_html=True)
            item_text = st.text_area("Item", height=100, help="The specific item to check")
            description = st.text_area("Description", help="Detailed description of what this item checks for")
            section = st.selectbox(
                "Section",
                [""] + sections,
                help="The section this item belongs to"
            )
            col1, col2 = st.columns(2)
            submit = col1.form_submit_button("Add Item")
            if col2.form_submit_button("Cancel"):
                st.session_state.adding_new_item = False
                st.experimental_rerun()
            
            if submit:
                if not all([category, item_text, section]):
                    st.error("Please fill in all required fields")
                    return
                
                try:
                    new_item = {
                        "category": category,
                        "original": original,
                        "question": item_text,
                        "description": description,
                        "section": section
                    }
                    db_service.save_checklist_item(new_item)
                    st.success("New item added successfully!")
                    st.session_state.adding_new_item = False
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error adding item: {str(e)}")
    
    else:  # Edit existing item
        if current_item:
            with st.form("edit_item_form"):
                st.markdown('<h3 class="section-subtitle">Edit Item</h3>', unsafe_allow_html=True)
                item_text = st.text_area("Item", value=current_item.get('question', ''), height=100, help="The specific item to check")
                description = st.text_area("Description", value=current_item.get('description', ''), help="Detailed description of what this item checks for")
                section = st.selectbox(
                    "Section",
                    [""] + sections,
                    index=sections.index(current_item.get('section', '')) + 1 if current_item.get('section', '') in sections else 0,
                    help="The section this item belongs to"
                )
                
                if st.form_submit_button("Save Changes"):
                    if not all([category, item_text, section]):
                        st.error("Please fill in all required fields")
                        return
                    
                    try:
                        updated_item = {
                            "item_id": current_item.get('item_id'),
                            "category": category,
                            "original": original,
                            "question": item_text,
                            "description": description,
                            "section": section
                        }
                        db_service.update_checklist_item(updated_item)
                        st.success("Item updated successfully!")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error updating item: {str(e)}")
