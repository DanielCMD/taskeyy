"""
Details panel component for Taskeyy.
"""
import streamlit as st
from taskeyy.database import TaskDatabase

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
    
    edit_key = f"edit_mode_{task_id}"
    if edit_key not in st.session_state:
        st.session_state[edit_key] = False

    # --- MODO DE EDIÇÃO ---
    if st.session_state[edit_key]:
        st.markdown(f"### ✏️ Editando")
        with st.form(key=f"form_edit_{task_id}"):
            edit_title = st.text_input("Título", value=task['title'])
            edit_desc = st.text_area("Descrição", value=task['description'] or "")
            
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                edit_priority = st.selectbox("Prioridade", ["Baixa", "Média", "Alta", "Crítico"], index=["Baixa", "Média", "Alta", "Crítico"].index(task['priority']))
            with col_e2:
                edit_origin = st.text_input("Origem", value=task['origin'] or "")
                
            edit_date = st.date_input("Data Planejada", value=task['date_planned'] if task['date_planned'] else None)
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.form_submit_button("Salvar", type="primary", use_container_width=True):
                    date_str = edit_date.strftime("%Y-%m-%d") if edit_date else None
                    db.update_task_details(task_id, edit_title, edit_desc, edit_priority, task['status'], edit_origin, date_str)
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

        st.markdown("**Zona de Perigo:**")
        if st.button("🗑️ Deletar Tarefa", type="secondary", use_container_width=True):
            db.delete_task(task_id)
            st.session_state["selected_task_id"] = None
            st.toast("Tarefa deletada.", icon="🗑️")
            st.rerun()

    st.divider()

    # Comments
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