
import dash
from dash import html, dcc, Input, Output, callback
import pandas as pd
import plotly.express as px

from src.data_loader import load_data, load_payments
from src.components import metric_card


dash.register_page(
    __name__,
    path="/orders-payments",
    name="Orders & Payments",
    order=4
)

orders, order_items, geolocation = load_data()
payments = load_payments()

payments["payment_value"] = pd.to_numeric(
    payments["payment_value"],
    errors="coerce"
)

payments["payment_installments"] = pd.to_numeric(
    payments["payment_installments"],
    errors="coerce"
)

payment_types = sorted(payments["payment_type"].dropna().unique())


status_data = (
    orders["order_status"]
    .value_counts()
    .rename_axis("order_status")
    .reset_index(name="total_orders")
)


def make_status_chart():

    fig = px.bar(
        status_data,
        x="total_orders",
        y="order_status",
        orientation="h",
        title="Orders by Status",
        color_discrete_sequence=["#397FC5"]
    )

    fig.update_layout(
        template="plotly_white",
        height=380,
        font=dict(size=13),
        title_font=dict(size=19)
    )

    return fig


layout = html.Div(
    [
        html.Div(
            [
                html.P("TRANSACTION INTELLIGENCE", className="eyebrow"),
                html.H1("Orders & Payments", className="page-title"),
                html.P(
                    "Monitor order fulfilment, payment methods "
                    "and transaction behaviour.",
                    className="page-subtitle"
                )
            ],
            className="page-heading accent-cyan"
        ),

        html.Div(
            [
                html.Div(
                    [
                        html.Label(
                            "Payment Method",
                            className="filter-label"
                        ),
                        dcc.Dropdown(
                            id="payment-method-filter",
                            options=[
                                {
                                    "label": "All Payment Methods",
                                    "value": "ALL"
                                }
                            ] + [
                                {"label": method.title(), "value": method}
                                for method in payment_types
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
            id="payment-kpis",
            className="metric-grid"
        ),

        html.Div(
            [
                html.Div(
                    dcc.Graph(
                        id="payment-method-chart",
                        config={"displayModeBar": False}
                    ),
                    className="chart-card"
                ),

                html.Div(
                    dcc.Graph(
                        id="payment-installment-chart",
                        config={"displayModeBar": False}
                    ),
                    className="chart-card"
                ),

                html.Div(
                    dcc.Graph(
                        figure=make_status_chart(),
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
    Output("payment-kpis", "children"),
    Output("payment-method-chart", "figure"),
    Output("payment-installment-chart", "figure"),
    Input("payment-method-filter", "value")
)
def update_payment_dashboard(selected_method):

    if selected_method == "ALL":
        filtered = payments.copy()
    else:
        filtered = payments[
            payments["payment_type"] == selected_method
        ]

    total_payment = filtered["payment_value"].sum()

    total_paid_orders = filtered["order_id"].nunique()

    transaction_count = len(filtered)

    average_payment = (
        total_payment / total_paid_orders
        if total_paid_orders else 0
    )

    average_installments = filtered[
        "payment_installments"
    ].mean()

    installment_text = (
        f"{average_installments:.1f}"
        if pd.notna(average_installments) else "N/A"
    )

    kpis = [
        metric_card(
            "Payment Value",
            f"R$ {total_payment:,.0f}",
            "Value for selected payment method",
            "blue"
        ),

        metric_card(
            "Paid Orders",
            f"{total_paid_orders:,.0f}",
            "Unique orders with selected payment",
            "teal"
        ),

        metric_card(
            "Transactions",
            f"{transaction_count:,.0f}",
            "Payment records",
            "purple"
        ),

        metric_card(
            "Average Installments",
            installment_text,
            "Average installments per transaction",
            "orange"
        )
    ]

    # Payment method comparison (always shows all methods)
    method_summary = (
        payments.groupby("payment_type")
        .agg(
            payment_value=("payment_value", "sum"),
            transactions=("payment_sequential", "count")
        )
        .reset_index()
        .sort_values("payment_value", ascending=False)
    )

    method_fig = px.bar(
        method_summary,
        x="payment_type",
        y="payment_value",
        title="Payment Value by Method",
        labels={
            "payment_type": "Payment Method",
            "payment_value": "Payment Value (R$)"
        },
        color_discrete_sequence=["#298CCB"]
    )

    method_fig.update_layout(
        template="plotly_white",
        height=380,
        font=dict(size=13),
        title_font=dict(size=19)
    )

    # Installment distribution for selected method
    installment_data = (
        filtered.dropna(subset=["payment_installments"])
        .groupby("payment_installments")
        .size()
        .reset_index(name="transactions")
        .sort_values("payment_installments")
    )

    installment_fig = px.bar(
        installment_data,
        x="payment_installments",
        y="transactions",
        title="Payment Installment Distribution",
        labels={
            "payment_installments": "Number of Installments",
            "transactions": "Transactions"
        },
        color_discrete_sequence=["#47AFC4"]
    )

    installment_fig.update_layout(
        template="plotly_white",
        height=380,
        font=dict(size=13),
        title_font=dict(size=19)
    )

    return kpis, method_fig, installment_fig

