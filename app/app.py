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

col_title, col_save = st.columns([4, 1])
with col_title:
    st.title("🚀 Roadmap de Produto & Planejamento de Capacidade")
    st.markdown("Cálculo automático de capacidade, priorização de backlog e geração de roadmap.")

# --- Data Persistence Logic ---
DATA_FILE = "planning_data.xlsx"

def load_data():
    if os.path.exists(DATA_FILE):
        with pd.ExcelFile(DATA_FILE) as xls:
            team_df = pd.read_excel(xls, 'Team')
            backlog_df = pd.read_excel(xls, 'Backlog')
            vacations_df = pd.read_excel(xls, 'Vacations')
            sprints_df = pd.read_excel(xls, 'Sprints')
            milestones_df = pd.read_excel(xls, 'Milestones')
            
        # Fill NaN and fix types to avoid Streamlit errors
        backlog_df[COL_EPIC] = backlog_df[COL_EPIC].fillna("").astype(str)
        backlog_df[COL_INDICATOR] = backlog_df[COL_INDICATOR].fillna(INDICATORS[0]).astype(str).str.strip()
        if COL_PRIORITY not in backlog_df.columns:
            backlog_df[COL_PRIORITY] = 1
        if COL_MANUAL_START not in backlog_df.columns:
            backlog_df[COL_MANUAL_START] = None
        
        # Vacations column types
        vacations_df[COL_VAC_PERSON] = vacations_df[COL_VAC_PERSON].fillna("").astype(str)
        
        # Milestones types
        milestones_df[COL_MS_INDICATOR] = milestones_df[COL_MS_INDICATOR].fillna("").astype(str).str.strip()
        milestones_df[COL_MS_TARGET] = milestones_df[COL_MS_TARGET].fillna("").astype(str)
        
        return team_df, backlog_df, vacations_df, sprints_df, milestones_df
    else:
        # Fallback to defaults
        team_df = pd.DataFrame(columns=[COL_PERSON, COL_COMPETENCY, COL_WEEKLY_HOURS, COL_ALLOCATION_PCT])
        backlog_df = pd.DataFrame(columns=[COL_FEATURE_ID, COL_FEATURE_NAME, COL_PRIORITY, COL_INDICATOR, COL_EPIC, COL_BUSINESS_VALUE, COL_EFFORT_DE, COL_EFFORT_DS, COL_EFFORT_FE, COL_EFFORT_PO, COL_MANUAL_START])
        vacations_df = pd.DataFrame(columns=[COL_VAC_PERSON, COL_VAC_START_DATE, COL_VAC_END_DATE])
        sprints_df = pd.DataFrame(columns=[COL_SPR_NUMBER, COL_SPR_START_DATE, COL_SPR_END_DATE])
        milestones_df = pd.DataFrame(columns=[COL_MS_INDICATOR, COL_MS_DATE, COL_MS_TARGET])
        return team_df, backlog_df, vacations_df, sprints_df, milestones_df

def save_data(team_df, backlog_df, vacations_df, sprints_df, milestones_df):
    with pd.ExcelWriter(DATA_FILE, engine='openpyxl') as writer:
        team_df.to_excel(writer, sheet_name='Team', index=False)
        backlog_df.to_excel(writer, sheet_name='Backlog', index=False)
        vacations_df.to_excel(writer, sheet_name='Vacations', index=False)
        sprints_df.to_excel(writer, sheet_name='Sprints', index=False)
        milestones_df.to_excel(writer, sheet_name='Milestones', index=False)

if 'team_df' not in st.session_state:
    t_df, b_df, v_df, s_df, m_df = load_data()
    st.session_state.team_df = t_df
    st.session_state.backlog_df = b_df
    st.session_state.vacations_df = v_df
    st.session_state.sprints_df = s_df
    st.session_state.milestones_df = m_df

# --- Main Tabs ---
tab1, tab2, tab3 = st.tabs(["📋 Roadmap & Capacidade", "📦 Backlog do Produto", "⚙️ Equipe & Configuração"])

