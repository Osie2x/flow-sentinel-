"""Dash monitoring app for FlowSentinel."""

from __future__ import annotations

import sqlite3

import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, dash_table, dcc, html

from flowsentinel.config import DASHBOARD_PORT, DASHBOARD_REFRESH_MS, DASHBOARD_TREND_DAYS, DB_PATH


def query(sql: str, params: tuple = ()) -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame()
    with sqlite3.connect(DB_PATH) as connection:
        return pd.read_sql_query(sql, connection, params=params)


def latest_score() -> dict:
    frame = query("SELECT * FROM health_scores ORDER BY computed_at DESC LIMIT 1")
    if frame.empty:
        return {
            "composite_score": 0.0,
            "completeness": 0.0,
            "error_rate": 0.0,
            "throughput": 0.0,
            "anomaly_rate": 0.0,
            "total_records": 0,
        }
    return frame.iloc[0].to_dict()


app = Dash(__name__, title="FlowSentinel Dashboard")

app.layout = html.Div(
    style={"fontFamily": "'Segoe UI', sans-serif", "backgroundColor": "#0D1B2A", "minHeight": "100vh", "padding": "24px", "color": "#F4F6F8"},
    children=[
        html.Div(
            [
                html.H1("FlowSentinel", style={"color": "#1B998B", "margin": 0, "fontSize": "30px"}),
                html.P("Business Process Automation & Monitoring", style={"color": "#9CA3AF", "margin": 0}),
            ],
            style={"marginBottom": "24px"},
        ),
        dcc.Interval(id="refresh", interval=DASHBOARD_REFRESH_MS, n_intervals=0),
        html.Div(id="kpi-cards", style={"display": "flex", "gap": "16px", "marginBottom": "24px", "flexWrap": "wrap"}),
        html.Div(
            [
                html.Div([dcc.Graph(id="gauge-chart")], style={"flex": "0 0 320px", "backgroundColor": "#1A2E45", "borderRadius": "8px", "padding": "16px"}),
                html.Div([dcc.Graph(id="score-trend")], style={"flex": "1", "backgroundColor": "#1A2E45", "borderRadius": "8px", "padding": "16px", "marginLeft": "16px"}),
            ],
            style={"display": "flex", "marginBottom": "24px"},
        ),
        html.Div(
            [
                html.Div([dcc.Graph(id="volume-chart")], style={"flex": "1", "backgroundColor": "#1A2E45", "borderRadius": "8px", "padding": "16px"}),
                html.Div([dcc.Graph(id="exception-chart")], style={"flex": "1", "backgroundColor": "#1A2E45", "borderRadius": "8px", "padding": "16px", "marginLeft": "16px"}),
            ],
            style={"display": "flex", "marginBottom": "24px"},
        ),
        html.Div(
            [
                html.H3("Recent anomaly flags", style={"color": "#1B998B", "marginTop": 0}),
                html.Div(id="anomaly-table"),
            ],
            style={"backgroundColor": "#1A2E45", "borderRadius": "8px", "padding": "16px"},
        ),
    ],
)


