
import dash
from dash import Dash, html, dcc


app = Dash(
    __name__,
    use_pages=True,
    title="Olist | E-Commerce Analytics",
    suppress_callback_exceptions=True
)

# Create navigation links from registered pages
navigation_links = [
    dcc.Link(
        [
            html.Span(f"{index + 1:02d}", className="nav-number"),
            html.Span(page["name"])
        ],
        href=page["relative_path"],
        className="sidebar-link"
    )
    for index, page in enumerate(dash.page_registry.values())
]


app.layout = html.Div(
    [
        # SIDEBAR
        html.Aside(
            [
                html.Div(
                    [
                        html.Div("O", className="brand-mark"),
                        html.Div(
                            [
                                html.H2("OLIST"),
                                html.P("ANALYTICS STUDIO")
                            ],
                            className="brand-text"
                        )
                    ],
                    className="sidebar-brand"
                ),

                html.P("WORKSPACE", className="nav-heading"),

                html.Nav(
                    navigation_links,
                    className="sidebar-nav"
                ),

                html.Div(
                    [
                        html.P("PROJECT"),
                        html.H4("Brazilian E-Commerce"),
                        html.Small("Data Analytics Project")
                    ],
                    className="sidebar-footer"
                )
            ],
            className="sidebar"
        ),

        # MAIN CONTENT
        html.Main(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.P("OLIST / ANALYTICS"),
                                html.H3("Business Intelligence Dashboard")
                            ],
                            className="topbar-title"
                        ),

                        html.Div(
                            "DATASET: BRAZIL",
                            className="topbar-tag"
                        )
                    ],
                    className="topbar"
                ),

                dash.page_container
            ],
            className="main-content"
        )
    ],
    className="app-shell"
)


server = app.server


if __name__ == "__main__":
    app.run(debug=True, port=8050)
