# Data Model Schema

The system stores configuration in the local file system using Pandas DataFrames which are backed by `planning_data.xlsx`. The tables map directly to tabs in the spreadsheet and persist interactions made within `st.data_editor` in `app.py`.

## Table 1: Team
Maps engineers to capacity percentages per week.
*   **person**: (`text`) User identifier. Used as Foreign Key in `Vacations`.
*   **competency**: (`enum`) Selectbox constraint across the predefined competencies `COMPETENCIES`.
*   **hours_per_week**: (`integer`) Baseline maximum available effort per week.
*   **allocation_pct**: (`integer`) Decimal scaling factor. Determines what percent of `hours_per_week` counts toward productive sprint capacity (0-100%, 5% steps).

## Table 2: Backlog
The core planning input. Contains both metadata and the effort estimates.
*   **feature_id**: (`text`) ID (e.g. TICKET-592).
*   **feature_name**: (`text`) Display label for visualizations.
*   **priority**: (`integer`, min=1) Ranks importance out of sequence for calculating score. Lower is higher priority.
*   **indicator**: (`enum`) Dropdown grouping criteria ("Conformidade", "Aderência", "Prontidão", "Should Cost").
*   **epic**: (`text`) Grouping name.
*   **business_value**: (`float`) Numerator in the automated scoring fraction.
*   **effort_DE, effort_DS, effort_FE, effort_PO**: (`float`) The estimated nominal hours to complete the requirement per competency. They are automatically summed into `total_effort` during roadmap generation.

## Table 3: Vacations
Allows defining date periods where a specific user is absent, reducing available capacity.
*   **person**: (`enum`) Selectbox mapped from the `person` column in `Team`.
*   **start_date / end_date**: (`date`) The physical calendar boundaries of the exception. The engine matches these against actual `sprint_dates` derived from the `Sprints` tab.

## Table 4: Sprints
Maps abstract numbered sprints to a physical calendar.
*   **sprint**: (`integer`) Number mapping.
*   **start_date / end_date**: (`date`) Defines when a sprint opens and closes so that capacity and vacations can be assigned accurately.
