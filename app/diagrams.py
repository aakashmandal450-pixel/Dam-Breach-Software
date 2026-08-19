import plotly.graph_objects as go


def dam_cross_section_figure(water_level_m: float, dam_height_m: float, breach_depth_m: float) -> go.Figure:
    """Return a simple labelled dam cross-section diagram."""
    crest = dam_height_m
    water = min(water_level_m, dam_height_m)
    breach_bottom = max(dam_height_m - breach_depth_m, 0.0)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[0, 35, 70],
            y=[0, crest, 0],
            fill="toself",
            mode="lines",
            name="Dam body",
            line=dict(color="#6f6258", width=2),
            fillcolor="rgba(111,98,88,0.35)",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[-25, 0, 0, -25],
            y=[0, 0, water, water],
            fill="toself",
            mode="lines",
            name="Reservoir",
            line=dict(color="#1b7895", width=2),
            fillcolor="rgba(27,120,149,0.35)",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[29, 35, 41],
            y=[crest, breach_bottom, crest],
            mode="lines",
            name="Final breach",
            line=dict(color="#b3332f", width=4),
        )
    )
    fig.add_annotation(x=35, y=crest + 2, text="Dam crest", showarrow=False)
    fig.add_annotation(x=-18, y=water + 1.5, text="Reservoir level", showarrow=False)
    fig.add_annotation(x=47, y=(crest + breach_bottom) / 2, text="Breach depth", showarrow=True, ax=35, ay=0)
    fig.update_layout(
        height=280,
        margin=dict(l=10, r=10, t=20, b=10),
        xaxis=dict(visible=False),
        yaxis=dict(title="Elevation / height (m)", rangemode="tozero"),
        legend=dict(orientation="h", y=-0.15),
    )
    return fig


def glof_trigger_figure() -> go.Figure:
    """Return a simple conceptual GLOF trigger diagram."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[0, 20, 40, 60, 80, 100],
            y=[65, 75, 63, 70, 55, 60],
            mode="lines",
            name="Mountain slope",
            line=dict(color="#5f6b72", width=3),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[35, 50, 65, 80],
            y=[25, 25, 28, 25],
            fill="toself",
            mode="lines",
            name="Glacial lake",
            line=dict(color="#1b7895", width=2),
            fillcolor="rgba(27,120,149,0.35)",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[80, 88, 96],
            y=[25, 45, 25],
            fill="toself",
            mode="lines",
            name="Moraine dam",
            line=dict(color="#6f6258", width=2),
            fillcolor="rgba(111,98,88,0.4)",
        )
    )
    fig.add_annotation(x=28, y=62, text="Avalanche / icefall", showarrow=True, ax=-20, ay=-25)
    fig.add_annotation(x=58, y=33, text="Impulse wave", showarrow=True, ax=-30, ay=-10)
    fig.add_annotation(x=91, y=39, text="Overtopping risk", showarrow=True, ax=20, ay=-20)
    fig.update_layout(
        height=280,
        margin=dict(l=10, r=10, t=20, b=10),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        legend=dict(orientation="h", y=-0.15),
    )
    return fig