with tab3:
    st.header("⚙️ Configuração")
    
    st.header("👥 Composição da Equipe")
    
    edited_team_df = st.session_state.team_df
    
    # Filter for Team
    comp_options = COMPETENCIES
    comp_filter = st.multiselect("Filtrar por Competência", comp_options, default=comp_options, key="team_comp_filter")
    team_mask = st.session_state.team_df[COL_COMPETENCY].isin(comp_filter) | st.session_state.team_df[COL_COMPETENCY].isna()
    filtered_team = st.session_state.team_df[team_mask]
    
    edited_filtered_team = st.data_editor(
        filtered_team,
        num_rows="dynamic",
        column_config={
            COL_PERSON: st.column_config.TextColumn("Pessoa"),
            COL_COMPETENCY: st.column_config.SelectboxColumn("Competência", options=COMPETENCIES),
            COL_WEEKLY_HOURS: st.column_config.NumberColumn("Horas/Semana"),
            COL_ALLOCATION_PCT: st.column_config.NumberColumn("Alocação %", min_value=0, max_value=100, step=5)
        },
        use_container_width=True,
        key="team_editor"
    )
    
    # Merge back changes
    deleted = filtered_team.index.difference(edited_filtered_team.index)
    st.session_state.team_df = st.session_state.team_df.drop(deleted, errors='ignore')
    for idx in edited_filtered_team.index:
        st.session_state.team_df.loc[idx] = edited_filtered_team.loc[idx]
    
    edited_team_df = st.session_state.team_df

    st.divider()
    col_v, col_s = st.columns(2)
    with col_v:
        st.header("🏖️ Férias")
        
        # Filter for Vacations
        person_options = edited_team_df[COL_PERSON].unique().tolist() if not edited_team_df.empty else []
        vac_person_filter = st.multiselect("Filtrar por Pessoa", person_options, default=person_options, key="vac_person_filter")
        vac_mask = st.session_state.vacations_df[COL_VAC_PERSON].isin(vac_person_filter) | st.session_state.vacations_df[COL_VAC_PERSON].isna()
        filtered_vacs = st.session_state.vacations_df[vac_mask]
        
        edited_filtered_vacs = st.data_editor(
            filtered_vacs,
            num_rows="dynamic",
            column_config={
                COL_VAC_PERSON: st.column_config.SelectboxColumn("Pessoa", options=person_options),
                COL_VAC_START_DATE: st.column_config.DateColumn("Data Início", format="YYYY-MM-DD"),
                COL_VAC_END_DATE: st.column_config.DateColumn("Data Fim", format="YYYY-MM-DD")
            },
            use_container_width=True,
            key="vacations_editor"
        )
        # Merge back
        vac_deleted = filtered_vacs.index.difference(edited_filtered_vacs.index)
        st.session_state.vacations_df = st.session_state.vacations_df.drop(vac_deleted, errors='ignore')
        for idx in edited_filtered_vacs.index:
            st.session_state.vacations_df.loc[idx] = edited_filtered_vacs.loc[idx]
            
        edited_vacations_df = st.session_state.vacations_df

    with col_s:
        st.header("🗓️ Calendário de Sprints")
        edited_sprints_df = st.data_editor(
            st.session_state.sprints_df,
            num_rows="dynamic",
            column_config={
                COL_SPR_NUMBER: st.column_config.NumberColumn("Sprint"),
                COL_SPR_START_DATE: st.column_config.DateColumn("Data Início", format="YYYY-MM-DD"),
                COL_SPR_END_DATE: st.column_config.DateColumn("Data Fim", format="YYYY-MM-DD")
            },
            use_container_width=True,
            key="sprints_editor"
        )
    
    st.divider()
    st.header("🎯 Milestones")
    edited_milestones_df = st.data_editor(
        st.session_state.milestones_df,
        num_rows="dynamic",
        column_config={
            COL_MS_INDICATOR: st.column_config.SelectboxColumn("Indicador", options=INDICATORS),
            COL_MS_DATE: st.column_config.DateColumn("Data", format="YYYY-MM-DD"),
            COL_MS_TARGET: st.column_config.TextColumn("Meta"),
        },
        use_container_width=True,
        key="milestones_editor"
    )
    st.session_state.milestones_df = edited_milestones_df

# --- Calculation Logic (sprint length derived from calendar) ---
capacity_per_sprint = calculate_team_capacity(edited_team_df, edited_vacations_df, edited_sprints_df)
capacity_dict_s1 = get_capacity_dict(capacity_per_sprint)

