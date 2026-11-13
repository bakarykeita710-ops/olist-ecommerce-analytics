
import dash
from dash import html, dcc, Input, Output, callback
import pandas as pd
import plotly.express as px

from src.data_loader import load_data
from src.components import metric_card


dash.register_page(
    __name__,
    path="/sales",
    name="Sales Performance",
    order=1
)

orders, order_items, geolocation = load_data()

orders["order_purchase_timestamp"] = pd.to_datetime(
    orders["order_purchase_timestamp"],
    errors="coerce"
)

orders["total_product_value"] = pd.to_numeric(
    orders["total_product_value"],
    errors="coerce"
)

orders["total_freight_value"] = pd.to_numeric(
    orders["total_freight_value"],
    errors="coerce"
)

min_date = orders["order_purchase_timestamp"].min().date().isoformat()
max_date = orders["order_purchase_timestamp"].max().date().isoformat()

statuses = sorted(orders["order_status"].dropna().unique())


def make_sales_charts(data):

    monthly = data.dropna(
        subset=["order_purchase_timestamp"]
    ).copy()

    monthly["month"] = (
        monthly["order_purchase_timestamp"]
        .dt.to_period("M")
        .astype(str)
    )

    monthly = (
        monthly.groupby("month")
        .agg(
            product_sales=("total_product_value", "sum"),
            orders=("order_id", "nunique")
        )
        .reset_index()
    )

    sales_chart = px.area(
        monthly,
        x="month",
        y="product_sales",
        markers=True,
        title="Monthly Product Sales",
        labels={
            "month": "Month",
            "product_sales": "Product Sales (R$)"
        },
        color_discrete_sequence=["#11998E"]
    )

    sales_chart.update_layout(
        template="plotly_white",
        height=370,
        font=dict(size=13, color="#334155"),
        title_font=dict(size=19, color="#202B3C"),
        margin=dict(l=30, r=25, t=65, b=40)
    )

    order_chart = px.bar(
        monthly,
        x="month",
        y="orders",
        title="Monthly Order Volume",
        labels={
            "month": "Month",
            "orders": "Number of Orders"
        },
        color_discrete_sequence=["#62B6A9"]
    )

    order_chart.update_layout(
        template="plotly_white",
        height=370,
        font=dict(size=13, color="#334155"),
        title_font=dict(size=19, color="#202B3C"),
        margin=dict(l=30, r=25, t=65, b=40)
    )

    return sales_chart, order_chart


layout = html.Div(
    [
        html.Div(
            [
                html.P("REVENUE AND GROWTH", className="eyebrow"),
                html.H1("Sales Performance", className="page-title"),
                html.P(
                    "Monitor product sales, order volume and average "
                    "product value over time.",
                    className="page-subtitle"
                )
            ],
            className="page-heading accent-teal"
        ),

        html.Div(
            [
                html.Div(
                    [
                        html.Label(
                            "Purchase Date Range",
                            className="filter-label"
                        ),
                        dcc.DatePickerRange(
                            id="sales-date-range",
                            start_date=min_date,
                            end_date=max_date,
                            min_date_allowed=min_date,
                            max_date_allowed=max_date,
                            display_format="DD MMM YYYY"
                        )
                    ],
                    className="filter-control"
                ),

                html.Div(
                    [
                        html.Label(
                            "Order Status",
                            className="filter-label"
                        ),
                        dcc.Dropdown(
                            id="sales-status-filter",
                            options=[
                                {"label": s.title(), "value": s}
                                for s in statuses
                            ],
                            value=statuses,
                            multi=True,
                            placeholder="Choose order statuses"
                        )
                    ],
                    className="filter-control"
                )
            ],
            className="filter-row"
        ),

        html.Div(
            id="sales-kpis",
            className="metric-grid"
        ),

        html.Div(
            [
                html.Div(
                    dcc.Graph(
                        id="sales-monthly-chart",
                        config={"displayModeBar": False}
                    ),
                    className="chart-card"
                ),

                html.Div(
                    dcc.Graph(
                        id="sales-volume-chart",
                        config={"displayModeBar": False}
                    ),
                    className="chart-card"
                )
            ],
            className="chart-grid"
        )
    ],
    className="dashboard-page"
)


@callback(
    Output("sales-kpis", "children"),
    Output("sales-monthly-chart", "figure"),
    Output("sales-volume-chart", "figure"),
    Input("sales-date-range", "start_date"),
    Input("sales-date-range", "end_date"),
    Input("sales-status-filter", "value")
)
def update_sales(start_date, end_date, selected_statuses):

    filtered = orders.copy()

    if start_date:
        filtered = filtered[
            filtered["order_purchase_timestamp"] >= pd.Timestamp(start_date)
        ]

    if end_date:
        filtered = filtered[
            filtered["order_purchase_timestamp"] <
            pd.Timestamp(end_date) + pd.Timedelta(days=1)
        ]

    if selected_statuses is not None:
        filtered = filtered[
            filtered["order_status"].isin(selected_statuses)
        ]

    total_orders = filtered["order_id"].nunique()

    total_sales = filtered["total_product_value"].sum()

    total_freight = filtered["total_freight_value"].sum()

    average_value = (
        total_sales / total_orders
        if total_orders > 0 else 0
    )

    kpis = [
        metric_card(
            "Total Orders",
            f"{total_orders:,.0f}",
            "Orders in selected period",
            "teal"
        ),

        metric_card(
            "Product Sales",
            f"R$ {total_sales:,.0f}",
            "Recorded product item value",
            "blue"
        ),

        metric_card(
            "Average Product Value",
            f"R$ {average_value:,.2f}",
            "Product value per order",
            "purple"
        ),

        metric_card(
            "Freight Value",
            f"R$ {total_freight:,.0f}",
            "Recorded delivery charges",
            "orange"
        )
    ]

    sales_chart, order_chart = make_sales_charts(filtered)

    return kpis, sales_chart, order_chart