@app.callback(
    Output("kpi-cards", "children"),
    Output("gauge-chart", "figure"),
    Output("score-trend", "figure"),
    Output("volume-chart", "figure"),
    Output("exception-chart", "figure"),
    Output("anomaly-table", "children"),
    Input("refresh", "n_intervals"),
)
def update_all(_: int):
    score = latest_score()
    trend = query(
        f"SELECT run_date, composite_score FROM health_scores ORDER BY run_date DESC LIMIT {DASHBOARD_TREND_DAYS}"
    )
    volume = query(
        f"SELECT date, COUNT(*) AS records, SUM(CASE WHEN has_violation = 1 THEN 1 ELSE 0 END) AS violations "
        f"FROM records GROUP BY date ORDER BY date DESC LIMIT {DASHBOARD_TREND_DAYS}"
    )
    exception_summary = query(
        "SELECT team, severity, COUNT(*) AS count FROM exceptions GROUP BY team, severity ORDER BY count DESC"
    )
    anomalies = query(
        "SELECT record_id, detector, field, score, flagged_at FROM anomalies ORDER BY flagged_at DESC LIMIT 20"
    )

    cards = []
    for label, value, color in [
        ("Health Score", f"{score.get('composite_score', 0):.1f}/100", "#1B998B"),
        ("Records", f"{int(score.get('total_records', 0)):,}", "#3B82F6"),
        ("Completeness", f"{score.get('completeness', 0):.1f}%", "#8B5CF6"),
        ("Error-Free", f"{score.get('error_rate', 0):.1f}%", "#F59E0B"),
        ("Anomaly-Free", f"{score.get('anomaly_rate', 0):.1f}%", "#EF4444"),
    ]:
        cards.append(
            html.Div(
                [html.P(label, style={"margin": 0, "fontSize": "11px", "color": "#9CA3AF"}), html.H2(value, style={"margin": 0, "color": color, "fontSize": "22px"})],
                style={"backgroundColor": "#1A2E45", "borderRadius": "8px", "padding": "16px 20px", "minWidth": "140px"},
            )
        )

    gauge = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=float(score.get("composite_score", 0)),
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#1B998B"},
                "steps": [
                    {"range": [0, 60], "color": "#2D1B1B"},
                    {"range": [60, 75], "color": "#2D2510"},
                    {"range": [75, 90], "color": "#102D20"},
                    {"range": [90, 100], "color": "#0D2520"},
                ],
                "threshold": {"line": {"color": "#FFBF00", "width": 2}, "value": 75},
            },
            title={"text": "Process Health", "font": {"color": "#F4F6F8"}},
            number={"font": {"color": "#1B998B", "size": 36}},
        )
    )
    gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#F4F6F8", height=260)

    score_trend = go.Figure()
    if not trend.empty:
        score_trend.add_trace(
            go.Scatter(
                x=trend["run_date"][::-1],
                y=trend["composite_score"][::-1],
                mode="lines+markers",
                line={"color": "#1B998B", "width": 2},
                fill="tozeroy",
                fillcolor="rgba(27,153,139,0.15)",
                name="Health Score",
            )
        )
    score_trend.add_hline(y=75, line_dash="dash", line_color="#FFBF00", annotation_text="Target")
    score_trend.update_layout(title="Health Score Trend", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#9CA3AF", height=260, yaxis_range=[0, 100])

    volume_chart = go.Figure()
    if not volume.empty:
        volume_chart.add_trace(go.Bar(x=volume["date"][::-1], y=volume["records"][::-1], name="Records", marker_color="#3B82F6"))
        volume_chart.add_trace(go.Bar(x=volume["date"][::-1], y=volume["violations"][::-1], name="Violations", marker_color="#EF4444"))
    volume_chart.update_layout(title="Daily Volume & Violations", barmode="overlay", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#9CA3AF", height=260)

    exception_chart = go.Figure()
    if not exception_summary.empty:
        exception_chart.add_trace(
            go.Bar(
                x=exception_summary["team"],
                y=exception_summary["count"],
                marker_color=exception_summary["severity"].map({"HIGH": "#EF4444", "MEDIUM": "#F59E0B", "LOW": "#6B7280"}).fillna("#6B7280"),
                text=exception_summary["severity"],
                textposition="auto",
            )
        )
    exception_chart.update_layout(title="Exceptions by Team", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#9CA3AF", height=260)

    if anomalies.empty:
        anomaly_table = html.P("No anomalies found yet.", style={"color": "#9CA3AF"})
    else:
        anomaly_table = dash_table.DataTable(
            data=anomalies.to_dict("records"),
            columns=[{"name": column.replace("_", " ").title(), "id": column} for column in anomalies.columns],
            style_header={"backgroundColor": "#0D1B2A", "color": "#1B998B", "fontWeight": "bold", "border": "1px solid #2D4A6A"},
            style_data={"backgroundColor": "#1A2E45", "color": "#F4F6F8", "border": "1px solid #2D4A6A"},
            style_data_conditional=[{"if": {"row_index": "odd"}, "backgroundColor": "#152438"}],
            page_size=10,
        )

    return cards, gauge, score_trend, volume_chart, exception_chart, anomaly_table


def main() -> None:
    app.run(debug=True, port=DASHBOARD_PORT)


if __name__ == "__main__":
    main()

