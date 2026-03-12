# Architecture Overview

The Data Product Roadmap & Capacity Planning Tool is a Python-based application built with **Streamlit** and **Plotly**. It follows a modular architecture separating data models, capacity calculation, roadmap algorithms, and visualization logic.

## Module Structure

*   **`app.py`**: The main execution script and Streamlit interface. Responsible for tying all modules together, handling user input via `st.data_editor`, persisting state to Excel, and laying out the UI components across tabs.
*   **`data_models.py`**: Contains all constants for column names across DataFrames. This ensures consistency and prevents typos when referencing columns in pandas.
*   **`capacity_model.py`**: Contains `calculate_team_capacity`. It takes the base team configuration and applies deductions based on the `vacations_df` and `sprints_df` to output a sprint-by-sprint true capacity dictionary.
*   **`roadmap_engine.py`**: The core algorithmic module. 
    *   `calculate_feature_durations` estimates nominal sprints.
    *   `generate_roadmap` executes the primary auto-scheduling simulation.
    *   `calculate_sprint_load` aggregates the total demand per sprint after the roadmap is built.
*   **`charts.py`**: Uses Plotly Graph Objects to generate the interactive visualizations (Gantt chart and Capacity vs Demand bar/line charts).

## Data Flow

1.  **Initialize**: `app.py` reads `planning_data.xlsx` via pandas and loads it into `st.session_state`.
2.  **Edit**: The user edits DataFrames directly in the UI. Streamlit captures these edits into new DataFrames.
3.  **Process Capacity**: `app.py` passes Team, Vacations, and Sprints DataFrames to `calculate_team_capacity`. A sprint granular capacity dictionary is returned.
4.  **Process Roadmap**: The Backlog is enriched with `total_effort` and `score`. It, along with the capacity dictionary, is passed into `generate_roadmap`.
5.  **Calculate Demand**: The resulting roadmap and the backlog are passed to `calculate_sprint_load` to figure out sprint-by-sprint demand.
6.  **Visualize**: DataFrames and demand summaries are piped into functions from `charts.py`, and the resulting `go.Figure` objects are rendered using `st.plotly_chart`.
7.  **Persist**: The user clicks "Save", invoking `save_data` in `app.py` to overwrite `planning_data.xlsx` with current states.
