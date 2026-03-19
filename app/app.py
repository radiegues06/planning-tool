import streamlit as st
import pandas as pd
import os
from data_models import *
from capacity_model import calculate_team_capacity, get_capacity_dict
from roadmap_engine import aggregate_by_epic, calculate_feature_durations, generate_roadmap, calculate_sprint_load, date_to_sprint
from charts import create_gantt_chart, create_unified_load_chart

# Page Config
st.set_page_config(page_title="Roadmap de Produto & Planejamento de Capacidade", layout="wide", page_icon="📊")

# CSS for better aesthetics
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 Roadmap de Produto & Planejamento de Capacidade")
st.markdown("Cálculo automático de capacidade, priorização de backlog e geração de roadmap.")

# --- Data Persistence Logic ---
DATA_FILE = "planning_data.xlsx"

def load_data():
    with pd.ExcelFile(DATA_FILE) as xls:
        team_df = pd.read_excel(xls, 'Team')
        vacations_df = pd.read_excel(xls, 'Vacations')
        sprints_df = pd.read_excel(xls, 'Sprints')
        milestones_df = pd.read_excel(xls, 'Milestones')
    
    backlog_df = pd.read_excel("Backlog_Roadmap_2026.xlsx", "Backlog")
        
    # Map Portuguese columns to internal references
    column_mapping = {
        "Features": COL_FEATURE_NAME,
        "Indicadores": COL_INDICATOR,
        "Épicos": COL_EPIC,
        "Esforço DE": COL_EFFORT_DE,
        "Esforço DS": COL_EFFORT_DS,
        "Esforço FE": COL_EFFORT_FE,
        "Esforço PO": COL_EFFORT_PO,
        "Score": COL_SCORE,
        "Priorização": COL_PRIORITY
    }
    backlog_df = backlog_df.rename(columns=column_mapping)
    
    if COL_FEATURE_ID not in backlog_df.columns and not backlog_df.empty:
        backlog_df[COL_FEATURE_ID] = [f"F{i}" for i in range(1, len(backlog_df)+1)]

    # Fill NaN and fix types to avoid Streamlit errors
    if COL_EPIC in backlog_df.columns:
        backlog_df[COL_EPIC] = backlog_df[COL_EPIC].fillna("").astype(str)
    if COL_INDICATOR in backlog_df.columns:
        backlog_df[COL_INDICATOR] = backlog_df[COL_INDICATOR].fillna(INDICATORS[0]).astype(str).str.strip()
    if COL_PRIORITY not in backlog_df.columns:
        backlog_df[COL_PRIORITY] = 1
    if COL_MANUAL_START not in backlog_df.columns:
        backlog_df[COL_MANUAL_START] = None
    
    # Fill effort nan
    effort_cols_to_fill = [COL_EFFORT_DE, COL_EFFORT_DS, COL_EFFORT_FE, COL_EFFORT_PO]
    for c in effort_cols_to_fill:
        if c in backlog_df.columns:
            backlog_df[c] = backlog_df[c].fillna(0).astype('float64')
    
    # Vacations column types
    vacations_df[COL_VAC_PERSON] = vacations_df[COL_VAC_PERSON].fillna("").astype(str)
    
    # Milestones types
    milestones_df[COL_MS_INDICATOR] = milestones_df[COL_MS_INDICATOR].fillna("").astype(str).str.strip()
    milestones_df[COL_MS_TARGET] = milestones_df[COL_MS_TARGET].fillna("").astype(str)
    
    return team_df, backlog_df, vacations_df, sprints_df, milestones_df

if 'team_df' not in st.session_state:
    t_df, b_df, v_df, s_df, m_df = load_data()
    st.session_state.team_df = t_df
    st.session_state.backlog_df = b_df
    st.session_state.vacations_df = v_df
    st.session_state.sprints_df = s_df
    st.session_state.milestones_df = m_df

# --- Calculation Logic (sprint length derived from calendar) ---
capacity_per_sprint = calculate_team_capacity(st.session_state.team_df, st.session_state.vacations_df, st.session_state.sprints_df)
capacity_dict_s1 = get_capacity_dict(capacity_per_sprint)

# --- Roadmap & Capacity ---
roadmap_container = st.container()

# Calculate Scores and Durations
backlog_df = st.session_state.backlog_df

if not backlog_df.empty:
    # Calculate Total Effort
    effort_cols = [COL_EFFORT_DE, COL_EFFORT_DS, COL_EFFORT_FE, COL_EFFORT_PO]
    backlog_df[COL_TOTAL_EFFORT] = backlog_df[effort_cols].sum(axis=1).replace(0, 1)
    
    # Aggregate by Epic for scheduling
    epic_backlog = aggregate_by_epic(backlog_df)
    
    # Recalculate effort on aggregated data
    epic_backlog[COL_TOTAL_EFFORT] = epic_backlog[effort_cols].sum(axis=1).replace(0, 1)
    
    # Calculate Durations
    epic_with_duration = calculate_feature_durations(epic_backlog, capacity_per_sprint)
    
    # Build Roadmap (at Epic level)
    roadmap_df = generate_roadmap(epic_with_duration, capacity_per_sprint)
    
    # Render Roadmap into top container
    with roadmap_container:
        st.subheader("Roadmap Automático")
        if not roadmap_df.empty:
            # # Add filters for Roadmap
            # r_col1, r_col2 = st.columns(2)
            # with r_col1:
            #     r_ind_filter = st.multiselect("Filtrar Indicador do Roadmap", roadmap_df[COL_INDICATOR].unique(), default=roadmap_df[COL_INDICATOR].unique(), key="roadmap_ind_filter")
            # with r_col2:
            #     st.write("") # Vertical alignment
            #     st.write("") # Vertical alignment
            #     show_capacity_alerts = st.toggle("Exibir Alertas de Capacidade", value=False, key="roadmap_capacity_toggle")
            
            # filtered_roadmap_df = roadmap_df[roadmap_df[COL_INDICATOR].isin(r_ind_filter)]

            filtered_roadmap_df = roadmap_df.copy()
            
            if not filtered_roadmap_df.empty:
                # Calculate sprint load for capacity overlay
                sprint_load_df = calculate_sprint_load(roadmap_df, roadmap_df)
                
                gantt = create_gantt_chart(filtered_roadmap_df, sprint_load_df, capacity_per_sprint, st.session_state.sprints_df, milestones_df=st.session_state.milestones_df, show_alerts=False)
                if gantt:
                    st.plotly_chart(gantt, use_container_width=True)
            
            st.divider()
            
            # Capacity vs Demand chart
            st.subheader("Capacidade vs Demanda")
            sprint_load_df_cap = calculate_sprint_load(roadmap_df, roadmap_df)
            fig = create_unified_load_chart(sprint_load_df_cap, capacity_per_sprint, COMPETENCIES, st.session_state.sprints_df)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
