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
from taskeyy.ui.dashboard import render_dashboard

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
        /* Reduz o padding do topo */
        .block-container { 
            padding-top: 2rem !important; 
            padding-bottom: 1rem !important; 
        }

        /* Aplica rolagem independente nas colunas central e direita */
        div[data-testid="column"]:nth-of-type(2),
        div[data-testid="column"]:nth-of-type(3) {
            max-height: calc(100vh - 120px); /* Ajusta a altura com base na tela */
            overflow-y: auto; /* Habilita a barra de rolagem */
            padding-right: 10px; /* Espaço para a barra não colar no texto */
        }

        /* Esconde a barra de rolagem padrão do Streamlit na página toda */
        body {
            overflow: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# =============================================================
# Main
# =============================================================

# =============================================================
# Main
# =============================================================

def main() -> None:
    render_custom_css()
    
    db = TaskDatabase()
    
    # Renderiza a barra lateral (que controla st.session_state["view"])
    render_sidebar(db)
    
    # Verifica qual tela deve ser exibida
    current_view = st.session_state.get("view", "tasks")
    
    if current_view == "dashboard":
        # Chama a função do dashboard (que você vai criar)
        render_dashboard(db)
    else:
        # Visão padrão de 3 painéis
        col_left, col_center, col_right = st.columns([1, 2, 3.5])
        
        with col_left:
            render_lists_panel(db)
            
        with col_center:
            render_tasks_panel(db)
            
        with col_right:
            render_details_panel(db)


if __name__ == "__main__":
    main()
