"""
Sidebar component for Taskeyy.
"""
import streamlit as st
from taskeyy.database import TaskDatabase

# Lista de emojis sugeridos para listas
LIST_ICONS = ["📁", "🏠", "🚀", "🎯", "💼", "🏢", "💡", "📊", "🛠️", "🌱"]

def render_sidebar(db: TaskDatabase) -> None:
    """
    Render the sidebar with utilities.
    """
    st.sidebar.title("✅ Taskeyy")
    st.sidebar.markdown("Gestão de tarefas e pendências")
    st.sidebar.divider()
    
    with st.sidebar.expander("➕ Nova Lista"):
        new_list_name = st.text_input("Nome da lista", key="new_list_input")
        
        # Seletor de ícone
        new_list_icon = st.selectbox(
            "Ícone",
            LIST_ICONS,
            key="new_list_icon"
        )
        
        if st.button("Criar Lista", use_container_width=True):
            if new_list_name.strip():
                success = db.create_list(new_list_name.strip(), new_list_icon)
                if success:
                    st.success("Lista criada!")
                    if "new_list_input" in st.session_state:
                        del st.session_state["new_list_input"]
                    st.rerun()
                else:
                    st.error("Lista já existe.")
            else:
                st.warning("Digite um nome válido.")