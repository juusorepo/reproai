"""
ReproAI - System Prompts
-----------------------

This page displays all system prompts used in the ReproAI system.
"""

import streamlit as st
import os
from pathlib import Path
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="ReproAI Prompts",
    page_icon="📝",
    layout="wide"
)

# Title
st.title("📝 System Prompts")
st.markdown("""
View and edit system prompts used to analyze manuscripts and generate results.
""")

# Get all prompt files
prompts_dir = Path('app/prompts')
prompt_files = sorted(prompts_dir.glob('*.txt'))

# Create tabs for each prompt
tabs = st.tabs([f.stem.replace('_', ' ').title() for f in prompt_files])

# Display each prompt in its own tab
for tab, prompt_file in zip(tabs, prompt_files):
    with tab:
        st.markdown(f"### {prompt_file.stem.replace('_', ' ').title()}")
        
        # Read and display prompt content
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                content = f.read()
                st.code(content, language='text')
                
            # Add file info
            file_stat = os.stat(prompt_file)
            st.caption(f"""
            **File**: `{prompt_file.name}`  
            **Last modified**: {datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}  
            **Size**: {file_stat.st_size:,} bytes
            """)
            
        except Exception as e:
            st.error(f"Error reading prompt file {prompt_file.name}: {str(e)}")
