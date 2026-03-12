import pandas as pd
import numpy as np
from data_models import *
import copy

def aggregate_by_epic(backlog_df):
    """
    Aggregates features by Epic for Epic-level scheduling.
    - Features sharing the same Epic are merged: efforts summed, business_value summed, max priority taken.
    - Features with empty/no Epic are kept as individual entries.
    - The Indicator is taken from the first feature in the group.
    """
    if backlog_df.empty:
        return backlog_df
    
    df = backlog_df.copy()
    
    # Ensure epic column exists and fill blanks
    if COL_EPIC not in df.columns:
        df[COL_EPIC] = ""
    df[COL_EPIC] = df[COL_EPIC].fillna("").astype(str).str.strip()
    
    # Split: features with an epic vs without
    has_epic = df[df[COL_EPIC] != ""]
    no_epic = df[df[COL_EPIC] == ""]
    
    epic_rows = []
    if not has_epic.empty:
        for (indicator, epic), group in has_epic.groupby([COL_INDICATOR, COL_EPIC]):
            row = {
                COL_FEATURE_ID: f"EPIC-{epic}",
                COL_FEATURE_NAME: epic,
                COL_PRIORITY: int(group[COL_PRIORITY].min()),
                COL_INDICATOR: indicator,
                COL_EPIC: epic,
                COL_BUSINESS_VALUE: group[COL_BUSINESS_VALUE].sum(),
            }
            for eff_col in [COL_EFFORT_DE, COL_EFFORT_DS, COL_EFFORT_FE, COL_EFFORT_PO]:
                row[eff_col] = group[eff_col].fillna(0).sum()
            
            # Take manual start if any feature in the group has one
            if COL_MANUAL_START in group.columns:
                manual_starts = group[COL_MANUAL_START].dropna()
                row[COL_MANUAL_START] = manual_starts.min() if not manual_starts.empty else None
            else:
                row[COL_MANUAL_START] = None
            
            epic_rows.append(row)
    
    epic_df = pd.DataFrame(epic_rows) if epic_rows else pd.DataFrame()
    
    # For no-epic features, use feature_name as the display name
    if not no_epic.empty:
        no_epic = no_epic.copy()
    
    # Combine
    result = pd.concat([epic_df, no_epic], ignore_index=True) if not epic_df.empty else no_epic.copy()
    
    return result

def calculate_feature_durations(backlog_df, capacity_per_sprint):
    """
    Calculates a nominal number of sprints each feature requires.
    Uses Sprint 1 capacity as a baseline estimate.
    Real duration is calculated in generate_roadmap during parallel sequencing.
    """
    if backlog_df.empty:
        return backlog_df

    cap_s1 = capacity_per_sprint.get(1, {comp: 1 for comp in COMPETENCIES})
    
    def get_nominal_sprints(row):
        sprints_needed = []
        for comp, effort_col in EFFORT_COLS.items():
            effort = row[effort_col]
            capacity = cap_s1.get(comp, 0)
            if effort > 0:
                if capacity > 0:
                    sprints_needed.append(effort / capacity)
                else:
                    sprints_needed.append(float('inf'))
        if not sprints_needed: return 0
        return int(np.ceil(max(sprints_needed)))

    backlog_df[COL_SPRINTS_REQUIRED] = backlog_df.apply(get_nominal_sprints, axis=1)
    return backlog_df

def _find_earliest_start(remaining_capacity, efforts, max_sprint=100):
    """
    Find the earliest sprint where at least some capacity exists
    for all required competencies of a feature.
    """
    for s in range(1, max_sprint + 1):
        cap = remaining_capacity.get(s, {})
        can_start = True
        for comp in efforts:
            if cap.get(comp, 0) <= 0:
                can_start = False
                break
        if can_start:
            return s
    return 1  # fallback

