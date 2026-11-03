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

def render_dashboard_stats(db: TaskDatabase) -> None:
    """
    Render the mini dashboard with task statistics.
    """
    
    stats = db.get_dashboard_stats()
    
    st.markdown("**Resumo:**")
    
    # Linha 1: Abertas e Hoje
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Abertas", value=stats["total_open"])
    with col2:
        st.metric(label="Hoje", value=stats["today"])
        
    # Linha 2: Atrasadas e Semana
    col3, col4 = st.columns(2)
    with col3:
        st.metric(label="Atrasadas", value=stats["overdue"], delta_color="inverse")
    with col4:
        st.metric(label="Semana", value=stats["week"])
        
    # Linha 3: Feitas Hoje e Últ. 7 dias
    col5, col6 = st.columns(2)
    with col5:
        st.metric(label="Feitas Hoje", value=stats["done_today"])
    with col6:
        st.metric(label="Últ. 7 dias", value=stats["done_last_7_days"])
        
    st.divider()

# =============================================================
# Panel 1: Lists (Left)
# =============================================================

def render_lists_panel(db: TaskDatabase) -> None:
    """
    Render the left panel with all lists.
    """
    
    st.subheader("📁 Listas")

    # --- NOVO: Renderiza as estatísticas ---
    render_dashboard_stats(db)
    
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
    
    st.subheader(f"📋 {list_name}")
    
    # --- BARRA DE FILTROS ---
    tasks = db.get_tasks_by_list(list_id)
    
    if tasks:
        col_f1, col_f2, col_f3 = st.columns(3)
        
        origens = sorted(list(set(t["origin"] for t in tasks if t["origin"])))
        prioridades = ["Crítico", "Alta", "Média", "Baixa"]
        status_opcoes = ["Backlog", "Fazendo", "Bloqueio", "Feito"]
        
        with col_f1:
            filter_origin = st.multiselect("Origem", origens, key="filter_origin")
        with col_f2:
            filter_priority = st.multiselect("Prioridade", prioridades, key="filter_priority")
        with col_f3:
            filter_status = st.multiselect("Status", status_opcoes, key="filter_status")
            
        if filter_origin:
            tasks = [t for t in tasks if t["origin"] in filter_origin]
        if filter_priority:
            tasks = [t for t in tasks if t["priority"] in filter_priority]
        if filter_status:
            tasks = [t for t in tasks if t["status"] in filter_status]

    # --- FORMULÁRIO DE NOVA TAREFA ---
    if "expand_task_form" not in st.session_state:
        st.session_state["expand_task_form"] = False

    with st.expander("➕ Nova Tarefa", expanded=st.session_state["expand_task_form"]):
        with st.form(key="form_new_task", clear_on_submit=True):
            title = st.text_input("Título")
            desc = st.text_area("Descrição")
            
            col1, col2 = st.columns(2)
            with col1:
                priority = st.selectbox("Prioridade", ["Baixa", "Média", "Alta", "Crítico"])
                status = st.selectbox("Status", ["Backlog", "Fazendo", "Bloqueio", "Feito"])
            with col2:
                origin = st.text_input("Origem (ex: Projeto X)")
                date_planned = st.date_input("Data Planejada", value=None)
                
            submitted = st.form_submit_button("Salvar Tarefa", type="primary")
            
            if submitted:
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
                    
                    st.session_state["expand_task_form"] = False
                    st.toast("Tarefa criada com sucesso!", icon="✅")
                    st.rerun()
                else:
                    st.warning("O título é obrigatório.")

    st.divider()

    # --- LISTA DE TAREFAS (CARTÃO CLICÁVEL) ---
    if not tasks:
        st.write("Nenhuma tarefa encontrada.")
        return

    for task in tasks:
        # Criamos um container com borda para simular o cartão
        with st.container(border=True):
            # Renderizamos o conteúdo do cartão
            st.markdown(f"**{task['title']}**")
            st.caption(f"Status: {task['status']} | Origem: {task['origin'] or 'N/A'} | Prioridade: {task['priority']}")
            
            # Botão invisível que ocupa o cartão todo.
            # Usamos uma chave única para cada tarefa.
            if st.button(
                "Abrir", 
                key=f"btn_card_{task['id']}", 
                use_container_width=True,
                type="secondary" # deixa o botão mais neutro
            ):
                st.session_state["selected_task_id"] = task["id"]
                st.rerun()

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
    
    # Controle do estado de edição
    edit_key = f"edit_mode_{task_id}"
    if edit_key not in st.session_state:
        st.session_state[edit_key] = False

    # --- MODO DE EDIÇÃO ---
    if st.session_state[edit_key]:
        st.markdown(f"### ✏️ Editando: {task['title']}")
        
        with st.form(key=f"form_edit_{task_id}"):
            edit_title = st.text_input("Título", value=task['title'])
            edit_desc = st.text_area("Descrição", value=task['description'] or "")
            
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                edit_priority = st.selectbox(
                    "Prioridade", 
                    ["Baixa", "Média", "Alta", "Crítico"], 
                    index=["Baixa", "Média", "Alta", "Crítico"].index(task['priority'])
                )
            with col_e2:
                edit_origin = st.text_input("Origem", value=task['origin'] or "")
                
            edit_date = st.date_input(
                "Data Planejada", 
                value=task['date_planned'] if task['date_planned'] else None
            )
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.form_submit_button("Salvar", type="primary", use_container_width=True):
                    date_str = edit_date.strftime("%Y-%m-%d") if edit_date else None
                    db.update_task_details(
                        task_id=task_id,
                        title=edit_title,
                        description=edit_desc,
                        priority=edit_priority,
                        status=task['status'],
                        origin=edit_origin,
                        date_planned=date_str
                    )
                    st.session_state[edit_key] = False
                    st.toast("Tarefa atualizada!", icon="✅")
                    st.rerun()
            with col_btn2:
                if st.form_submit_button("Cancelar", use_container_width=True):
                    st.session_state[edit_key] = False
                    st.rerun()
        
    # --- MODO DE VISUALIZAÇÃO ---
    else:
        col_title, col_btn = st.columns([3, 1])
        with col_title:
            st.markdown(f"### {task['title']}")
        with col_btn:
            if st.button("✏️ Editar", use_container_width=True):
                st.session_state[edit_key] = True
                st.rerun()

        st.markdown(f"**Status:** {task['status']} | **Prioridade:** {task['priority']}")
        
        if task['description']:
            st.markdown("**Descrição:**")
            st.info(task['description'])
            
        col1, col2 = st.columns(2)
        with col1:
            st.caption(f"**Criado em:** {task['date_created'].strftime('%d/%m/%Y')}")
            st.caption(f"**Planejado:** {task['date_planned'].strftime('%d/%m/%Y') if task['date_planned'] else 'N/A'}")
            if task['date_real']:
                st.caption(f"**Concluído em:** {task['date_real'].strftime('%d/%m/%Y %H:%M')}")
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

        # --- Deletar Tarefa ---
        st.markdown("**Zona de Perigo:**")
        if st.button("🗑️ Deletar Tarefa", type="secondary", use_container_width=True):
            db.delete_task(task_id)
            st.session_state["selected_task_id"] = None
            st.toast("Tarefa deletada.", icon="🗑️")
            st.rerun()

    st.divider()

    # Comments Section (Sempre visível)
    st.markdown("**Comentários:**")
    comments = db.get_comments_by_task(task_id)
    
    for c in comments:
        st.markdown(f"- {c['content']} *(em {c['created_at'].strftime('%d/%m/%Y %H:%M')})*")
        
    new_comment = st.text_area("Novo comentário", key=f"comment_{task_id}")
    if st.button("Adicionar Comentário", key=f"btn_comment_{task_id}"):
        if new_comment.strip():
            db.create_comment(task_id, new_comment)
            
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
    
    db = TaskDatabase()
    
    render_sidebar(db)
    
    #col_left, col_center, col_right = st.columns([1.5, 3, 2.5])
    col_left, col_center, col_right = st.columns([1, 2, 4])
    
    with col_left:
        render_lists_panel(db)
        
    with col_center:
        render_tasks_panel(db)
        
    with col_right:
        render_details_panel(db)


if __name__ == "__main__":
    main()