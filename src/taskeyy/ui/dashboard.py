"""
Dashboard component for Taskeyy.
"""
import streamlit as st
import plotly.express as px
import pandas as pd
from taskeyy.database import TaskDatabase


def render_dashboard(db: TaskDatabase) -> None:
    """
    Render the strategic dashboard for management.
    """
    
    st.title("📊 Dashboard Estratégico")
    st.markdown("Visão geral do andamento dos projetos e tarefas.")
    
    # Buscar todos os dados (precisamos de uma função que traga tudo)
    # Como não temos get_all_tasks no DB, vamos adaptar a lógica:
    # Pegamos as listas e depois as tarefas de cada uma.
    lists = db.get_lists()
    all_tasks = []
    
    for lst in lists:
        tasks = db.get_tasks_by_list(lst["id"], order_by="date_created")
        for t in tasks:
            t["list_name"] = lst["name"] # Adiciona o nome da lista à tarefa
            all_tasks.append(t)
            
    if not all_tasks:
        st.info("Nenhuma tarefa no sistema ainda.")
        return

    df = pd.DataFrame(all_tasks)
    
    # --- MÉTRICAS GERAIS ---
    st.subheader("Resumo Geral")
    col1, col2, col3, col4 = st.columns(4)
    
    total = len(df)
    done = len(df[df["status"] == "Feito"])
    pending = total - done
    critical = len(df[(df["priority"] == "Crítico") & (df["status"] != "Feito")])
    
    col1.metric("Total de Tarefas", total)
    col2.metric("Concluídas", done)
    col3.metric("Pendentes", pending)
    col4.metric("Críticas Abertas", critical, delta_color="inverse")
    
    st.divider()

    # --- GRÁFICOS ---
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        # Gráfico 1: Distribuição por Status
        st.markdown("**Tarefas por Status**")
        status_counts = df["status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Quantidade"]
        
        fig_status = px.pie(
            status_counts, 
            names="Status", 
            values="Quantidade",
            color="Status",
            color_discrete_map={
                "Backlog": "#9E9E9E",
                "Fazendo": "#2196F3",
                "Bloqueio": "#F44336",
                "Feito": "#4CAF50"
            },
            hole=0.4
        )
        st.plotly_chart(fig_status, use_container_width=True)

    with col_chart2:
        # Gráfico 2: Volume de Tarefas Criadas vs Concluídas (Últimos 30 dias)
        st.markdown("**Criadas vs. Concluídas (Últimos 30 dias)**")
        
        # Converte as colunas de data para datetime
        df["date_created"] = pd.to_datetime(df["date_created"])
        df["date_real"] = pd.to_datetime(df["date_real"])
        
        # Filtra os últimos 30 dias (baseado na data de criação e data real)
        hoje = pd.Timestamp.now()
        trinta_dias_atras = hoje - pd.Timedelta(days=30)
        
        # Criadas
        df_created = df[df["date_created"] >= trinta_dias_atras].copy()
        df_created["date_only"] = df_created["date_created"].dt.date
        created_counts = df_created.groupby("date_only").size().reset_index(name="Quantidade")
        created_counts["Tipo"] = "Criadas"
        
        # Concluídas
        df_done = df[df["date_real"] >= trinta_dias_atras].copy()
        if not df_done.empty:
            df_done["date_only"] = df_done["date_real"].dt.date
            done_counts = df_done.groupby("date_only").size().reset_index(name="Quantidade")
            done_counts["Tipo"] = "Concluídas"
            
            # Junta as duas séries
            combined = pd.concat([created_counts, done_counts])
        else:
            combined = created_counts
            
        if not combined.empty:
            fig_daily = px.bar(
                combined,
                x="date_only",
                y="Quantidade",
                color="Tipo",
                barmode="group", # Coloca as barras lado a lado
                labels={"date_only": "Data", "Quantidade": "Tarefas", "Tipo": "Legenda"},
                color_discrete_map={
                    "Criadas": "#005B70",  # Teal
                    "Concluídas": "#F58220" # Laranja
                }
            )
            fig_daily.update_xaxes(tickformat="%d/%m")
            st.plotly_chart(fig_daily, use_container_width=True)
        else:
            st.info("Nenhuma atividade nos últimos 30 dias.")

    st.divider()
    
    # --- TABELA DE TAREFAS CRÍTICAS ---
    st.subheader("⚠️ Tarefas Críticas Abertas")
    critical_tasks = df[(df["priority"].isin(["Crítico", "Alta"])) & (df["status"] != "Feito")]
    
    if not critical_tasks.empty:
        st.dataframe(
            critical_tasks[["list_name", "title", "status", "priority", "date_planned"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "list_name": "Projeto",
                "title": "Título",
                "status": "Status",
                "priority": "Prioridade",
                "date_planned": "Planejado"
            }
        )
    else:
        st.success("Nenhuma tarefa crítica pendente. Excelente!")