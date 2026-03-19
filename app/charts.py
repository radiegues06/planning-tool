import plotly.graph_objects as go
import pandas as pd
from data_models import *
from roadmap_engine import date_to_sprint

# Color palette for indicators
INDICATOR_COLORS = {
    "Conformidade": "#3498db",
    "Aderência": "#2ecc71",
    "Prontidão": "#e67e22",
    "Should Cost": "#9b59b6",
    "Produtização": "#e74c3c",
}

# Color palette for competencies (used in unified load chart)
COMPETENCY_COLORS = {
    COMP_DE: "#3498db",
    COMP_DS: "#e74c3c",
    COMP_FE: "#2ecc71",
    COMP_PO: "#f39c12",
}


def _build_sprint_labels(sprints_df, sprint_numbers):
    """
    Builds a dict mapping sprint number -> display label like 'S1\n03/03'.
    Falls back to 'S{n}' if no date is available.
    """
    date_lookup = {}
    if sprints_df is not None and not sprints_df.empty:
        for _, row in sprints_df.iterrows():
            try:
                s_num = int(row[COL_SPR_NUMBER])
                start = pd.to_datetime(row[COL_SPR_START_DATE])
                date_lookup[s_num] = start.strftime("%d/%m")
            except Exception:
                pass

    labels = {}
    for s in sprint_numbers:
        if s in date_lookup:
            labels[s] = f"S{s}<br>{date_lookup[s]}"
        else:
            labels[s] = f"S{s}"
    return labels


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

