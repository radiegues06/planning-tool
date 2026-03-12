import plotly.graph_objects as go
import pandas as pd
from data_models import *

# Color palette for indicators
INDICATOR_COLORS = {
    "Conformidade": "#3498db",
    "Aderência": "#2ecc71",
    "Prontidão": "#e67e22",
    "Should Cost": "#9b59b6",
}

# Color palette for competencies (used in unified load chart)
COMPETENCY_COLORS = {
    COMP_DE: "#3498db",
    COMP_DS: "#e74c3c",
    COMP_FE: "#2ecc71",
    COMP_PO: "#f39c12",
}

def _get_overloaded_sprints(sprint_load_df, capacity_per_sprint):
    """Returns a set of sprint numbers where any competency exceeds capacity."""
    overloaded = set()
    if sprint_load_df is None or sprint_load_df.empty:
        return overloaded
    for _, row in sprint_load_df.iterrows():
        s = int(row[COL_SPRINT])
        cap = capacity_per_sprint.get(s, {})
        for comp in COMPETENCIES:
            demand = row.get(LOAD_COLS[comp], 0)
            capacity = cap.get(comp, 0)
            if demand > capacity and capacity > 0:
                overloaded.add(s)
                break
    return overloaded

def create_gantt_chart(roadmap_df, sprint_load_df=None, capacity_per_sprint=None):
    """
    Creates a Gantt chart with indicator-based swim lanes.
    Y-axis shows Indicator names (one per group, vertically centered).
    Bars show Epic/Feature names inside.
    Overloaded sprints are highlighted with red translucent vertical bands.
    """
    if roadmap_df.empty:
        return None
    
    df = roadmap_df.copy()
    
    # Group by indicator
    indicators_present = [ind for ind in INDICATORS if ind in df[COL_INDICATOR].values]
    if not indicators_present:
        indicators_present = df[COL_INDICATOR].unique().tolist()
    
    # Build Y-axis structure: one row per epic/feature, grouped by indicator
    y_tick_vals = []
    y_tick_texts = []
    separator_positions = []
    pos = 0
    indicator_mid_positions = {}
    
    for ind in indicators_present:
        ind_items = df[df[COL_INDICATOR] == ind]
        if ind_items.empty:
            continue
        start_pos = pos
        for _, row in ind_items.iterrows():
            pos += 1
        end_pos = pos - 1
        mid_pos = (start_pos + end_pos) / 2
        indicator_mid_positions[ind] = mid_pos
        y_tick_vals.append(mid_pos)
        y_tick_texts.append(ind)
        separator_positions.append(pos - 0.5)
    
    # Remove last separator
    if separator_positions:
        separator_positions.pop()
    
    fig = go.Figure()
    
    # Add bars grouped by indicator
    bar_idx = 0
    for ind in indicators_present:
        ind_items = df[df[COL_INDICATOR] == ind]
        color = INDICATOR_COLORS.get(ind, "#95a5a6")
        
        for _, row in ind_items.iterrows():
            is_manual = pd.notna(row.get(COL_MANUAL_START, None)) and row.get(COL_MANUAL_START, 0) >= 1
            border_color = "#e74c3c" if is_manual else color
            border_width = 3 if is_manual else 1
            
            display_name = row[COL_FEATURE_NAME]
            
            fig.add_trace(go.Bar(
                name=display_name,
                x=[row[COL_SPRINTS_REQUIRED]],
                y=[bar_idx],
                base=row[COL_START_SPRINT] - 0.5,
                orientation='h',
                marker=dict(
                    color=color,
                    line=dict(color=border_color, width=border_width)
                ),
                text=display_name,
                textposition='inside',
                insidetextanchor='middle',
                textfont=dict(color='white', size=12),
                hovertemplate=(
                    f"<b>{display_name}</b><br>"
                    f"Indicator: {ind}<br>"
                    f"Sprint: {row[COL_START_SPRINT]} → {row[COL_END_SPRINT]}<br>"
                    f"Duration: {row[COL_SPRINTS_REQUIRED]} sprints<br>"
                    f"Score: {row[COL_SCORE]:.2f}"
                    + ("<br><b>⚠ Manual Start</b>" if is_manual else "")
                    + "<extra></extra>"
                ),
                showlegend=False
            ))
            bar_idx += 1
    
    # Add horizontal separators between indicator groups
    for sep_pos in separator_positions:
        fig.add_hline(y=sep_pos, line_dash="dot", line_color="rgba(0,0,0,0.3)", line_width=1)
    
    # Add capacity overlay — red shading for overloaded sprints
    if sprint_load_df is not None and capacity_per_sprint is not None:
        overloaded = _get_overloaded_sprints(sprint_load_df, capacity_per_sprint)
        for s in overloaded:
            fig.add_vrect(
                x0=s - 0.5, x1=s + 0.5,
                fillcolor="rgba(231, 76, 60, 0.15)",
                line=dict(color="rgba(231, 76, 60, 0.4)", width=1),
                layer="below",
                annotation_text="⚠",
                annotation_position="top",
                annotation_font_size=10,
                annotation_font_color="red"
            )
    
    max_sprint = int(df[COL_END_SPRINT].max()) + 1
    total_items = bar_idx
    
    fig.update_layout(
        barmode='stack',
        showlegend=False,
        title="Product Roadmap",
        xaxis=dict(
            title="Sprint",
            dtick=1,
            range=[0.5, max_sprint + 0.5]
        ),
        yaxis=dict(
            tickmode='array',
            tickvals=y_tick_vals,
            ticktext=y_tick_texts,
            autorange="reversed",
            title=""
        ),
        margin=dict(l=120),
        template="plotly_white",
        height=max(400, total_items * 55 + 100)
    )
    
    return fig

