"""
Streamlit Interface for Taskeyy.

This module provides the web interface for the task manager.
It uses a 3-panel layout: Lists (left), Tasks (center),
and Task Details (right).
"""

import sys
from pathlib import Path

# Add src to sys.path for imports
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import streamlit as st
import pandas as pd
from datetime import date

from taskeyy.database import TaskDatabase


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
    """
    Inject custom CSS to adjust the layout and visuals.
    """

    st.markdown(
        """
        <style>
        /* Reduz o padding do topo */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 1rem !important;
        }
        
        /* Estilo para os cards de tarefas */
        .task-card {
            padding: 10px;
            border-radius: 5px;
            background-color: #f0f2f6;
            margin-bottom: 10px;
            cursor: pointer;
        }
        .task-title {
            font-weight: bold;
            color: #005B70;
        }
        .task-meta {
            font-size: 0.8em;
            color: #666;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


# =============================================================
# Sidebar / Utilities
# =============================================================

def render_sidebar(db: TaskDatabase) -> None:
    """
    Render the sidebar with utilities.
    """
    
    st.sidebar.title("✅ Taskeyy")
    st.sidebar.markdown("Gestão de tarefas e pendências")
    
    st.sidebar.divider()
    
    # Create List form
    with st.sidebar.expander("➕ Nova Lista"):
        new_list_name = st.text_input("Nome da lista", key="new_list_input")
        if st.button("Criar Lista", use_container_width=True):
            if new_list_name.strip():
                success = db.create_list(new_list_name.strip())
                if success:
                    st.success("Lista criada!")
                    # Limpar o campo
                    if "new_list_input" in st.session_state:
                        del st.session_state["new_list_input"]
                    st.rerun()
                else:
                    st.error("Lista já existe.")
            else:
                st.warning("Digite um nome válido.")


# =============================================================
# Panel 1: Lists (Left)
# =============================================================

def render_lists_panel(db: TaskDatabase) -> None:
    """
    Render the left panel with all lists.
    """
    
    st.subheader("📁 Listas")
    
    lists = db.get_lists()
    
    if not lists:
        st.info("Nenhuma lista encontrada.")
        return

    for lst in lists:
        if st.button(
            lst["name"], 
            key=f"list_{lst['id']}",
            use_container_width=True,
            type="primary" if st.session_state.get("selected_list_id") == lst["id"] else "secondary"
        ):
            st.session_state["selected_list_id"] = lst["id"]
            st.session_state["selected_task_id"] = None  # Reset task selection
            st.rerun()


# =============================================================
# Panel 2: Tasks (Center)
# =============================================================

def render_tasks_panel(db: TaskDatabase) -> None:
    """
    Render the center panel with tasks from the selected list.
    """
    
    list_id = st.session_state.get("selected_list_id")
    
    if not list_id:
        st.info("👈 Selecione uma lista na esquerda.")
        return

    # Get list name
    lists = db.get_lists()
    list_name = next((l["name"] for l in lists if l["id"] == list_id), "Desconhecida")
    
    st.subheader(f"📋 Tarefas: {list_name}")
    
    # Add Task Button (Opens form)
    # Usamos uma chave única para o expander para podermos fechá-lo
    with st.expander("➕ Nova Tarefa", expanded=st.session_state.get("expand_task_form", False)):
        title = st.text_input("Título", key="task_title")
        desc = st.text_area("Descrição", key="task_desc")
        
        col1, col2 = st.columns(2)
        with col1:
            priority = st.selectbox("Prioridade", ["Baixa", "Média", "Alta", "Crítico"], key="task_prio")
            status = st.selectbox("Status", ["Backlog", "Fazendo", "Bloqueio", "Feito"], key="task_status")
        with col2:
            origin = st.text_input("Origem (ex: Projeto X)", key="task_origin")
            date_planned = st.date_input("Data Planejada", value=None, key="task_date")
            
        if st.button("Salvar Tarefa", type="primary"):
            if title.strip():
                date_str = date_planned.strftime("%Y-%m-%d") if date_planned else None
                db.create_task(
                    list_id=list_id,
                    title=title,
                    description=desc,
                    status=status,
                    priority=priority,
                    origin=origin,
                    date_planned=date_str
                )
                
                # Limpar os campos do formulário
                keys_to_clear = ["task_title", "task_desc", "task_prio", "task_status", "task_origin", "task_date"]
                for key in keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]
                
                # Fechar o expander
                st.session_state["expand_task_form"] = False
                
                st.success("Tarefa criada!")
                st.rerun()
            else:
                st.warning("O título é obrigatório.")

    st.divider()

    # List Tasks
    tasks = db.get_tasks_by_list(list_id)
    
    if not tasks:
        st.write("Nenhuma tarefa nesta lista.")
        return

    for task in tasks:
        # Task Card layout
        with st.container():
            col_title, col_status = st.columns([3, 1])
            
            with col_title:
                st.markdown(f"**{task['title']}**")
                st.caption(f"Origem: {task['origin'] or 'N/A'} | Prioridade: {task['priority']}")
            
            with col_status:
                # Inline status update button
                if st.button(f"➡️ {task['status']}", key=f"status_{task['id']}"):
                    st.session_state["selected_task_id"] = task["id"]
                    st.rerun()
            
            # Select task button
            if st.button("Abrir Detalhes", key=f"btn_task_{task['id']}"):
                st.session_state["selected_task_id"] = task["id"]
                st.rerun()
                
            st.divider()


# =============================================================
# Panel 3: Details (Right)
# =============================================================

def render_details_panel(db: TaskDatabase) -> None:
    """
    Render the right panel with the details of the selected task.
    """
    
    task_id = st.session_state.get("selected_task_id")
    
    if not task_id:
        st.info("👈 Selecione uma tarefa no centro.")
        return

    list_id = st.session_state.get("selected_list_id")
    tasks = db.get_tasks_by_list(list_id)
    task = next((t for t in tasks if t["id"] == task_id), None)
    
    if not task:
        st.error("Tarefa não encontrada.")
        return

    st.subheader("🔍 Detalhes")
    
    st.markdown(f"### {task['title']}")
    st.markdown(f"**Status:** {task['status']} | **Prioridade:** {task['priority']}")
    
    if task['description']:
        st.markdown("**Descrição:**")
        st.info(task['description'])
        
    col1, col2 = st.columns(2)
    with col1:
        st.caption(f"**Criado em:** {task['date_created'].strftime('%d/%m/%Y')}")
        st.caption(f"**Planejado:** {task['date_planned'].strftime('%d/%m/%Y') if task['date_planned'] else 'N/A'}")
    with col2:
        st.caption(f"**Origem:** {task['origin'] or 'N/A'}")
        
    st.divider()
    
    # Status Update
    st.markdown("**Atualizar Status:**")
    new_status = st.radio(
        "Mudar para:", 
        ["Backlog", "Fazendo", "Bloqueio", "Feito"], 
        index=["Backlog", "Fazendo", "Bloqueio", "Feito"].index(task['status']),
        horizontal=True,
        key=f"status_radio_{task_id}"
    )
    if new_status != task['status']:
        if st.button("Salvar Novo Status", key=f"btn_status_{task_id}"):
            db.update_task_status(task_id, new_status)
            st.rerun()

    st.divider()

    # Comments Section
    st.markdown("**Comentários:**")
    comments = db.get_comments_by_task(task_id)
    
    for c in comments:
        st.markdown(f"- {c['content']} *(em {c['created_at'].strftime('%d/%m/%Y %H:%M')})*")
        
    new_comment = st.text_area("Novo comentário", key=f"comment_{task_id}")
    if st.button("Adicionar Comentário", key=f"btn_comment_{task_id}"):
        if new_comment.strip():
            db.create_comment(task_id, new_comment)
            
            # Limpar o campo de comentário
            if f"comment_{task_id}" in st.session_state:
                del st.session_state[f"comment_{task_id}"]
                
            st.rerun()


# =============================================================
# Main
# =============================================================

def main() -> None:
    """
    Main entry point for the Streamlit app.
    """
    
    render_custom_css()
    
    # Instanciando o banco de dados a cada rerun.
    # O Neon (com connection pooling) gerencia isso de forma eficiente.
    db = TaskDatabase()
    
    render_sidebar(db)
    
    col_left, col_center, col_right = st.columns([1.5, 3, 2.5])
    
    with col_left:
        render_lists_panel(db)
        
    with col_center:
        render_tasks_panel(db)
        
    with col_right:
        render_details_panel(db)


if __name__ == "__main__":
    main()