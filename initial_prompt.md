You are an experienced **software architect and data product engineer**.

Your task is to design and implement a **data product roadmap and capacity planning tool** using **Python and Streamlit**.

Before writing code, you must:

1. Analyze the requirements
2. Propose an architecture
3. Break the work into tasks
4. Then implement the solution incrementally

The objective is to build an **interactive planning tool for data product teams** that calculates capacity, prioritizes features, and automatically builds a roadmap.

The tool should be easy to modify and suitable for experimentation and scenario simulation.

---

# Context

We are planning the development roadmap of a **data product team** composed of multiple competencies:

* Data Engineering
* Data Science
* Frontend
* Business / Product Owner (PO)

Each feature requires effort from one or more of these competencies.

The tool must support:

* backlog prioritization
* capacity planning
* automatic roadmap construction
* capacity bottleneck detection
* interactive visualization

Originally this logic existed in Excel, but now we want a **Streamlit application** that performs these calculations and visualizations automatically.

---

# Core Functional Requirements

The application must support the following workflow.

## 1. Team Capacity Modeling

The user defines the team composition.

Each person has:

* name
* competency (DE, DS, FE, PO)
* weekly hours
* allocation percentage
* sprint length (weeks)

Capacity per sprint must be calculated as:

capacity_per_sprint =
hours_per_week × allocation_percentage × sprint_length_weeks

The system must then aggregate total capacity per sprint per competency.

Example output:

competency | capacity_per_sprint
Data Engineering | 160
Data Science | 80
Frontend | 40
PO | 50

---

## 2. Backlog Definition

The backlog contains product features with:

* feature_id
* feature_name
* priority
* business_value
* effort_DE
* effort_DS
* effort_FE
* effort_PO

Total effort must be computed as:

total_effort = sum(all competency efforts)

Prioritization score must be:

score = business_value / total_effort

The backlog must be sortable by this score.

---

## 3. Automatic Feature Duration Calculation

Each feature requires different competencies.

We calculate how many sprints each competency needs:

sprints_DE = effort_DE / capacity_DE
sprints_DS = effort_DS / capacity_DS
sprints_FE = effort_FE / capacity_FE
sprints_PO = effort_PO / capacity_PO

The feature duration is defined by the bottleneck:

sprints_required =
max(sprints_DE, sprints_DS, sprints_FE, sprints_PO)

Round up to the next integer sprint.

---

## 4. Automatic Roadmap Construction

The roadmap should be generated automatically based on:

* feature priority score
* estimated duration

Algorithm:

1. Sort backlog by prioritization score
2. Start roadmap at sprint 1
3. Assign features sequentially
4. For each feature:

start_sprint = previous_feature_end + 1
end_sprint = start_sprint + sprints_required - 1

The roadmap output should contain:

feature_id
feature_name
start_sprint
end_sprint

---

## 5. Sprint Capacity Load Calculation

The system must calculate demand per sprint per competency.

For each sprint:

sum all effort from features active during that sprint.

Output example:

sprint | DE_demand | DS_demand | FE_demand | PO_demand

This allows identifying bottlenecks.

---

## 6. Bottleneck Detection

Compute:

gap = capacity − demand

If gap < 0 → there is a bottleneck.

This should be highlighted in visualizations.

---

# Visualization Requirements

Use **Streamlit + Plotly or Altair**.

The UI must contain at least these sections.

---

## 1. Roadmap Visualization

Display a **Gantt chart** showing:

* features on Y axis
* sprint timeline on X axis
* feature start and end

This provides a product roadmap visualization.

---

## 2. Capacity vs Demand Charts

For each competency, show:

* capacity
* demand

Preferably using:

* bar charts
* stacked charts
* or line comparison charts

---

## 3. Bottleneck Heatmap

Display a matrix:

rows → sprint
columns → competency

Color indicates:

green → capacity available
red → capacity exceeded

---

## 4. Scenario Simulation

The interface should allow changing parameters interactively:

Examples:

* number of Data Engineers
* number of Data Scientists
* backlog priorities
* effort estimates

When inputs change:

the roadmap and charts should recompute automatically.

---

# Data Model

Use pandas DataFrames for the main structures.

Suggested models:

team_capacity_df

columns:
person
competency
hours_per_week
allocation_pct
capacity_per_sprint

backlog_df

columns:
feature_id
feature_name
business_value
effort_DE
effort_DS
effort_FE
effort_PO
total_effort
score

roadmap_df

columns:
feature_id
feature_name
start_sprint
end_sprint

sprint_load_df

columns:
sprint
DE_demand
DS_demand
FE_demand
PO_demand

---

# Architecture Requirements

Use the following structure:

app/
app.py
roadmap_engine.py
capacity_model.py
data_models.py
charts.py
utils.py

Responsibilities:

capacity_model.py
team capacity calculation

roadmap_engine.py
roadmap generation and sprint demand calculation

charts.py
visualizations

app.py
streamlit UI

---

# Development Instructions

Follow this process:

1. Analyze the requirements
2. Propose system architecture
3. Define data models
4. Implement capacity model
5. Implement roadmap generation logic
6. Implement sprint load calculations
7. Implement visualizations
8. Build Streamlit UI
9. Add scenario simulation inputs

Keep the code modular and readable.

---

# Final Objective

Produce a **working Streamlit application** that allows a data team to:

* define team capacity
* define backlog
* prioritize features
* automatically generate a roadmap
* detect capacity bottlenecks
* simulate team composition changes

The final result should resemble a lightweight internal tool similar to:

* Jira Advanced Roadmaps
* Productboard
* Aha!

But focused on **data product teams and capacity planning**.

Start by analyzing the problem and proposing the architecture before writing the code.
