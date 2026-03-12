import pandas as pd
import os

# Competency constants (hardcoded here to match data_models.py for seed)
COMP_DE = "Data Engineering"
COMP_DS = "Data Science"
COMP_FE = "Frontend"
COMP_PO = "Business / PO"

# Initial Team Data
team_data = pd.DataFrame([
    {"person": "Alice", "competency": COMP_DE, "hours_per_week": 40, "allocation_pct": 100},
    {"person": "Bob", "competency": COMP_DE, "hours_per_week": 40, "allocation_pct": 80},
    {"person": "Charlie", "competency": COMP_DS, "hours_per_week": 40, "allocation_pct": 100},
    {"person": "Dave", "competency": COMP_FE, "hours_per_week": 40, "allocation_pct": 50},
    {"person": "Eve", "competency": COMP_PO, "hours_per_week": 20, "allocation_pct": 100},
])

# Initial Backlog Data with new columns
backlog_data = pd.DataFrame([
    {"feature_id": "F1", "feature_name": "Data Pipeline v1", "indicator": "Conformidade", "epic": "", "business_value": 100, "effort_DE": 160, "effort_DS": 40, "effort_FE": 0, "effort_PO": 20},
    {"feature_id": "F2", "feature_name": "ML Model Training", "indicator": "Prontidão", "epic": "", "business_value": 200, "effort_DE": 40, "effort_DS": 120, "effort_FE": 0, "effort_PO": 40},
    {"feature_id": "F3", "feature_name": "Analytics Dashboard", "indicator": "Aderência", "epic": "", "business_value": 150, "effort_DE": 40, "effort_DS": 20, "effort_FE": 80, "effort_PO": 30},
    {"feature_id": "F4", "feature_name": "User API Integration", "indicator": "Should Cost", "epic": "", "business_value": 80, "effort_DE": 80, "effort_DS": 0, "effort_FE": 20, "effort_PO": 20},
])

output_file = "planning_data.xlsx"

if not os.path.exists(output_file):
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        team_data.to_excel(writer, sheet_name='Team', index=False)
        backlog_data.to_excel(writer, sheet_name='Backlog', index=False)
    print(f"Created {output_file}")
else:
    print(f"{output_file} already exists")