# --- Tab 1: Roadmap & Capacity ---
with tab1:
    roadmap_container = st.container()
    
    # Calculate Scores and Durations
    edited_backlog_df = st.session_state.backlog_df
    
    if not edited_backlog_df.empty:
        # Calculate Total Effort
        effort_cols = [COL_EFFORT_DE, COL_EFFORT_DS, COL_EFFORT_FE, COL_EFFORT_PO]
        edited_backlog_df[COL_TOTAL_EFFORT] = edited_backlog_df[effort_cols].sum(axis=1).replace(0, 1)
        # Factor priority into score
        edited_backlog_df[COL_SCORE] = (edited_backlog_df[COL_BUSINESS_VALUE] / edited_backlog_df[COL_TOTAL_EFFORT]) * (1 / edited_backlog_df[COL_PRIORITY])
        
        # Aggregate by Epic for scheduling
        epic_backlog = aggregate_by_epic(edited_backlog_df)
        
        # Recalculate scores on aggregated data
        epic_backlog[COL_TOTAL_EFFORT] = epic_backlog[effort_cols].sum(axis=1).replace(0, 1)
        epic_backlog[COL_SCORE] = (epic_backlog[COL_BUSINESS_VALUE] / epic_backlog[COL_TOTAL_EFFORT]) * (1 / epic_backlog[COL_PRIORITY])
        
        # Calculate Durations
        epic_with_duration = calculate_feature_durations(epic_backlog, capacity_per_sprint)
        
        # Build Roadmap (at Epic level)
        roadmap_df = generate_roadmap(epic_with_duration, capacity_per_sprint)
        
        # Render Roadmap into top container
        with roadmap_container:
            st.subheader("Roadmap Automático")
            if not roadmap_df.empty:
                # Add filters for Roadmap
                r_col1, r_col2 = st.columns(2)
                with r_col1:
                    r_ind_filter = st.multiselect("Filtrar Indicador do Roadmap", roadmap_df[COL_INDICATOR].unique(), default=roadmap_df[COL_INDICATOR].unique(), key="roadmap_ind_filter")
                with r_col2:
                    st.write("") # Vertical alignment
                    st.write("") # Vertical alignment
                    show_capacity_alerts = st.toggle("Exibir Alertas de Capacidade", value=False, key="roadmap_capacity_toggle")
                
                filtered_roadmap_df = roadmap_df[roadmap_df[COL_INDICATOR].isin(r_ind_filter)]
                
                if not filtered_roadmap_df.empty:
                    # Calculate sprint load for capacity overlay
                    sprint_load_df = calculate_sprint_load(roadmap_df, roadmap_df)
                    
                    gantt = create_gantt_chart(filtered_roadmap_df, sprint_load_df, capacity_per_sprint, edited_sprints_df, milestones_df=st.session_state.milestones_df, show_alerts=show_capacity_alerts)
                    if gantt:
                        st.plotly_chart(gantt, use_container_width=True)
                
                st.divider()
                
                # Capacity vs Demand chart
                st.subheader("Capacidade vs Demanda")
                sprint_load_df_cap = calculate_sprint_load(roadmap_df, roadmap_df)
                fig = create_unified_load_chart(sprint_load_df_cap, capacity_per_sprint, COMPETENCIES, edited_sprints_df)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)

# --- Tab 2: Product Backlog ---
with tab2:
    st.subheader("Backlog do Produto")
    
    # Filters
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        ind_options = INDICATORS
        ind_filter = st.multiselect("Filtrar por Indicador", ind_options, default=ind_options, key="backlog_ind_filter")
    with f_col2:
        epic_options = [e for e in st.session_state.backlog_df[COL_EPIC].unique() if e] + [""]
        epic_filter = st.multiselect("Filtrar por Épico", epic_options, default=epic_options, key="backlog_epic_filter")
        
    b_mask = (st.session_state.backlog_df[COL_INDICATOR].isin(ind_filter)) & (st.session_state.backlog_df[COL_EPIC].isin(epic_filter))
    filtered_backlog = st.session_state.backlog_df[b_mask]
    
    edited_filtered_backlog = st.data_editor(
        filtered_backlog,
        num_rows="dynamic",
        column_config={
            COL_FEATURE_ID: st.column_config.TextColumn("ID"),
            COL_FEATURE_NAME: st.column_config.TextColumn("Nome da Feature"),
            COL_PRIORITY: st.column_config.NumberColumn("Prioridade", min_value=1, step=1),
            COL_INDICATOR: st.column_config.SelectboxColumn("Indicador", options=INDICATORS),
            COL_EPIC: st.column_config.TextColumn("Épico"),
            COL_BUSINESS_VALUE: st.column_config.NumberColumn("Valor"),
            COL_EFFORT_DE: st.column_config.NumberColumn("Esforço DE"),
            COL_EFFORT_DS: st.column_config.NumberColumn("Esforço DS"),
            COL_EFFORT_FE: st.column_config.NumberColumn("Esforço FE"),
            COL_EFFORT_PO: st.column_config.NumberColumn("Esforço PO"),
            COL_MANUAL_START: st.column_config.NumberColumn("Sprint Início Manual", min_value=1, step=1, help="Deixe vazio para agendamento automático"),
        },
        use_container_width=True,
        key="backlog_editor"
    )
    
    # Merge back
    b_deleted = filtered_backlog.index.difference(edited_filtered_backlog.index)
    st.session_state.backlog_df = st.session_state.backlog_df.drop(b_deleted, errors='ignore')
    for idx in edited_filtered_backlog.index:
        st.session_state.backlog_df.loc[idx] = edited_filtered_backlog.loc[idx]

# --- Final Actions ---
with col_save:
    st.write("") # Spacing 
    st.write("") # Spacing
    if st.button("💾 Salvar Alterações", use_container_width=True, type="primary"):
        save_data(edited_team_df, st.session_state.backlog_df, edited_vacations_df, edited_sprints_df, st.session_state.milestones_df)
        st.success("✅ Salvo!")
