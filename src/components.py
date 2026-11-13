
from dash import html


def metric_card(label, value, description, accent="blue"):

    return html.Div(
        [
            html.P(label, className="metric-label"),
            html.H2(value, className="metric-value"),
            html.P(description, className="metric-description")
        ],
        className=f"metric-card metric-{accent}"
    )


def placeholder_layout(title, subtitle, accent):

    return html.Div(
        [
            html.Div(
                [
                    html.P("OLIST ANALYTICS", className="eyebrow"),
                    html.H1(title, className="page-title"),
                    html.P(subtitle, className="page-subtitle")
                ],
                className=f"page-heading accent-{accent}"
            ),

            html.Div(
                [
                    html.H3("Analysis workspace"),
                    html.P(
                        "This page is ready for its charts, "
                        "KPIs and interactive filters."
                    ),
                    html.P(
                        "We will add the completed EDA insights "
                        "to this page in the next development steps."
                    )
                ],
                className="placeholder-card"
            )
        ],
        className="dashboard-page"
    )
