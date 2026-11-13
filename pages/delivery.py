
import dash
from dash import html, dcc, Input, Output, callback
import pandas as pd
import numpy as np
import plotly.express as px

from src.data_loader import load_data
from src.components import metric_card


dash.register_page(
    __name__,
    path="/delivery",
    name="Delivery & Logistics",
    order=5
)

orders, order_items, geolocation = load_data()


# ---------------------------------
# Prepare delivered orders
# ---------------------------------

date_columns = [
    "order_purchase_timestamp",
    "order_delivered_customer_date",
    "order_estimated_delivery_date"
]

for column in date_columns:
    orders[column] = pd.to_datetime(
        orders[column],
        errors="coerce"
    )

delivered_orders = orders[
    orders["order_status"] == "delivered"
].copy()

valid_deliveries = delivered_orders.dropna(
    subset=date_columns
).copy()


# Exclude known delivery date inconsistencies
if "delivery_date_issue" in valid_deliveries.columns:

    issue = valid_deliveries["delivery_date_issue"]

    if not pd.api.types.is_bool_dtype(issue):
        issue = (
            issue.astype(str)
            .str.lower()
            .isin(["true", "1", "yes"])
        )
    else:
        issue = issue.fillna(False)

    valid_deliveries = valid_deliveries[~issue].copy()


# Calculate delivery time and delay
valid_deliveries["delivery_time_days"] = (
    valid_deliveries["order_delivered_customer_date"] -
    valid_deliveries["order_purchase_timestamp"]
).dt.total_seconds() / 86400

valid_deliveries["delivery_delay_days"] = (
    valid_deliveries["order_delivered_customer_date"] -
    valid_deliveries["order_estimated_delivery_date"]
).dt.total_seconds() / 86400


# Remove impossible negative delivery durations
valid_deliveries = valid_deliveries[
    valid_deliveries["delivery_time_days"] >= 0
].copy()


# Classify delivery performance
valid_deliveries["delivery_performance"] = np.where(
    valid_deliveries["delivery_delay_days"] > 0,
    "Late",
    np.where(
        valid_deliveries["delivery_delay_days"] < 0,
        "Early",
        "On Time"
    )
)


states = sorted(
    valid_deliveries["customer_state"].dropna().unique()
)


# ---------------------------------
# Layout
# ---------------------------------

layout = html.Div(
    [
        html.Div(
            [
                html.P("LOGISTICS AND FULFILMENT", className="eyebrow"),
                html.H1("Delivery & Logistics", className="page-title"),
                html.P(
                    "Evaluate delivery times, late orders and "
                    "logistics performance across Brazilian states.",
                    className="page-subtitle"
                )
            ],
            className="page-heading accent-navy"
        ),

        html.Div(
            [
                html.Div(
                    [
                        html.Label(
                            "Filter by Customer State",
                            className="filter-label"
                        ),
                        dcc.Dropdown(
                            id="delivery-state-filter",
                            options=[
                                {"label": "All States", "value": "ALL"}
                            ] + [
                                {"label": state, "value": state}
                                for state in states
                            ],
                            value="ALL",
                            clearable=False
                        )
                    ],
                    className="filter-control"
                )
            ],
            className="filter-row"
        ),

        html.Div(
            id="delivery-kpis",
            className="metric-grid"
        ),

        html.Div(
            [
                html.Div(
                    dcc.Graph(
                        id="delivery-time-chart",
                        config={"displayModeBar": False}
                    ),
                    className="chart-card"
                ),

                html.Div(
                    dcc.Graph(
                        id="delivery-performance-chart",
                        config={"displayModeBar": False}
                    ),
                    className="chart-card"
                ),

                html.Div(
                    dcc.Graph(
                        id="delivery-state-chart",
                        config={"displayModeBar": False}
                    ),
                    className="chart-card chart-wide"
                )
            ],
            className="chart-grid"
        )
    ],
    className="dashboard-page"
)