def create_unified_load_chart(sprint_load_df, capacity_per_sprint, competencies):
    """
    Creates a single grouped bar chart showing demand vs capacity for all competencies.
    - Filled bars for demand
    - Dashed-outline bars for capacity
    - Distinct colors per competency
    - Bottleneck markers where demand > capacity
    """
    if sprint_load_df is None or sprint_load_df.empty:
        return None
    
    sprints = sprint_load_df[COL_SPRINT].tolist()
    
    fig = go.Figure()
    
    # Add demand and capacity bars for each competency
    for comp in competencies:
        demand_col = LOAD_COLS[comp]
        demands = sprint_load_df[demand_col].tolist()
        capacities = [capacity_per_sprint.get(s, {}).get(comp, 0) for s in sprints]
        color = COMPETENCY_COLORS.get(comp, "#95a5a6")
        
        # Short label for legend
        short_label = comp.split(" /")[0].split(" ")[0] if " " in comp else comp
        
        # Capacity bars (behind, full width, dashed/light)
        fig.add_trace(go.Bar(
            x=sprints,
            y=capacities,
            name=f"{short_label} Capacity",
            offsetgroup=comp, # Group by competency
            marker=dict(
                color="rgba(0,0,0,0)",
                line=dict(color=color, width=2),
                pattern=dict(shape="/", fgcolor=color, bgcolor="rgba(255,255,255,0.1)")
            ),
            legendgroup=comp,
        ))
        
        # Demand bars (in front, filled)
        fig.add_trace(go.Bar(
            x=sprints,
            y=demands,
            name=f"{short_label} Demand",
            offsetgroup=comp, # Superimpose on capacity
            marker=dict(color=color, opacity=0.85),
            legendgroup=comp,
        ))
        
        # Bottleneck markers
        bottleneck_x = []
        bottleneck_y = []
        for s, d, c in zip(sprints, demands, capacities):
            if d > c and c > 0:
                bottleneck_x.append(s)
                bottleneck_y.append(d)
        
        if bottleneck_x:
            fig.add_trace(go.Scatter(
                x=bottleneck_x,
                y=bottleneck_y,
                mode='markers+text',
                name=f"{short_label} ⚠",
                marker=dict(color='red', size=12, symbol='x'),
                text=["⚠"] * len(bottleneck_x),
                textposition="top center",
                textfont=dict(color='red', size=10),
                legendgroup=comp,
                showlegend=False,
                offsetgroup=comp, # Keep aligned
            ))
    
    fig.update_layout(
        barmode='group', # Groups the different 'offsetgroup's side-by-side
        title="All Competencies: Capacity vs Demand",
        xaxis=dict(title="Sprint", dtick=1),
        yaxis=dict(title="Hours"),
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=500
    )
    
    return fig