def create_gantt_chart(roadmap_df, sprint_load_df=None, capacity_per_sprint=None, sprints_df=None, milestones_df=None, show_alerts=False):
    """
    Creates a Gantt chart with indicator-based swim lanes.
    Y-axis shows Indicator names (one per group, vertically centered).
    Bars show Epic/Feature names inside (clipped to fit).
    Overloaded sprints are highlighted with red translucent vertical bands.
    X-axis shows sprint number + start date.
    Hover shows per-competency effort breakdown.
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
    
    # Build sprint labels for x-axis
    max_sprint = int(df[COL_END_SPRINT].max()) + 1
    all_sprints = list(range(1, max_sprint + 1))
    sprint_labels = _build_sprint_labels(sprints_df, all_sprints)
    
    # Add vertical sprint backgrounds and dashed lines
    for i, s in enumerate(all_sprints):
        if i % 2 == 0:
            fig.add_vrect(
                x0=s - 0.5, x1=s + 0.5,
                fillcolor="rgba(0,0,0,0.04)",
                line_width=0,
                layer="below"
            )
        fig.add_vline(x=s - 0.5, line_dash="dash", line_color="rgba(0,0,0,0.1)", line_width=1, layer="below")
    if all_sprints:
        fig.add_vline(x=all_sprints[-1] + 0.5, line_dash="dash", line_color="rgba(0,0,0,0.1)", line_width=1, layer="below")
    
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
            
            # Build effort breakdown for hover
            de_effort = row.get(COL_EFFORT_DE, 0) or 0
            ds_effort = row.get(COL_EFFORT_DS, 0) or 0
            fe_effort = row.get(COL_EFFORT_FE, 0) or 0
            po_effort = row.get(COL_EFFORT_PO, 0) or 0
            total_effort = row.get(COL_TOTAL_EFFORT, 0) or 0
            effort_line = f"Esforço total: {total_effort:.0f}h<br>" + \
                f"DE: {de_effort:.0f}h | DS: {ds_effort:.0f}h | FE: {fe_effort:.0f}h | PO: {po_effort:.0f}h<br>"
            
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
                cliponaxis=True,
                textfont=dict(color='white', size=11),
                hovertemplate=(
                    f"<b>{display_name}</b><br>"
                    f"Score: {row[COL_SCORE]:.1f}<br>"
                    f"Prioridade: {row[COL_PRIORITY]}<br>"
                    f"───────────<br>"
                    f"{effort_line}"
                    f"───────────<br>"
                    f"Features:<br>{row.get(COL_EPIC_FEATURES, row.get(COL_FEATURE_NAME, ''))}<br>"
                    + ("<br><b>⚠ Início Manual</b>" if is_manual else "")
                    + "<extra></extra>"
                ),
                showlegend=False
            ))
            bar_idx += 1
    
    # Add horizontal separators between indicator groups
    for sep_pos in separator_positions:
        fig.add_hline(y=sep_pos, line_dash="dot", line_color="rgba(0,0,0,0.3)", line_width=1)
    
    # Add capacity overlay — red shading for overloaded sprints
    if sprint_load_df is not None and capacity_per_sprint is not None and show_alerts:
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
    
    # Add milestone star markers
    if milestones_df is not None and not milestones_df.empty and sprints_df is not None:
        for _, ms_row in milestones_df.iterrows():
            ms_indicator = str(ms_row.get(COL_MS_INDICATOR, "")).strip()
            ms_date = ms_row.get(COL_MS_DATE)
            ms_target = str(ms_row.get(COL_MS_TARGET, ""))
            
            if not ms_indicator or pd.isna(ms_date):
                continue
            
            sprint_num = date_to_sprint(ms_date, sprints_df)
            if sprint_num is None:
                continue
            
            y_pos = indicator_mid_positions.get(ms_indicator)
            if y_pos is None:
                continue
            
            ms_date_str = pd.to_datetime(ms_date).strftime("%d/%m/%Y")
            
            fig.add_trace(go.Scatter(
                x=[sprint_num],
                y=[y_pos],
                mode='markers+text',
                marker=dict(
                    symbol='star',
                    size=18,
                    color='gold',
                    line=dict(color='darkorange', width=1.5)
                ),
                text=[ms_target],
                textposition='top center',
                textfont=dict(color='darkorange', size=11, family='Arial Black'),
                hovertemplate=(
                    f"<b>🎯 Milestone</b><br>"
                    f"Indicador: {ms_indicator}<br>"
                    f"Data: {ms_date_str}<br>"
                    f"Meta: {ms_target}"
                    "<extra></extra>"
                ),
                showlegend=False
            ))
    
    total_items = bar_idx
    
    fig.update_layout(
        barmode='stack',
        showlegend=False,
        title="Roadmap do Produto",
        xaxis=dict(
            title="Sprint",
            tickmode='array',
            tickvals=all_sprints,
            ticktext=[sprint_labels[s] for s in all_sprints],
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

def create_unified_load_chart(sprint_load_df, capacity_per_sprint, competencies, sprints_df=None):
    """
    Creates a single grouped bar chart showing demand vs capacity for all competencies.
    - Filled bars for demand
    - Dashed-outline bars for capacity
    - Distinct colors per competency
    - Bottleneck markers where demand > capacity
    - X-axis shows sprint number + start date
    """
    if sprint_load_df is None or sprint_load_df.empty:
        return None
    
    sprints = sprint_load_df[COL_SPRINT].tolist()
    sprint_labels = _build_sprint_labels(sprints_df, [int(s) for s in sprints])
    x_labels = [sprint_labels[int(s)] for s in sprints]
    
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
            x=x_labels,
            y=capacities,
            name=f"{short_label} Capacidade",
            offsetgroup=comp,
            marker=dict(
                color="rgba(0,0,0,0)",
                line=dict(color=color, width=2),
                pattern=dict(shape="/", fgcolor=color, bgcolor="rgba(255,255,255,0.1)")
            ),
            legendgroup=comp,
            showlegend=False,
            hovertemplate="%{y:.0f}h<extra></extra>",
        ))
        
        # Demand bars (in front, filled)
        fig.add_trace(go.Bar(
            x=x_labels,
            y=demands,
            name=f"{short_label} Demanda",
            offsetgroup=comp,
            marker=dict(color=color, opacity=0.85),
            legendgroup=comp,
            showlegend=False,
            hovertemplate="%{y:.0f}h<extra></extra>",
        ))
        
        # Bottleneck markers
        bottleneck_x = []
        bottleneck_y = []
        for lbl, d, c in zip(x_labels, demands, capacities):
            if d > c and c > 0:
                bottleneck_x.append(lbl)
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
                offsetgroup=comp,
            ))

    # Add dummy traces for simplified legend
    # 1. Competency Colors
    for comp in competencies:
        color = COMPETENCY_COLORS.get(comp, "#95a5a6")
        fig.add_trace(go.Bar(
            x=[None], y=[None],
            name=comp,
            marker=dict(color=color),
            legendgroup="colors",
            legendgrouptitle_text="Competências" if comp == competencies[0] else None
        ))
        
    # 2. Demand vs Capacity Styles
    style_color = "rgba(100, 100, 100, 0.8)"
    fig.add_trace(go.Bar(
        x=[None], y=[None],
        name="Demanda",
        marker=dict(color=style_color),
        legendgroup="styles",
        legendgrouptitle_text="Tipo"
    ))
    fig.add_trace(go.Bar(
        x=[None], y=[None],
        name="Capacidade",
        marker=dict(
            color="rgba(0,0,0,0)",
            line=dict(color=style_color, width=2),
            pattern=dict(shape="/", fgcolor=style_color)
        ),
        legendgroup="styles"
    ))
    
    fig.update_layout(
        barmode='group',
        title="Todas as Competências: Capacidade vs Demanda",
        xaxis=dict(title="Sprint"),
        yaxis=dict(title="Horas"),
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
