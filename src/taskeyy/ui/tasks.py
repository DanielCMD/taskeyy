"""
Tasks panel component for Taskeyy.
"""
import streamlit as st
from taskeyy.database import TaskDatabase

def render_tasks_panel(db: TaskDatabase) -> None:
    """
    Render the center panel with tasks from the selected list.
    """
    list_id = st.session_state.get("selected_list_id")
    if not list_id:
        st.info("👈 Selecione uma lista na esquerda.")
        return

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
            
            if submitted and title.strip():
                date_str = date_planned.strftime("%Y-%m-%d") if date_planned else None
                db.create_task(list_id, title, desc, status, priority, origin, date_planned=date_str)
                st.session_state["expand_task_form"] = False
                st.toast("Tarefa criada com sucesso!", icon="✅")
                st.rerun()

    st.divider()

    # --- LISTA DE TAREFAS ---
    if not tasks:
        st.write("Nenhuma tarefa encontrada.")
        return

    for task in tasks:
        with st.container(border=True):
            st.markdown(f"**{task['title']}**")
            st.caption(f"Status: {task['status']} | Origem: {task['origin'] or 'N/A'} | Prioridade: {task['priority']}")
            
            if st.button("Abrir", key=f"btn_card_{task['id']}", use_container_width=True):
                st.session_state["selected_task_id"] = task["id"]
                st.rerun()