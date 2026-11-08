"""
Lists panel component for Taskeyy.
"""
import streamlit as st
from taskeyy.database import TaskDatabase

def render_dashboard_stats(db: TaskDatabase) -> None:
    """
    Render the mini dashboard with task statistics.
    """
    stats = db.get_dashboard_stats()
    st.markdown("**Resumo:**")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Abertas", value=stats["total_open"])
    with col2:
        st.metric(label="Hoje", value=stats["today"])
        
    col3, col4 = st.columns(2)
    with col3:
        st.metric(label="Atrasadas", value=stats["overdue"], delta_color="inverse")
    with col4:
        st.metric(label="Semana", value=stats["week"])
        
    col5, col6 = st.columns(2)
    with col5:
        st.metric(label="Feitas Hoje", value=stats["done_today"])
    with col6:
        st.metric(label="Últ. 7 dias", value=stats["done_last_7_days"])
        
    st.divider()

def render_lists_panel(db: TaskDatabase) -> None:
    """
    Render the left panel with all lists.
    """
    st.subheader("📁 Listas")
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
            st.session_state["selected_task_id"] = None
            st.rerun()