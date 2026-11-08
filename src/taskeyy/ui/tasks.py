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
    
    # --- BARRA DE 3 BOTÕES ---
    col_order, col_filter, col_new, _ = st.columns([1, 1, 1,2])
    
    # Variável para guardar a ordenação escolhida
    order_by = "priority"

    with col_order:
        # Usando st.popover (ele se fecha automaticamente ao clicar fora)
        with st.popover("⬇️ Ordenar", use_container_width=True):
            st.markdown("**Ordenar por:**")
            order_by = st.radio(
                "Opções",
                options=["priority", "date_planned", "title", "date_created"],
                format_func=lambda x: {
                    "priority": "Prioridade",
                    "date_planned": "Data Planejada",
                    "title": "Título (A-Z)",
                    "date_created": "Mais Recentes"
                }[x],
                label_visibility="collapsed",
                key="radio_order" # Chave para manter o estado do radio
            )

    # Variáveis para os filtros
    filter_origin = []
    filter_priority = []
    filter_status = []

    with col_filter:
        with st.popover("🔍 Filtrar", use_container_width=True):
            st.markdown("**Filtrar por:**")
            # Precisamos pegar todas as tarefas para listar as origens disponíveis
            all_tasks = db.get_tasks_by_list(list_id, order_by="title")
            origens = sorted(list(set(t["origin"] for t in all_tasks if t["origin"])))
            prioridades = ["Crítico", "Alta", "Média", "Baixa"]
            status_opcoes = ["Backlog", "Fazendo", "Bloqueio", "Feito"]
            
            filter_origin = st.multiselect("Origem", origens, key="filter_origin")
            filter_priority = st.multiselect("Prioridade", prioridades, key="filter_priority")
            filter_status = st.multiselect("Status", status_opcoes, key="filter_status")

    with col_new:
        # O botão de nova tarefa abre o formulário (que fica embaixo do popover)
        with st.popover("➕ Nova", use_container_width=True):
            st.markdown("**Nova Tarefa**")
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
                    st.toast("Tarefa criada com sucesso!", icon="✅")
                    st.rerun()

    st.divider()

    # --- BUSCAR TAREFAS ---
    tasks = db.get_tasks_by_list(list_id, order_by)
    
    # --- APLICAR FILTROS ---
    if filter_origin:
        tasks = [t for t in tasks if t["origin"] in filter_origin]
    if filter_priority:
        tasks = [t for t in tasks if t["priority"] in filter_priority]
    if filter_status:
        tasks = [t for t in tasks if t["status"] in filter_status]

    # --- LISTA DE TAREFAS ---
    if not tasks:
        st.write("Nenhuma tarefa encontrada.")
        return

    for task in tasks:
        with st.container(border=True):
            col_text, col_btn = st.columns([0.85, 0.15])
            
            with col_text:
                display_title = task['title']
                if len(display_title) > 90:
                    display_title = display_title[:90] + "..."
                
                st.markdown(f"**{display_title}**")
                #st.caption(f"Status: {task['status']} | Origem: {task['origin'] or 'N/A'} | Prioridade: {task['priority']}")
                st.caption(f"{task['status']} | {task['origin'] or 'N/A'} | {task['priority']}")
                    
            with col_btn:
                if st.button("↗", key=f"btn_card_{task['id']}", help="Abrir Detalhes"):
                    st.session_state["selected_task_id"] = task["id"]
                    st.rerun()