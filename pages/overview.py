
import dash
from dash import html, dcc
import pandas as pd
import plotly.express as px

from src.data_loader import load_data
from src.components import metric_card


dash.register_page(
    __name__,
    path="/",
    name="Overview",
    order=0
)

# Load integrated data
order_level, order_items, geolocation = load_data()


# -----------------------------
# 1. Calculate main KPIs
# -----------------------------

total_orders = order_level["order_id"].nunique()

total_sales = order_level["total_product_value"].sum()

total_customers = order_level["customer_unique_id"].nunique()

average_review = order_level["average_review_score"].mean()

average_review_text = (
    f"{average_review:.2f} / 5"
    if pd.notna(average_review)
    else "N/A"
)


# -----------------------------
# 2. Monthly sales data
# -----------------------------

monthly_data = order_level.dropna(
    subset=["order_purchase_timestamp"]
).copy()

monthly_data["month"] = (
    monthly_data["order_purchase_timestamp"]
    .dt.to_period("M")
    .astype(str)
)

monthly_sales = (
    monthly_data.groupby("month", as_index=False)
    ["total_product_value"]
    .sum()
)


# -----------------------------
# 3. Product category data
# -----------------------------

category_column = "product_category_name_english"

if category_column not in order_items.columns:
    category_column = "product_category_name"

category_data = order_items.copy()

category_data[category_column] = (
    category_data[category_column].fillna("Unknown")
)

top_categories = (
    category_data.groupby(category_column, as_index=False)["price"]
    .sum()
    .nlargest(10, "price")
    .sort_values("price")
)


# -----------------------------
# 4. Order status data
# -----------------------------

status_data = (
    order_level["order_status"]
    .value_counts()
    .rename_axis("order_status")
    .reset_index(name="total_orders")
)


# -----------------------------
# 5. Create charts
# -----------------------------

sales_figure = px.line(
    monthly_sales,
    x="month",
    y="total_product_value",
    markers=True,
    title="Monthly Product Sales",
    labels={
        "month": "Month",
        "total_product_value": "Product Sales (R$)"
    },
    color_discrete_sequence=["#6259D9"]
)

sales_figure.update_layout(
    template="plotly_white",
    height=340,
    margin=dict(l=25, r=25, t=55, b=35),
    font=dict(color="#334155"),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)"
)


category_figure = px.bar(
    top_categories,
    x="price",
    y=category_column,
    orientation="h",
    title="Top 10 Product Categories",
    labels={
        "price": "Product Sales (R$)",
        category_column: "Category"
    },
    color_discrete_sequence=["#19A89D"]
)

category_figure.update_layout(
    template="plotly_white",
    height=380,
    margin=dict(l=25, r=25, t=55, b=35),
    showlegend=False,
    font=dict(color="#334155"),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)"
)


status_figure = px.pie(
    status_data,
    names="order_status",
    values="total_orders",
    hole=0.65,
    title="Order Status Distribution",
    color_discrete_sequence=[
        "#6259D9",
        "#19A89D",
        "#F5A623",
        "#EF7185",
        "#6396D8",
        "#9B8BC9"
    ]
)

status_figure.update_layout(
    template="plotly_white",
    height=340,
    margin=dict(l=20, r=20, t=55, b=25),
    font=dict(color="#334155"),
    paper_bgcolor="rgba(0,0,0,0)"
)

status_figure.update_traces(
    textposition="inside",
    textinfo="percent"
)


# -----------------------------
# 6. Dashboard layout
# -----------------------------

layout = html.Div(
    [
        html.Div(
            [
                html.P("EXECUTIVE OVERVIEW", className="eyebrow"),
                html.H1(
                    "Marketplace at a glance",
                    className="page-title"
                ),
                html.P(
                    "A high-level view of Olist's e-commerce "
                    "performance and business activity.",
                    className="page-subtitle"
                )
            ],
            className="page-heading accent-blue"
        ),

        html.Div(
            [
                metric_card(
                    "Total Orders",
                    f"{total_orders:,.0f}",
                    "Orders recorded in the dataset",
                    "blue"
                ),

                metric_card(
                    "Total Product Sales",
                    f"R$ {total_sales:,.0f}",
                    "Sum of product item values",
                    "purple"
                ),

                metric_card(
                    "Unique Customers",
                    f"{total_customers:,.0f}",
                    "Distinct customer identities",
                    "teal"
                ),

                metric_card(
                    "Average Review",
                    average_review_text,
                    "Average score per reviewed order",
                    "orange"
                )
            ],
            className="metric-grid"
        ),

        html.Div(
            [
                html.Div(
                    [
                        dcc.Graph(
                            figure=sales_figure,
                            config={"displayModeBar": False}
                        )
                    ],
                    className="chart-card chart-wide"
                ),

                html.Div(
                    [
                        dcc.Graph(
                            figure=status_figure,
                            config={"displayModeBar": False}
                        )
                    ],
                    className="chart-card"
                ),

                html.Div(
                    [
                        dcc.Graph(
                            figure=category_figure,
                            config={"displayModeBar": False}
                        )
                    ],
                    className="chart-card"
                )
            ],
            className="chart-grid"
        )
    ],
    className="dashboard-page"
)
