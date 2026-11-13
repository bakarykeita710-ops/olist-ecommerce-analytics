

import dash
from dash import html, dcc, dash_table, Input, Output, callback
import pandas as pd
import plotly.express as px

from src.data_loader import load_data
from src.components import metric_card


dash.register_page(
    __name__,
    path="/products",
    name="Product Analysis",
    order=2
)

orders, order_items, geolocation = load_data()

category_col = (
    "product_category_name_english"
    if "product_category_name_english" in order_items.columns
    else "product_category_name"
)

items = order_items.copy()

items[category_col] = items[category_col].fillna("Unknown")
items["price"] = pd.to_numeric(items["price"], errors="coerce")

category_summary = (
    items.groupby(category_col)
    .agg(
        total_sales=("price", "sum"),
        items_sold=("order_item_id", "count"),
        total_orders=("order_id", "nunique"),
        average_price=("price", "mean")
    )
    .reset_index()
)


def create_product_chart(metric):

    labels = {
        "total_sales": "Total Product Sales (R$)",
        "items_sold": "Number of Items Sold",
        "total_orders": "Number of Orders"
    }

    top = (
        category_summary.nlargest(10, metric)
        .sort_values(metric)
    )

    fig = px.bar(
        top,
        x=metric,
        y=category_col,
        orientation="h",
        title=f"Top 10 Categories by {labels[metric]}",
        labels={
            metric: labels[metric],
            category_col: "Product Category"
        },
        color_discrete_sequence=["#A15BD5"]
    )

    fig.update_layout(
        template="plotly_white",
        height=450,
        font=dict(size=13, color="#334155"),
        title_font=dict(size=19, color="#202B3C"),
        margin=dict(l=25, r=25, t=65, b=35)
    )

    return fig


initial_chart = create_product_chart("total_sales")

scatter_chart = px.scatter(
    category_summary,
    x="items_sold",
    y="total_sales",
    size="total_orders",
    hover_name=category_col,
    title="Category Sales vs Items Sold",
    labels={
        "items_sold": "Items Sold",
        "total_sales": "Total Sales (R$)"
    },
    color_discrete_sequence=["#D56BAA"]
)

scatter_chart.update_layout(
    template="plotly_white",
    height=450,
    font=dict(size=13, color="#334155"),
    title_font=dict(size=19, color="#202B3C")
)


top_table = category_summary.nlargest(10, "total_sales")


layout = html.Div(
    [
        html.Div(
            [
                html.P("MERCHANDISE INSIGHTS", className="eyebrow"),
                html.H1("Product Analysis", className="page-title"),
                html.P(
                    "Discover the categories and products contributing "
                    "most to marketplace performance.",
                    className="page-subtitle"
                )
            ],
            className="page-heading accent-purple"
        ),

        html.Div(
            [
                metric_card(
                    "Product Items",
                    f"{len(items):,.0f}",
                    "Total item records",
                    "purple"
                ),

                metric_card(
                    "Product Categories",
                    f"{category_summary.shape[0]:,.0f}",
                    "Distinct categories, including unknown",
                    "blue"
                ),

                metric_card(
                    "Total Product Sales",
                    f"R$ {items['price'].sum():,.0f}",
                    "Sum of item prices",
                    "teal"
                ),

                metric_card(
                    "Average Item Price",
                    f"R$ {items['price'].mean():,.2f}",
                    "Average product item price",
                    "orange"
                )
            ],
            className="metric-grid"
        ),

        html.Div(
            [
                html.Div(
                    [
                        html.Label(
                            "Rank categories by",
                            className="filter-label"
                        ),
                        dcc.Dropdown(
                            id="product-metric-filter",
                            options=[
                                {
                                    "label": "Revenue",
                                    "value": "total_sales"
                                },
                                {
                                    "label": "Items Sold",
                                    "value": "items_sold"
                                },
                                {
                                    "label": "Number of Orders",
                                    "value": "total_orders"
                                }
                            ],
                            value="total_sales",
                            clearable=False
                        )
                    ],
                    className="filter-control"
                )
            ],
            className="filter-row"
        ),

        html.Div(
            [
                html.Div(
                    dcc.Graph(
                        id="product-ranking-chart",
                        figure=initial_chart,
                        config={"displayModeBar": False}
                    ),
                    className="chart-card"
                ),

                html.Div(
                    dcc.Graph(
                        figure=scatter_chart,
                        config={"displayModeBar": False}
                    ),
                    className="chart-card"
                )
            ],
            className="chart-grid"
        ),

        html.H3(
            "Top 10 Categories by Revenue",
            className="section-caption"
        ),

        dash_table.DataTable(
            id="product-category-table",
            columns=[
                {
                    "name": "Category",
                    "id": category_col
                },
                {
                    "name": "Total Sales (R$)",
                    "id": "total_sales",
                    "type": "numeric",
                    "format": {"specifier": ",.2f"}
                },
                {
                    "name": "Items Sold",
                    "id": "items_sold",
                    "type": "numeric"
                },
                {
                    "name": "Orders",
                    "id": "total_orders",
                    "type": "numeric"
                },
                {
                    "name": "Average Price (R$)",
                    "id": "average_price",
                    "type": "numeric",
                    "format": {"specifier": ",.2f"}
                }
            ],
            data=top_table.to_dict("records"),
            sort_action="native",
            page_size=10,
            style_table={"overflowX": "auto"},
            style_header={
                "backgroundColor": "#263B78",
                "color": "white",
                "fontWeight": "800",
                "fontSize": "13px",
                "padding": "14px",
                "textAlign": "left"
            },
            style_cell={
                "padding": "13px",
                "fontSize": "13px",
                "fontFamily": "Segoe UI, Arial",
                "textAlign": "left",
                "whiteSpace": "normal",
                "height": "auto"
            },
            style_data_conditional=[
                {
                    "if": {"row_index": "odd"},
                    "backgroundColor": "#F5F7FC"
                }
            ]
        )
    ],
    className="dashboard-page"
)


@callback(
    Output("product-ranking-chart", "figure"),
    Input("product-metric-filter", "value")
)
def update_product_ranking(selected_metric):
    return create_product_chart(selected_metric)
