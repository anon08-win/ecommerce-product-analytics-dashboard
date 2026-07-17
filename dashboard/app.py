"""
E-Commerce Product Analytics Dashboard
Multi-page Plotly Dash application with 6 tabs.
Run: python dashboard/app.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from src.data_loader import build_analytical_dataset
from src.analytics import (
    compute_executive_kpis, compute_funnel, monthly_revenue,
    revenue_by_category, revenue_by_state, top_sellers, seasonal_trends,
    rfm_segmentation, rfm_summary, cohort_analysis, category_performance,
    pareto_analysis, retention_analysis, best_selling_products,
    low_performing_products, customer_distribution, churn_risk, top_customers,
)
from src.insights import generate_insights

# ---------------------------------------------------------------------------
# Theme & Layout Constants
# ---------------------------------------------------------------------------
COLORS = {
    "bg": "#F8F9FA",
    "card": "#FFFFFF",
    "primary": "#1A73E8",
    "secondary": "#5F6368",
    "success": "#34A853",
    "warning": "#FBBC04",
    "danger": "#EA4335",
    "text": "#202124",
    "text_light": "#5F6368",
    "border": "#E8EAED",
    "chart_palette": ["#1A73E8", "#34A853", "#FBBC04", "#EA4335", "#9334E6",
                       "#FF6D01", "#185ABC", "#B31412", "#0D652D", "#E37400"],
}


def chart_layout(**overrides):
    """Build a plotly layout dict with consistent styling. Handles xaxis/yaxis merging."""
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, -apple-system, sans-serif", size=12, color=COLORS["text"]),
        margin=dict(l=20, r=20, t=40, b=20),
        hovermode="x unified",
        xaxis=dict(gridcolor="#F1F3F4", showgrid=True),
        yaxis=dict(gridcolor="#F1F3F4", showgrid=True),
    )
    for k, v in overrides.items():
        if k == "xaxis" and isinstance(v, dict):
            layout["xaxis"].update(v)
        elif k == "yaxis" and isinstance(v, dict):
            layout["yaxis"].update(v)
        else:
            layout[k] = v
    return layout


# ---------------------------------------------------------------------------
# Load Data
# ---------------------------------------------------------------------------
print("Loading and processing dataset...")
df = build_analytical_dataset()
print("Computing analytics...")
kpis = compute_executive_kpis(df)
funnel = compute_funnel(df)
monthly = monthly_revenue(df)
cat_rev = revenue_by_category(df)
state_rev = revenue_by_state(df)
sellers = top_sellers(df)
seasonal = seasonal_trends(df)
rfm_df = rfm_segmentation(df)
rfm_sum = rfm_summary(rfm_df)
cohort = cohort_analysis(df)
cat_perf = category_performance(df)
pareto = pareto_analysis(df)
retention = retention_analysis(df)
best_prod = best_selling_products(df)
low_prod = low_performing_products(df)
cust_dist = customer_distribution(df)
churn = churn_risk(df)
top_cust = top_customers(df)
insights = generate_insights(df, kpis, funnel, cat_rev, state_rev, rfm_sum, cohort, seasonal, pareto)
print("Analytics ready. Starting dashboard...")

# ---------------------------------------------------------------------------
# App Init
# ---------------------------------------------------------------------------
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.FLATLY],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
app.title = "E-Commerce Product Analytics Dashboard"
server = app.server


# ---------------------------------------------------------------------------
# Helper: KPI Card
# ---------------------------------------------------------------------------
def kpi_card(title, value, subtitle="", color=COLORS["primary"]):
    return dbc.Card(
        dbc.CardBody([
            html.P(title, className="text-muted mb-1", style={"fontSize": "0.8rem", "fontWeight": 500}),
            html.H3(value, style={"color": color, "fontWeight": 700, "marginBottom": "0"}),
            html.P(subtitle, className="text-muted mt-1", style={"fontSize": "0.75rem"}) if subtitle else None,
        ]),
        className="shadow-sm",
        style={"border": "none", "borderRadius": "8px", "backgroundColor": COLORS["card"]},
    )


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------
navbar = dbc.Navbar(
    dbc.Container([
        dbc.NavbarBrand(
            html.Span([
                html.I(className="bi bi-bar-chart-line me-2"),
                "E-Commerce Product Analytics Dashboard"
            ], style={"fontWeight": 700, "fontSize": "1.1rem"}),
            className="ms-2",
        ),
        dbc.Nav([
            dbc.NavItem(dbc.NavLink("Executive Summary", href="/", active="exact")),
            dbc.NavItem(dbc.NavLink("Product Analytics", href="/products", active="exact")),
            dbc.NavItem(dbc.NavLink("Customer Analytics", href="/customers", active="exact")),
            dbc.NavItem(dbc.NavLink("Revenue Analytics", href="/revenue", active="exact")),
            dbc.NavItem(dbc.NavLink("Cohort Analysis", href="/cohorts", active="exact")),
            dbc.NavItem(dbc.NavLink("Business Insights", href="/insights", active="exact")),
        ], navbar=True, className="ms-auto"),
    ], fluid=True),
    color=COLORS["primary"],
    dark=True,
    style={"boxShadow": "0 2px 4px rgba(0,0,0,0.1)"},
)

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
TABS = dbc.Tabs([
    dbc.Tab(label="Executive Summary", tab_id="tab-exec", labelClassName="fw-semibold"),
    dbc.Tab(label="Product Analytics", tab_id="tab-product", labelClassName="fw-semibold"),
    dbc.Tab(label="Customer Analytics", tab_id="tab-customer", labelClassName="fw-semibold"),
    dbc.Tab(label="Revenue Analytics", tab_id="tab-revenue", labelClassName="fw-semibold"),
    dbc.Tab(label="Cohort Analysis", tab_id="tab-cohort", labelClassName="fw-semibold"),
    dbc.Tab(label="Business Insights", tab_id="tab-insights", labelClassName="fw-semibold"),
], id="tabs", active_tab="tab-exec", className="mb-4 mt-3")


# ---------------------------------------------------------------------------
# Tab: Executive Summary
# ---------------------------------------------------------------------------
def executive_layout():
    return html.Div([
        dbc.Row([
            dbc.Col(kpi_card("Total Revenue", f"${kpis['total_revenue']:,.0f}", "", COLORS["primary"]), md=3),
            dbc.Col(kpi_card("Total Orders", f"{kpis['total_orders']:,}", "", COLORS["secondary"]), md=3),
            dbc.Col(kpi_card("Unique Customers", f"{kpis['unique_customers']:,}", "", COLORS["success"]), md=3),
            dbc.Col(kpi_card("Avg Order Value", f"${kpis['aov']:,.2f}", "", COLORS["warning"]), md=3),
        ], className="mb-4 g-3"),
        dbc.Row([
            dbc.Col(kpi_card("Repeat Customers", f"{kpis['repeat_customers']:,}", f"{kpis['repeat_purchase_rate']}% rate", COLORS["primary"]), md=3),
            dbc.Col(kpi_card("Customer LTV", f"${kpis['clv']:,.2f}", "Avg per customer", COLORS["success"]), md=3),
            dbc.Col(kpi_card(
                "Monthly Growth",
                f"{kpis['monthly_growth_pct']}%" if kpis['monthly_growth_pct'] is not None else "N/A",
                "MoM (complete months)" if kpis['monthly_growth_pct'] is not None else "Insufficient data",
                COLORS["warning"] if kpis['monthly_growth_pct'] is not None and kpis['monthly_growth_pct'] >= 0 else COLORS["danger"] if kpis['monthly_growth_pct'] is not None else COLORS["secondary"],
            ), md=3),
            dbc.Col(kpi_card("Cancellation Rate", f"{kpis['cancellation_rate']}%", f"Avg delivery: {kpis['avg_delivery_days']}d", COLORS["danger"]), md=3),
        ], className="mb-4 g-3"),
        dbc.Row([
            dbc.Col([
                dbc.Card(dbc.CardBody([
                    html.H5("Monthly Revenue Trend", className="card-title mb-3"),
                    dcc.Graph(
                        figure=go.Figure()
                        .add_trace(go.Scatter(
                            x=monthly["order_month_str"], y=monthly["revenue"],
                            mode="lines+markers", name="Revenue",
                            line=dict(color=COLORS["primary"], width=2.5),
                            fill="tozeroy", fillcolor="rgba(26,115,232,0.08)",
                        ))
                        .add_trace(go.Bar(
                            x=monthly["order_month_str"], y=monthly["orders"],
                            name="Orders", yaxis="y2",
                            marker_color=COLORS["chart_palette"][1], opacity=0.5,
                        ))
                        .update_layout(**chart_layout(
                            yaxis=dict(title="Revenue ($)"),
                            yaxis2=dict(title="Orders", overlaying="y", side="right", showgrid=False),
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                            height=380,
                        ))
                    ),
                ]), className="shadow-sm", style={"border": "none", "borderRadius": "8px"}),
            ], md=8),
            dbc.Col([
                dbc.Card(dbc.CardBody([
                    html.H5("Purchase Funnel", className="card-title mb-3"),
                    dcc.Graph(
                        figure=go.Figure(go.Funnel(
                            y=funnel["stage"], x=funnel["count"],
                            textinfo="value+percent initial",
                            marker=dict(color=[COLORS["primary"], COLORS["chart_palette"][1],
                                               COLORS["warning"], COLORS["success"]]),
                        )).update_layout(**chart_layout(height=380))
                    ),
                ]), className="shadow-sm", style={"border": "none", "borderRadius": "8px"}),
            ], md=4),
        ], className="mb-4 g-3"),
        dbc.Row([
            dbc.Col([
                dbc.Card(dbc.CardBody([
                    html.H5("Top 10 States by Revenue", className="card-title mb-3"),
                    html.P("Item-level revenue by customer state", className="text-muted", style={"fontSize": "0.75rem", "marginTop": "-0.5rem"}),
                    dcc.Graph(
                        figure=px.bar(
                            state_rev.head(10), x="customer_state", y="revenue",
                            color="revenue", color_continuous_scale="Blues",
                            labels={"customer_state": "State", "revenue": "Revenue ($)"},
                        ).update_layout(**chart_layout(height=340, showlegend=False))
                    ),
                ]), className="shadow-sm", style={"border": "none", "borderRadius": "8px"}),
            ], md=6),
            dbc.Col([
                dbc.Card(dbc.CardBody([
                    html.H5("Top 10 Categories by Revenue", className="card-title mb-3"),
                    html.P("Item-level revenue (sum of all items in each category)", className="text-muted", style={"fontSize": "0.75rem", "marginTop": "-0.5rem"}),
                    dcc.Graph(
                        figure=px.bar(
                            cat_rev.head(10), x="revenue", y="product_category_name_english",
                            orientation="h", color="revenue",
                            color_continuous_scale="Tealgrn",
                            labels={"product_category_name_english": "Category", "revenue": "Revenue ($)"},
                        ).update_layout(**chart_layout(height=340, showlegend=False, yaxis=dict(autorange="reversed")))
                    ),
                ]), className="shadow-sm", style={"border": "none", "borderRadius": "8px"}),
            ], md=6),
        ]),
    ])


# ---------------------------------------------------------------------------
# Tab: Product Analytics
# ---------------------------------------------------------------------------
def product_layout():
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card(dbc.CardBody([
                    html.H5("Revenue by Category", className="card-title mb-3"),
                    html.P("Item-level revenue distribution (top 20 categories)", className="text-muted", style={"fontSize": "0.75rem", "marginTop": "-0.5rem"}),
                    dcc.Graph(
                        figure=px.treemap(
                            cat_rev.head(20), path=["product_category_name_english"],
                            values="revenue", color="revenue_share_pct",
                            color_continuous_scale="Blues",
                            labels={"revenue": "Revenue ($)", "revenue_share_pct": "Share %"},
                        ).update_layout(**chart_layout(height=450))
                    ),
                ]), className="shadow-sm", style={"border": "none", "borderRadius": "8px"}),
            ], md=6),
            dbc.Col([
                dbc.Card(dbc.CardBody([
                    html.H5("Pareto (80/20) Analysis", className="card-title mb-3"),
                    dcc.Graph(
                        figure=go.Figure()
                        .add_trace(go.Bar(
                            x=pareto["categories_pct"], y=pareto["revenue"],
                            name="Revenue", marker_color=COLORS["primary"], opacity=0.7,
                        ))
                        .add_trace(go.Scatter(
                            x=pareto["categories_pct"], y=pareto["cumulative_revenue_pct"],
                            name="Cumulative %", mode="lines",
                            line=dict(color=COLORS["danger"], width=2.5, dash="dot"),
                            yaxis="y2",
                        ))
                        .add_hline(y=80, line_dash="dash", line_color=COLORS["warning"],
                                   annotation_text="80% line", yref="y2")
                        .update_layout(**chart_layout(
                            height=450,
                            xaxis=dict(title="% of Categories"),
                            yaxis=dict(title="Revenue ($)"),
                            yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0, 105], showgrid=False),
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        ))
                    ),
                ]), className="shadow-sm", style={"border": "none", "borderRadius": "8px"}),
            ], md=6),
        ], className="mb-4 g-3"),
        dbc.Row([
            dbc.Col([
                dbc.Card(dbc.CardBody([
                    html.H5("Best Selling Products (Top 15)", className="card-title mb-3"),
                    dash_table.DataTable(
                        data=best_prod.to_dict("records"),
                        columns=[
                            {"name": "Category", "id": "product_category_name_english"},
                            {"name": "Revenue", "id": "revenue", "type": "numeric", "format": {"specifier": "$,.0f"}},
                            {"name": "Units", "id": "units_sold"},
                            {"name": "Orders", "id": "orders"},
                            {"name": "Avg Price", "id": "avg_price", "type": "numeric", "format": {"specifier": "$,.2f"}},
                        ],
                        style_table={"overflowX": "auto"},
                        style_header={"backgroundColor": COLORS["primary"], "color": "white", "fontWeight": "bold"},
                        style_cell={"textAlign": "left", "padding": "10px", "fontSize": "0.85rem"},
                        style_data_conditional=[{"if": {"row_index": "odd"}, "backgroundColor": "#F8F9FA"}],
                        page_size=15,
                    ),
                ]), className="shadow-sm", style={"border": "none", "borderRadius": "8px"}),
            ], md=6),
            dbc.Col([
                dbc.Card(dbc.CardBody([
                    html.H5("Low Performing Products (5+ orders)", className="card-title mb-3"),
                    dash_table.DataTable(
                        data=low_prod.to_dict("records"),
                        columns=[
                            {"name": "Category", "id": "product_category_name_english"},
                            {"name": "Revenue", "id": "revenue", "type": "numeric", "format": {"specifier": "$,.0f"}},
                            {"name": "Orders", "id": "orders"},
                            {"name": "Avg Price", "id": "avg_price", "type": "numeric", "format": {"specifier": "$,.2f"}},
                            {"name": "Avg Review", "id": "avg_review", "type": "numeric", "format": {"specifier": ".2f"}},
                        ],
                        style_table={"overflowX": "auto"},
                        style_header={"backgroundColor": COLORS["danger"], "color": "white", "fontWeight": "bold"},
                        style_cell={"textAlign": "left", "padding": "10px", "fontSize": "0.85rem"},
                        style_data_conditional=[{"if": {"row_index": "odd"}, "backgroundColor": "#F8F9FA"}],
                        page_size=15,
                    ),
                ]), className="shadow-sm", style={"border": "none", "borderRadius": "8px"}),
            ], md=6),
        ], className="mb-4 g-3"),
        dbc.Row([
            dbc.Col([
                dbc.Card(dbc.CardBody([
                    html.H5("Seasonal Revenue Trends", className="card-title mb-3"),
                    dcc.Graph(
                        figure=px.line(
                            seasonal, x="month_name", y="revenue", color="order_year",
                            labels={"month_name": "Month", "revenue": "Revenue ($)", "order_year": "Year"},
                            color_discrete_sequence=COLORS["chart_palette"],
                        ).update_layout(**chart_layout(height=380))
                    ),
                ]), className="shadow-sm", style={"border": "none", "borderRadius": "8px"}),
            ], md=12),
        ]),
    ])


# ---------------------------------------------------------------------------
# Tab: Customer Analytics
# ---------------------------------------------------------------------------
def customer_layout():
    churn_at_risk = int(churn.loc[churn["risk_level"] == "At Risk", "customers"].values[0]) if len(churn.loc[churn["risk_level"] == "At Risk"]) else 0
    churn_active = int(churn.loc[churn["risk_level"] == "Active", "customers"].values[0]) if len(churn.loc[churn["risk_level"] == "Active"]) else 0

    return html.Div([
        dbc.Row([
            dbc.Col(kpi_card("Repeat Customers", f"{kpis['repeat_customers']:,}", f"{kpis['repeat_purchase_rate']}% rate", COLORS["primary"]), md=3),
            dbc.Col(kpi_card("Churn Risk", f"{churn_at_risk:,}", "Customers inactive 90+ days", COLORS["danger"]), md=3),
            dbc.Col(kpi_card("Avg CLV", f"${kpis['clv']:,.2f}", "Per customer", COLORS["success"]), md=3),
            dbc.Col(kpi_card("Active Customers", f"{churn_active:,}", "Purchased in last 30 days", COLORS["warning"]), md=3),
        ], className="mb-4 g-3"),
        dbc.Row([
            dbc.Col([
                dbc.Card(dbc.CardBody([
                    html.H5("RFM Segment Distribution", className="card-title mb-3"),
                    dcc.Graph(
                        figure=px.bar(
                            rfm_sum, x="segment", y="customers", color="segment",
                            labels={"segment": "Segment", "customers": "Customers"},
                            color_discrete_sequence=COLORS["chart_palette"],
                        ).update_layout(**chart_layout(height=360, showlegend=False, xaxis=dict(categoryorder="total descending")))
                    ),
                ]), className="shadow-sm", style={"border": "none", "borderRadius": "8px"}),
            ], md=6),
            dbc.Col([
                dbc.Card(dbc.CardBody([
                    html.H5("Revenue by RFM Segment", className="card-title mb-3"),
                    dcc.Graph(
                        figure=px.pie(
                            rfm_sum, names="segment", values="total_revenue",
                            color_discrete_sequence=COLORS["chart_palette"],
                            hole=0.4,
                        ).update_layout(**chart_layout(height=360))
                    ),
                ]), className="shadow-sm", style={"border": "none", "borderRadius": "8px"}),
            ], md=6),
        ], className="mb-4 g-3"),
        dbc.Row([
            dbc.Col([
                dbc.Card(dbc.CardBody([
                    html.H5("Customer Churn Risk", className="card-title mb-3"),
                    dcc.Graph(
                        figure=px.bar(
                            churn, x="risk_level", y="customers", color="risk_level",
                            text="share_pct",
                            labels={"risk_level": "Risk Level", "customers": "Customers", "share_pct": "Share %"},
                            color_discrete_map={"Active": COLORS["success"], "Warm": COLORS["warning"],
                                                "Cooling": COLORS["chart_palette"][5], "At Risk": COLORS["danger"]},
                        ).update_layout(**chart_layout(height=360, showlegend=False))
                    ),
                ]), className="shadow-sm", style={"border": "none", "borderRadius": "8px"}),
            ], md=6),
            dbc.Col([
                dbc.Card(dbc.CardBody([
                    html.H5("Customer Order Distribution", className="card-title mb-3"),
                    dcc.Graph(
                        figure=px.bar(
                            cust_dist, x="order_count", y="num_customers",
                            labels={"order_count": "Orders per Customer", "num_customers": "Number of Customers"},
                            color_discrete_sequence=[COLORS["primary"]],
                        ).update_layout(**chart_layout(height=360))
                    ),
                ]), className="shadow-sm", style={"border": "none", "borderRadius": "8px"}),
            ], md=6),
        ], className="mb-4 g-3"),
        dbc.Row([
            dbc.Col([
                dbc.Card(dbc.CardBody([
                    html.H5("RFM Segment Details", className="card-title mb-3"),
                    dash_table.DataTable(
                        data=rfm_sum.to_dict("records"),
                        columns=[
                            {"name": "Segment", "id": "segment"},
                            {"name": "Customers", "id": "customers"},
                            {"name": "Share %", "id": "customer_share_pct"},
                            {"name": "Avg Recency (d)", "id": "avg_recency"},
                            {"name": "Avg Frequency", "id": "avg_frequency"},
                            {"name": "Avg Monetary", "id": "avg_monetary", "type": "numeric", "format": {"specifier": "$,.2f"}},
                            {"name": "Revenue", "id": "total_revenue", "type": "numeric", "format": {"specifier": "$,.0f"}},
                            {"name": "Rev Share %", "id": "revenue_share_pct"},
                        ],
                        style_table={"overflowX": "auto"},
                        style_header={"backgroundColor": COLORS["primary"], "color": "white", "fontWeight": "bold"},
                        style_cell={"textAlign": "left", "padding": "10px", "fontSize": "0.85rem"},
                        style_data_conditional=[{"if": {"row_index": "odd"}, "backgroundColor": "#F8F9FA"}],
                    ),
                ]), className="shadow-sm", style={"border": "none", "borderRadius": "8px"}),
            ], md=12),
        ]),
    ])


# ---------------------------------------------------------------------------
# Tab: Revenue Analytics
# ---------------------------------------------------------------------------
def revenue_layout():
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card(dbc.CardBody([
                    html.H5("Monthly Revenue & AOV", className="card-title mb-3"),
                    dcc.Graph(
                        figure=go.Figure()
                        .add_trace(go.Bar(
                            x=monthly["order_month_str"], y=monthly["revenue"],
                            name="Revenue", marker_color=COLORS["primary"], opacity=0.75,
                        ))
                        .add_trace(go.Scatter(
                            x=monthly["order_month_str"], y=monthly["aov"],
                            name="AOV", mode="lines+markers",
                            line=dict(color=COLORS["danger"], width=2.5),
                            yaxis="y2",
                        ))
                        .update_layout(**chart_layout(
                            height=400,
                            yaxis=dict(title="Revenue ($)"),
                            yaxis2=dict(title="AOV ($)", overlaying="y", side="right", showgrid=False),
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        ))
                    ),
                ]), className="shadow-sm", style={"border": "none", "borderRadius": "8px"}),
            ], md=12),
        ], className="mb-4"),
        dbc.Row([
            dbc.Col([
                dbc.Card(dbc.CardBody([
                    html.H5("Revenue by State (Top 15)", className="card-title mb-3"),
                    dcc.Graph(
                        figure=px.bar(
                            state_rev.head(15), x="customer_state", y="revenue",
                            color="aov", color_continuous_scale="Teal",
                            labels={"customer_state": "State", "revenue": "Revenue ($)", "aov": "AOV ($)"},
                        ).update_layout(**chart_layout(height=450))
                    ),
                ]), className="shadow-sm", style={"border": "none", "borderRadius": "8px"}),
            ], md=6),
            dbc.Col([
                dbc.Card(dbc.CardBody([
                    html.H5("Revenue by State (Horizontal)", className="card-title mb-3"),
                    dcc.Graph(
                        figure=px.bar(
                            state_rev.head(15), x="revenue", y="customer_state",
                            orientation="h", color="revenue",
                            color_continuous_scale="Blues",
                            labels={"customer_state": "State", "revenue": "Revenue ($)"},
                        ).update_layout(**chart_layout(height=450, yaxis=dict(autorange="reversed")))
                    ),
                ]), className="shadow-sm", style={"border": "none", "borderRadius": "8px"}),
            ], md=6),
        ], className="mb-4 g-3"),
        dbc.Row([
            dbc.Col([
                dbc.Card(dbc.CardBody([
                    html.H5("Top 20 Sellers by Revenue", className="card-title mb-3"),
                    dcc.Graph(
                        figure=px.bar(
                            sellers.head(20), x="revenue", y="seller_id",
                            orientation="h", color="revenue",
                            color_continuous_scale="Greens",
                            labels={"seller_id": "Seller", "revenue": "Revenue ($)"},
                        ).update_layout(**chart_layout(height=450, yaxis=dict(autorange="reversed")))
                    ),
                ]), className="shadow-sm", style={"border": "none", "borderRadius": "8px"}),
            ], md=6),
            dbc.Col([
                dbc.Card(dbc.CardBody([
                    html.H5("MoM Revenue Growth", className="card-title mb-3"),
                    dcc.Graph(
                        figure=go.Figure(go.Bar(
                            x=monthly["order_month_str"],
                            y=monthly["revenue_mom_pct"].fillna(0),
                            marker_color=[COLORS["chart_palette"][1] if (pd.notna(v) and v >= 0) else COLORS["danger"] if pd.notna(v) else COLORS["border"]
                                          for v in monthly["revenue_mom_pct"]],
                            text=[f"{v:.1f}%" if pd.notna(v) else "" for v in monthly["revenue_mom_pct"]],
                            textposition="outside",
                        )).update_layout(**chart_layout(height=450, yaxis=dict(title="MoM Growth %")))
                    ),
                ]), className="shadow-sm", style={"border": "none", "borderRadius": "8px"}),
            ], md=6),
        ]),
    ])


# ---------------------------------------------------------------------------
# Tab: Cohort Analysis
# ---------------------------------------------------------------------------
def cohort_layout():
    cohort_cols = min(13, cohort.shape[1])
    cohort_slice = cohort.iloc[:, :cohort_cols]

    # Replace NaN with NaN for plotting; use custom text to show "-" for NaN cells
    z_vals = cohort_slice.values.copy()
    text_vals = np.where(np.isnan(z_vals), "-", np.round(z_vals, 1).astype(str))

    fig_heat = go.Figure(go.Heatmap(
        z=z_vals,
        x=[f"Month {i}" for i in range(cohort_cols)],
        y=[str(idx) for idx in cohort_slice.index],
        colorscale=[[0, "#F8F9FA"], [0.2, "#E3F2FD"], [0.4, "#BBDEFB"], [0.6, "#64B5F6"], [0.8, "#1E88E5"], [1.0, "#0D47A1"]],
        zmin=0, zmax=100,
        text=text_vals,
        texttemplate="%{text}",
        hovertemplate="Cohort: %{y}<br>Month %{x}<br>Retention: %{z:.1f}%<extra></extra>",
        showscale=True,
        colorbar=dict(title="Retention %"),
    ))
    fig_heat.update_layout(**chart_layout(
        height=max(500, len(cohort) * 28),
        xaxis=dict(title="Months Since First Purchase"),
        yaxis=dict(title="Cohort Month", autorange="reversed"),
        title="Customer Retention Heatmap",
    ))

    def get_cohort_trace(col):
        if col in cohort.columns:
            return cohort[col].fillna(0).values
        return np.zeros(len(cohort))

    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card(dbc.CardBody([
                    html.H5("Retention Matrix", className="card-title mb-3"),
                    dcc.Graph(figure=fig_heat),
                ]), className="shadow-sm", style={"border": "none", "borderRadius": "8px"}),
            ], md=12),
        ], className="mb-4"),
        dbc.Row([
            dbc.Col([
                dbc.Card(dbc.CardBody([
                    html.H5("Retention Over Time", className="card-title mb-3"),
                    dcc.Graph(
                        figure=go.Figure()
                        .add_trace(go.Scatter(
                            x=[str(idx) for idx in cohort.index],
                            y=get_cohort_trace(1),
                            mode="lines+markers", name="Month 1 Retention",
                            line=dict(color=COLORS["primary"], width=2),
                        ))
                        .add_trace(go.Scatter(
                            x=[str(idx) for idx in cohort.index],
                            y=get_cohort_trace(3),
                            mode="lines+markers", name="Month 3 Retention",
                            line=dict(color=COLORS["warning"], width=2),
                        ))
                        .add_trace(go.Scatter(
                            x=[str(idx) for idx in cohort.index],
                            y=get_cohort_trace(6),
                            mode="lines+markers", name="Month 6 Retention",
                            line=dict(color=COLORS["danger"], width=2),
                        ))
                        .update_layout(**chart_layout(height=400, yaxis=dict(title="Retention %")))
                    ),
                ]), className="shadow-sm", style={"border": "none", "borderRadius": "8px"}),
            ], md=6),
            dbc.Col([
                dbc.Card(dbc.CardBody([
                    html.H5("Customer Retention Curve", className="card-title mb-3"),
                    dcc.Graph(
                        figure=px.line(
                            retention, x="months_since_first", y="retention_pct",
                            labels={"months_since_first": "Months Since First Purchase", "retention_pct": "Retention %"},
                        ).update_layout(**chart_layout(height=400, yaxis=dict(title="Retention %")))
                    ),
                ]), className="shadow-sm", style={"border": "none", "borderRadius": "8px"}),
            ], md=6),
        ]),
    ])


# ---------------------------------------------------------------------------
# Tab: Business Insights
# ---------------------------------------------------------------------------
def insights_layout():
    insight_cards = []
    category_colors = {
        "Revenue Concentration": COLORS["primary"],
        "Funnel Optimization": COLORS["danger"],
        "Customer Value": COLORS["success"],
        "Retention Risk": COLORS["warning"],
        "Geographic Distribution": COLORS["chart_palette"][5],
        "Operations": COLORS["chart_palette"][7],
        "Growth": COLORS["success"],
        "Portfolio Strategy": COLORS["chart_palette"][8],
        "Seasonal Planning": COLORS["chart_palette"][9],
    }
    for ins in insights:
        cat = ins["category"]
        color = category_colors.get(cat, COLORS["primary"])
        insight_cards.append(
            dbc.Card(
                dbc.CardBody([
                    dbc.Badge(cat, style={"backgroundColor": color, "fontSize": "0.7rem", "fontWeight": 600, "color": "white"}),
                    html.H5(ins["title"], className="card-title mt-2", style={"fontWeight": 600}),
                    html.P(ins["insight"], className="text-muted", style={"fontSize": "0.9rem"}),
                    html.Hr(style={"borderColor": COLORS["border"]}),
                    html.P([
                        html.Strong("Recommendation: ", style={"color": COLORS["primary"]}),
                        ins["recommendation"],
                    ], style={"fontSize": "0.88rem"}),
                ]),
                className="shadow-sm mb-3",
                style={"border": "none", "borderRadius": "8px", "borderLeft": f"4px solid {color}"},
            )
        )

    rows = []
    for i in range(0, len(insight_cards), 2):
        pair = insight_cards[i:i+2]
        rows.append(dbc.Row([dbc.Col(card, md=6) for card in pair], className="mb-3 g-3"))

    return html.Div([
        html.H4("Data-Driven Business Insights", className="mb-4", style={"fontWeight": 600, "color": COLORS["text"]}),
        *rows,
    ])


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
tab_content = html.Div(id="tab-content")

app.layout = html.Div([
    dcc.Location(id="url"),
    navbar,
    dbc.Container([
        TABS,
        tab_content,
    ], fluid=True, className="px-4", style={"backgroundColor": COLORS["bg"], "minHeight": "100vh"}),
], style={"backgroundColor": COLORS["bg"]})


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------
@app.callback(
    Output("tab-content", "children"),
    Input("tabs", "active_tab"),
)
def render_tab(tab):
    if tab == "tab-exec":
        return executive_layout()
    elif tab == "tab-product":
        return product_layout()
    elif tab == "tab-customer":
        return customer_layout()
    elif tab == "tab-revenue":
        return revenue_layout()
    elif tab == "tab-cohort":
        return cohort_layout()
    elif tab == "tab-insights":
        return insights_layout()
    return html.Div("Select a tab")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