def _simulate_feature(remaining_capacity, efforts, start_sprint, max_sprint=100):
    """
    Simulate consuming effort from remaining_capacity starting at start_sprint.
    Returns end_sprint and mutates remaining_capacity in place.
    """
    remaining = {comp: effort for comp, effort in efforts.items()}
    sim_sprint = start_sprint
    
    while any(v > 0 for v in remaining.values()) and sim_sprint <= max_sprint:
        cap_this = remaining_capacity.get(sim_sprint, {})
        
        for comp in list(remaining.keys()):
            if remaining[comp] <= 0:
                continue
            available = cap_this.get(comp, 0)
            if available > 0:
                consumed = min(available, remaining[comp])
                remaining[comp] -= consumed
                cap_this[comp] = available - consumed
        
        if any(v > 0 for v in remaining.values()):
            sim_sprint += 1
    
    return sim_sprint

def generate_roadmap(backlog_df, capacity_per_sprint):
    """
    Parallel scheduling algorithm with shared capacity tracking.
    
    Features can run in parallel as long as combined demand does not
    exceed capacity. DS-heavy features are prioritized via secondary sort.
    Manual start sprint overrides are respected.
    """
    if backlog_df.empty:
        return pd.DataFrame()

    # Deep copy capacity so we can track remaining availability
    remaining_capacity = copy.deepcopy(capacity_per_sprint)
    
    # Sort: primary by score descending, secondary by DS effort descending (DS maximization)
    roadmap_df = backlog_df.copy()
    roadmap_df['_has_ds'] = roadmap_df[COL_EFFORT_DS].fillna(0).apply(lambda x: 1 if x > 0 else 0)
    roadmap_df = roadmap_df.sort_values(
        by=[COL_SCORE, '_has_ds', COL_EFFORT_DS], 
        ascending=[False, False, False]
    )
    
    start_sprints = []
    end_sprints = []
    
    for _, row in roadmap_df.iterrows():
        # Build effort dict for this feature
        efforts = {}
        for comp, eff_col in EFFORT_COLS.items():
            val = row[eff_col]
            if val > 0:
                efforts[comp] = val
        
        if not efforts:
            start_sprints.append(1)
            end_sprints.append(1)
            continue
        
        # Determine start sprint
        manual_start = row.get(COL_MANUAL_START, None)
        if pd.notna(manual_start) and manual_start and int(manual_start) >= 1:
            start_sprint = int(manual_start)
        else:
            start_sprint = _find_earliest_start(remaining_capacity, efforts)
        
        # Simulate effort consumption
        end_sprint = _simulate_feature(remaining_capacity, efforts, start_sprint)
        
        start_sprints.append(start_sprint)
        end_sprints.append(end_sprint)
    
    roadmap_df[COL_START_SPRINT] = start_sprints
    roadmap_df[COL_END_SPRINT] = end_sprints
    roadmap_df[COL_SPRINTS_REQUIRED] = roadmap_df[COL_END_SPRINT] - roadmap_df[COL_START_SPRINT] + 1
    
    # Clean up temp column
    roadmap_df = roadmap_df.drop(columns=['_has_ds'], errors='ignore')
    
    return roadmap_df

def calculate_sprint_load(roadmap_df, backlog_df):
    """
    Calculates demand per sprint per competency.
    For each feature active during a sprint, its effort is spread across its duration.
    """
    if roadmap_df.empty:
        return pd.DataFrame()
    
    max_sprint = int(roadmap_df[COL_END_SPRINT].max())
    sprints = list(range(1, max_sprint + 1))
    
    load_data = []
    
    for s in sprints:
        sprint_row = {COL_SPRINT: s}
        for comp in COMPETENCIES:
            sprint_row[LOAD_COLS[comp]] = 0
            
        active_features = roadmap_df[(roadmap_df[COL_START_SPRINT] <= s) & (roadmap_df[COL_END_SPRINT] >= s)]
        
        for _, feat in active_features.iterrows():
            duration = feat[COL_SPRINTS_REQUIRED]
            for comp, effort_col in EFFORT_COLS.items():
                if duration > 0:
                    effort_per_sprint = feat[effort_col] / duration
                    sprint_row[LOAD_COLS[comp]] += effort_per_sprint
                
        load_data.append(sprint_row)
        
    return pd.DataFrame(load_data)