# ---------------------------------
# Interactive callback
# ---------------------------------

@callback(
    Output("delivery-kpis", "children"),
    Output("delivery-time-chart", "figure"),
    Output("delivery-performance-chart", "figure"),
    Output("delivery-state-chart", "figure"),
    Input("delivery-state-filter", "value")
)
def update_delivery_dashboard(selected_state):

    if selected_state == "ALL":
        filtered = valid_deliveries.copy()
    else:
        filtered = valid_deliveries[
            valid_deliveries["customer_state"] == selected_state
        ].copy()

    total_delivered = len(filtered)

    average_delivery = filtered[
        "delivery_time_days"
    ].mean()

    average_delay = filtered[
        "delivery_delay_days"
    ].mean()

    late_rate = (
        (filtered["delivery_delay_days"] > 0).mean() * 100
        if total_delivered else 0
    )

    average_delivery_text = (
        f"{average_delivery:.1f} days"
        if pd.notna(average_delivery) else "N/A"
    )

    average_delay_text = (
        f"{average_delay:.1f} days"
        if pd.notna(average_delay) else "N/A"
    )

    kpis = [
        metric_card(
            "Valid Delivered Orders",
            f"{total_delivered:,.0f}",
            "Orders with valid delivery dates",
            "blue"
        ),

        metric_card(
            "Average Delivery Time",
            average_delivery_text,
            "From purchase to customer delivery",
            "teal"
        ),

        metric_card(
            "Late Delivery Rate",
            f"{late_rate:.2f}%",
            "Percentage delivered after estimate",
            "orange"
        ),

        metric_card(
            "Average Delay vs Estimate",
            average_delay_text,
            "Positive means later than estimated",
            "purple"
        )
    ]

    # Delivery time distribution
    time_fig = px.histogram(
        filtered,
        x="delivery_time_days",
        nbins=30,
        title="Distribution of Delivery Time",
        labels={
            "delivery_time_days": "Delivery Time (Days)"
        },
        color_discrete_sequence=["#348EAA"]
    )

    time_fig.update_layout(
        template="plotly_white",
        height=380,
        font=dict(size=13),
        title_font=dict(size=19)
    )

    # Early, on-time and late deliveries
    performance_data = (
        filtered["delivery_performance"]
        .value_counts()
        .rename_axis("performance")
        .reset_index(name="total_orders")
    )

    performance_fig = px.pie(
        performance_data,
        names="performance",
        values="total_orders",
        hole=0.60,
        title="Delivery Performance Distribution",
        color="performance",
        color_discrete_map={
            "Early": "#20A69A",
            "On Time": "#6A83D5",
            "Late": "#E9845B"
        }
    )

    performance_fig.update_layout(
        template="plotly_white",
        height=380,
        font=dict(size=13),
        title_font=dict(size=19)
    )

    # Delivery performance across states
    state_data = (
        valid_deliveries.groupby("customer_state")
        .agg(
            total_orders=("order_id", "nunique"),
            average_delivery_days=("delivery_time_days", "mean"),
            late_orders=(
                "delivery_delay_days",
                lambda values: (values > 0).sum()
            )
        )
        .reset_index()
    )

    state_data["late_rate"] = (
        state_data["late_orders"] /
        state_data["total_orders"] * 100
    )

    state_data = (
        state_data.nlargest(10, "total_orders")
        .sort_values("late_rate")
    )

    state_fig = px.bar(
        state_data,
        x="late_rate",
        y="customer_state",
        orientation="h",
        title="Delivery Late Rate — Top 10 States by Order Volume",
        labels={
            "late_rate": "Late Delivery Rate (%)",
            "customer_state": "Customer State"
        },
        color_discrete_sequence=["#315B9A"]
    )

    state_fig.update_layout(
        template="plotly_white",
        height=430,
        font=dict(size=13),
        title_font=dict(size=19)
    )

    return kpis, time_fig, performance_fig, state_fig
