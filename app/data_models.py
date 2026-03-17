import pandas as pd

# Columns for Team Capacity DataFrame
COL_PERSON = "person"
COL_COMPETENCY = "competency"
COL_WEEKLY_HOURS = "hours_per_week"
COL_ALLOCATION_PCT = "allocation_pct"
COL_CAPACITY_PER_SPRINT = "capacity_per_sprint"

# Competency constants
COMP_DE = "Data Engineering"
COMP_DS = "Data Science"
COMP_FE = "Frontend"
COMP_PO = "Business / PO"

COMPETENCIES = [COMP_DE, COMP_DS, COMP_FE, COMP_PO]

# Columns for Backlog DataFrame
COL_FEATURE_ID = "feature_id"
COL_FEATURE_NAME = "feature_name"
COL_INDICATOR = "indicator"
COL_EPIC = "epic"
COL_BUSINESS_VALUE = "business_value"

INDICATORS = ["Conformidade", "Aderência", "Prontidão", "Should Cost", "Produtização"]
COL_EFFORT_DE = "effort_DE"
COL_EFFORT_DS = "effort_DS"
COL_EFFORT_FE = "effort_FE"
COL_EFFORT_PO = "effort_PO"
COL_TOTAL_EFFORT = "total_effort"
COL_SCORE = "score"

# Columns for Roadmap DataFrame
COL_START_SPRINT = "start_sprint"
COL_END_SPRINT = "end_sprint"
COL_SPRINTS_REQUIRED = "sprints_required"

# Columns for Sprint Load DataFrame
COL_SPRINT = "sprint"
COL_DE_DEMAND = "DE_demand"
COL_DS_DEMAND = "DS_demand"
COL_FE_DEMAND = "FE_demand"
COL_PO_DEMAND = "PO_demand"

# Columns for Vacations tab
COL_VAC_PERSON = "person"
COL_VAC_START_DATE = "start_date"
COL_VAC_END_DATE = "end_date"

# Columns for Sprints tab
COL_SPR_NUMBER = "sprint"
COL_SPR_START_DATE = "start_date"
COL_SPR_END_DATE = "end_date"

# Add priority to backlog
COL_PRIORITY = "priority"
COL_MANUAL_START = "manual_start_sprint"

LOAD_COLS = {
    COMP_DE: COL_DE_DEMAND,
    COMP_DS: COL_DS_DEMAND,
    COMP_FE: COL_FE_DEMAND,
    COMP_PO: COL_PO_DEMAND
}

EFFORT_COLS = {
    COMP_DE: COL_EFFORT_DE,
    COMP_DS: COL_EFFORT_DS,
    COMP_FE: COL_EFFORT_FE,
    COMP_PO: COL_EFFORT_PO
}

# Milestones tab columns
COL_MS_INDICATOR = "indicator"
COL_MS_DATE = "date"
COL_MS_TARGET = "target"
