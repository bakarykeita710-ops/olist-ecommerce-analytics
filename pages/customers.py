

import dash
from dash import html, dcc, Input, Output, callback
import pandas as pd
import plotly.express as px

from src.data_loader import load_data
from src.components import metric_card


dash.register_page(
    __name__,
    path="/customers",
    name="Customer Insights",
    order=3
)

orders, order_items, geolocation = load_data()

orders["order_purchase_timestamp"] = pd.to_datetime(
    orders["order_purchase_timestamp"],
    errors="coerce"
)

# Build one record per unique customer
customer_summary = (
    orders.dropna(subset=["customer_unique_id"])
    .groupby("customer_unique_id")
    .agg(
        total_orders=("order_id", "nunique"),
        total_spent=("total_product_value", "sum"),
        customer_state=("customer_state", "first"),
        average_review_score=("average_review_score", "mean")
    )
    .reset_index()
)

customer_summary["customer_type"] = customer_summary[
    "total_orders"
].apply(
    lambda count: (
        "Repeat Customer" if count > 1
        else "One-Time Customer"
    )
)

states = sorted(
    customer_summary["customer_state"].dropna().unique()
)


layout = html.Div(
    [
        html.Div(
            [
                html.P("CUSTOMER BEHAVIOUR", className="eyebrow"),
                html.H1("Customer Insights", className="page-title"),
                html.P(
                    "Understand customer loyalty, purchasing "
                    "behaviour and satisfaction across Brazil.",
                    className="page-subtitle"
                )
            ],
            className="page-heading accent-orange"
        ),

        html.Div(
            [
                html.Div(
                    [
                        html.Label(
                            "Customer State",
                            className="filter-label"
                        ),
                        dcc.Dropdown(
                            id="customer-state-filter",
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
            id="customer-kpis",
            className="metric-grid"
        ),

        html.Div(
            [
                html.Div(
                    dcc.Graph(
                        id="customer-type-chart",
                        config={"displayModeBar": False}
                    ),
                    className="chart-card"
                ),

                html.Div(
                    dcc.Graph(
                        id="customer-state-chart",
                        config={"displayModeBar": False}
                    ),
                    className="chart-card"
                ),

                html.Div(
                    dcc.Graph(
                        id="customer-review-chart",
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


@callback(
    Output("customer-kpis", "children"),
    Output("customer-type-chart", "figure"),
    Output("customer-state-chart", "figure"),
    Output("customer-review-chart", "figure"),
    Input("customer-state-filter", "value")
)
def update_customer_dashboard(selected_state):

    if selected_state == "ALL":
        filtered_customers = customer_summary.copy()
        filtered_orders = orders.copy()
    else:
        filtered_customers = customer_summary[
            customer_summary["customer_state"] == selected_state
        ]

        filtered_orders = orders[
            orders["customer_state"] == selected_state
        ]

    total_customers = len(filtered_customers)

    repeat_customers = (
        filtered_customers["customer_type"] == "Repeat Customer"
    ).sum()

    repeat_rate = (
        repeat_customers / total_customers * 100
        if total_customers else 0
    )

    average_rating = filtered_orders[
        "average_review_score"
    ].mean()

    rating_text = (
        f"{average_rating:.2f} / 5"
        if pd.notna(average_rating) else "N/A"
    )

    kpis = [
        metric_card(
            "Unique Customers",
            f"{total_customers:,.0f}",
            "Distinct customer identities",
            "orange"
        ),

        metric_card(
            "One-Time Customers",
            f"{(filtered_customers['customer_type'] == 'One-Time Customer').sum():,.0f}",
            "Customers with one recorded order",
            "blue"
        ),

        metric_card(
            "Repeat Customer Rate",
            f"{repeat_rate:.2f}%",
            "Customers with multiple recorded orders",
            "purple"
        ),

        metric_card(
            "Average Review",
            rating_text,
            "Average score per reviewed order",
            "teal"
        )
    ]

    # One-time vs repeat customers
    type_counts = (
        filtered_customers["customer_type"]
        .value_counts()
        .reindex(
            ["One-Time Customer", "Repeat Customer"],
            fill_value=0
        )
        .rename_axis("customer_type")
        .reset_index(name="total_customers")
    )

    type_fig = px.bar(
        type_counts,
        x="customer_type",
        y="total_customers",
        title="One-Time vs Repeat Customers",
        color="customer_type",
        color_discrete_sequence=["#F0A15C", "#E36D86"]
    )

    type_fig.update_layout(
        template="plotly_white",
        showlegend=False,
        height=370,
        font=dict(size=13),
        title_font=dict(size=19)
    )

    # Customer distribution by state
    state_data = (
        filtered_customers.groupby("customer_state")
        .agg(
            total_customers=("customer_unique_id", "nunique")
        )
        .reset_index()
        .nlargest(10, "total_customers")
        .sort_values("total_customers")
    )

    state_fig = px.bar(
        state_data,
        x="total_customers",
        y="customer_state",
        orientation="h",
        title="Top 10 States by Unique Customers",
        color_discrete_sequence=["#E98B40"]
    )

    state_fig.update_layout(
        template="plotly_white",
        height=370,
        font=dict(size=13),
        title_font=dict(size=19)
    )

    # Customer review score distribution
    review_data = filtered_orders.dropna(
        subset=["average_review_score"]
    )

    review_fig = px.histogram(
        review_data,
        x="average_review_score",
        nbins=10,
        title="Distribution of Customer Review Scores",
        labels={
            "average_review_score": "Average Review Score"
        },
        color_discrete_sequence=["#D889A0"]
    )

    review_fig.update_layout(
        template="plotly_white",
        height=350,
        font=dict(size=13),
        title_font=dict(size=19)
    )

    return kpis, type_fig, state_fig, review_fig
