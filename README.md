# 🚀 Data Product Roadmap & Capacity Planner

## 🎯 Repository Goal
The **Data Product Roadmap & Capacity Planner** is an automated planning tool designed to help Data & Analytics teams prioritize their backlog, manage team capacity, and automatically generate comprehensive product roadmaps. 

It replaces manual spreadsheet planning with an interactive, Streamlit-based application that optimizes feature scheduling based on business value, effort required across different competencies (Data Engineering, Data Science, Frontend, PO), and team availability (including vacations).

## ✨ Key Features
*   **Dynamic Capacity Engine:** Automatically calculates available hours per sprint based on team composition, weekly hours, allocation percentages, and scheduled vacations.
*   **Automated Prioritization:** Calculates a normalized score for each feature based on Business Value vs. Total Effort, factored by Priority.
*   **Epic-Level Parallel Scheduling:** Groups features by Epic and intelligently schedules them in parallel, maximizing team utilization (especially prioritizing Data Science tasks) without exceeding the capacity of any specific competency.
*   **Interactive Visualizations:** 
    *   **Gantt Chart:** Visualizes the generated roadmap grouped by business Indicators, clearly showing Epic timelines and highlighting capacity bottleneck sprints.
    *   **Unified Capacity Chart:** A detailed, overlapping bar chart comparing the precise demand vs. available capacity for every competency across all sprints.
*   **Excel Persistence:** All configurations (Team, Vacations, Sprints) and Backlog data remain persistent locally via an underlying Excel file (`planning_data.xlsx`).

## 🛠️ Tech Stack
*   **Python:** Core logic and automated scheduling engine.
*   **Streamlit:** Interactive web interface and data editors.
*   **Plotly:** Advanced, interactive charting (Gantt and Overlaid Bar Charts).
*   **Pandas:** Data manipulation, capacity calculation, and Excel I/O.

## 🚀 How to Run Locally

### Prerequisites
*   Python 3.9+ installed on your system.

### Setup Instructions
1. Clone the repository to your local machine.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
3. Activate the virtual environment:
   * **Windows:** `venv\Scripts\activate`
   * **Mac/Linux:** `source venv/bin/activate`
4. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the App (Windows)
You can directly run the included batch file by double-clicking it:
*   `start_tool.bat`

**Alternatively, via terminal (All OS):**
1. Ensure your virtual environment is activated.
2. Run the Streamlit application:
   ```bash
   streamlit run app/app.py
   ```
3. The application will open automatically in your default web browser at `http://localhost:8501`.
