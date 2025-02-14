"""
ReproAI - Checklists Page
-------------------------

This page provides the interface for managing reproducibility checklists.

Author: ReproAI Team
"""

import streamlit as st
import pandas as pd
from app.services.db_service import DatabaseService
import os

# Load CSS
def load_css():
    """Load custom CSS styles."""
    css_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'styles.css')
    with open(css_file, 'r') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

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

def display_checklist_items(db_service: DatabaseService):
    """Display the checklist view."""
    st.markdown('<h2 class="section-title">Current checklist</h2>', unsafe_allow_html=True)
    
    st.markdown("""
        <div class="css-1r6slb0">
            <p><strong>Title:</strong> Nature Research Reporting Summary</p>
            <p><strong>Section:</strong> Behavioural & social sciences study design</p>
            <p><strong>Source:</strong> <a href="https://www.nature.com/documents/nr-reporting-summary.pdf" target="_blank">www.nature.com/documents/nr-reporting-summary.pdf</a></p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class="ai-insight">
            Text from original source is shown in italics. The text is split to items for stepwise analysis.
        </div>
    """, unsafe_allow_html=True)
    
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
                            "Item": item.get('question', ''),
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

def manage_checklist_items(db_service: DatabaseService):
    """Form to add or edit checklist items."""
    st.markdown('<h2 class="section-title">Manage Checklist Items</h2>', unsafe_allow_html=True)
    
    # Get existing categories and items
    checklist_items = db_service.get_checklist_items()
    categories = sorted(list(set(item.get('category', '') for item in checklist_items if item.get('category'))))
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
            col1, col2 = st.columns(2)
            submit = col1.form_submit_button("Add Item")
            if col2.form_submit_button("Cancel"):
                st.session_state.adding_new_item = False
                st.experimental_rerun()
            
            if submit:
                if not all([category, item_text]):
                    st.error("Please fill in all required fields")
                    return
                
                try:
                    new_item = {
                        "category": category,
                        "original": original,
                        "question": item_text,
                        "description": description
                    }
                    db_service.save_checklist_item(new_item)
                    st.success(" New item added successfully!")
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
                
                if st.form_submit_button("Save Changes"):
                    if not all([category, item_text]):
                        st.error("Please fill in all required fields")
                        return
                    
                    try:
                        updated_item = {
                            "item_id": current_item.get('item_id'),
                            "category": category,
                            "original": original,
                            "question": item_text,
                            "description": description
                        }
                        db_service.update_checklist_item(updated_item)
                        st.success(" Item updated successfully!")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error updating item: {str(e)}")

def main():
    """Main app function."""
    # Load CSS
    load_css()
    
    # Sidebar Navigation
    st.sidebar.title("Instructions")
    st.sidebar.write("Later on, user may choose which checklist to use for the analysis.")
    
    # Main content
    st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: baseline;">
            <h1 class="custom-title">Checklists</h1>
            </div>
    """, unsafe_allow_html=True)
    
    # Initialize database service
    db_service = DatabaseService(st.secrets["MONGODB_URI"])
    
    # Create tabs
    tab1, tab2 = st.tabs([
        "View Checklist",
        "Manage Items"
    ])
    
    with tab1:
        display_checklist_items(db_service)
    
    with tab2:
        manage_checklist_items(db_service)

if __name__ == "__main__":
    main()
