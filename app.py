"""
Streamlit Interface for Taskeyy.
"""
import sys
from pathlib import Path

# Add src to sys.path for imports
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import streamlit as st
from taskeyy.database import TaskDatabase

# Importando os componentes de UI
from taskeyy.ui.sidebar import render_sidebar
from taskeyy.ui.lists import render_lists_panel
from taskeyy.ui.tasks import render_tasks_panel
from taskeyy.ui.details import render_details_panel

# =============================================================
# Page Configuration
# =============================================================

st.set_page_config(
    page_title="Taskeyy",
    page_icon="✅",
    layout="wide"
)

# =============================================================
# Custom CSS
# =============================================================

def render_custom_css() -> None:
    st.markdown(
        """
        <style>
        .block-container { padding-top: 2rem !important; padding-bottom: 1rem !important; }
        </style>
        """,
        unsafe_allow_html=True
    )

# =============================================================
# Main
# =============================================================

def main() -> None:
    render_custom_css()
    
    db = TaskDatabase()
    
    render_sidebar(db)
    
    col_left, col_center, col_right = st.columns([1, 2, 3.5])
    
    with col_left:
        render_lists_panel(db)
        
    with col_center:
        render_tasks_panel(db)
        
    with col_right:
        render_details_panel(db)

if __name__ == "__main__":
    main()