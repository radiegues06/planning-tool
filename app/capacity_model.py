import pandas as pd
from data_models import *

def _get_sprint_length_weeks(sprints_df, sprint_num, default=2):
    """Derive sprint length in weeks from the sprint calendar dates. Falls back to default."""
    if sprints_df is None or sprints_df.empty:
        return default
    sprint_info = sprints_df[sprints_df[COL_SPR_NUMBER] == sprint_num]
    if sprint_info.empty:
        return default
    try:
        start = pd.to_datetime(sprint_info.iloc[0][COL_SPR_START_DATE]).date()
        end = pd.to_datetime(sprint_info.iloc[0][COL_SPR_END_DATE]).date()
        weeks = max((end - start).days / 7, 0.5)
        return weeks
    except Exception:
        return default


def calculate_team_capacity(team_df, vacations_df=None, sprints_df=None):
    """
    Calculates capacity per person and aggregates total capacity per competency per sprint.
    Sprint length is derived per-sprint from the sprint calendar dates.
    Supports deductions from vacations based on calendar dates.
    Returns: Dict mapping sprint_num -> {competency -> capacity}
    """
    if team_df.empty:
        return {}
    
    # Make sprint limit dynamic if sprints_df is available
    if sprints_df is not None and not sprints_df.empty:
        sprint_nums = sprints_df[COL_SPR_NUMBER].tolist()
        max_sprint = max(sprint_nums)
        sprint_nums = list(range(1, max(50, max_sprint + 1)))
    else:
        sprint_nums = list(range(1, 50))
    
    # Calculate base weekly capacity per person
    team_df['weekly_cap'] = team_df[COL_WEEKLY_HOURS] * (team_df[COL_ALLOCATION_PCT] / 100.0)
    
    capacity_per_sprint = {}
    
    for s_num in sprint_nums:
        sprint_length_weeks = _get_sprint_length_weeks(sprints_df, s_num)
        temp_team = team_df.copy()
        temp_team['sprint_cap'] = temp_team['weekly_cap'] * sprint_length_weeks
        
        # Deduct vacations by date mapping
        if vacations_df is not None and not vacations_df.empty and sprints_df is not None and not sprints_df.empty:
            sprint_info = sprints_df[sprints_df[COL_SPR_NUMBER] == s_num]
            if not sprint_info.empty:
                try:
                    sprint_start = pd.to_datetime(sprint_info.iloc[0][COL_SPR_START_DATE]).date()
                    sprint_end = pd.to_datetime(sprint_info.iloc[0][COL_SPR_END_DATE]).date()
                    
                    for _, v_row in vacations_df.iterrows():
                        v_start = pd.to_datetime(v_row[COL_VAC_START_DATE]).date()
                        v_end = pd.to_datetime(v_row[COL_VAC_END_DATE]).date()
                        
                        overlap_start = max(sprint_start, v_start)
                        overlap_end = min(sprint_end, v_end)
                        
                        if overlap_start <= overlap_end:
                            days_off = (overlap_end - overlap_start).days + 1
                            sprint_total_days = (sprint_end - sprint_start).days + 1
                            
                            person = v_row[COL_VAC_PERSON]
                            person_mask = temp_team[COL_PERSON] == person
                            
                            if not temp_team[person_mask].empty:
                                base_sprint_cap = temp_team.loc[person_mask, 'weekly_cap'].values[0] * sprint_length_weeks
                                hours_deducted = (days_off / sprint_total_days) * base_sprint_cap
                                temp_team.loc[person_mask, 'sprint_cap'] -= hours_deducted
                except Exception:
                    pass
        
        # Clip at 0
        temp_team['sprint_cap'] = temp_team['sprint_cap'].clip(lower=0)
        
        # Aggregate
        comp_agg = temp_team.groupby(COL_COMPETENCY)['sprint_cap'].sum().to_dict()
        
        for comp in COMPETENCIES:
            if comp not in comp_agg:
                comp_agg[comp] = 0
                
        capacity_per_sprint[s_num] = comp_agg
        
    return capacity_per_sprint

def get_capacity_dict(capacity_per_sprint):
    """Legacy helper for backward compatibility - returns average cap or cap for sprint 1 if needed."""
    if not capacity_per_sprint:
        return {comp: 0 for comp in COMPETENCIES}
    return capacity_per_sprint.get(1, {comp: 0 for comp in COMPETENCIES})
