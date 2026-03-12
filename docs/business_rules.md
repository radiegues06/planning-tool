# Business Rules and Auto-Scheduling Algorithm

The planning tool operates based on a few deterministic business rules mapped from data product engineering teams.

## 1. Capacity Calculation Engine
Capacity is aggregated per sprint (usually 2 weeks), per competency: **Data Engineering (DE), Data Science (DS), Frontend (FE), and Business/Product Owner (PO)**.

```math
base\_weekly\_capacity = \sum_{person \in team} hours\_per\_week \times allocation\_pct
```

```math
sprint\_capacity_{ competency, sprint} = base\_weekly\_capacity \times sprint\_length\_weeks
```

### Vacations Deductions
The engine simulates future sprints up to a reasonable limit. If the `Vacations` mapping contains a date range overlapping with a specific sprint, the engine finds the exact number of days overlapping within that sprint. Then, it uses a proportional deduction: the person's total sprint capacity is multiplied by `(overlapping_vacation_days / total_sprint_days)`. This assumes the person is 100% off during those days.

## 2. Priority and Score Calculation
Each feature in the Backlog requires an `effort` estimated in hours for each competency.

```math
total\_effort = effort\_DE + effort\_DS + effort\_FE + effort\_PO
```

An auto-computed `score` determines the scheduling order. A higher score means it is scheduled first.

```math
score = \left( \frac{business\_value}{total\_effort} \right) \times \left( \frac{1}{priority} \right)
```

The lower the `priority` (e.g., 1 is top priority), the higher the multiplier, forcing the feature to the front of the queue regardless of effort.

## 3. Auto-Scheduling Algorithm (generate_roadmap)
The algorithm uses a **queue-based resource reservation model**:

1.  **Sort the Backlog** by the computed `score` in descending order.
2.  **Initialize timeline**: `current_sprint = 1`.
3.  **Iterate through sorted features**:
    *   Set the `start_sprint` of the given feature to the `current_sprint`.
    *   Create a clone of the original effort estimates (`remaining_efforts`).
4.  **Simulate Sprint Consumption** (while loop):
    *   Iterate week-by-week/sprint-by-sprint. `sim_sprint` starts at `start_sprint`.
    *   Retrieve the detailed capacity available for `sim_sprint` specifically, recognizing vacation deductions.
    *   For each active competency requirement, subtract the capacity available for `sim_sprint` from `remaining_efforts`.
    *   Once a competency's remaining effort reaches zero, it no longer consumes capacity.
    *   If any competency effort remains above 0, `sim_sprint` increments by 1.
5.  **Finalize Feature**: The `end_sprint` is the final `sim_sprint`.
6.  **Next Feature**: The next item in the backlog will begin automatically at `end_sprint + 1`.

Because of how the capacity is checked globally at each simulation loop, the engine correctly handles weeks with 0 capacity due to general holidays.
