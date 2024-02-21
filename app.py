# import json
# import os
# import xml.etree.ElementTree as ET
from urllib.parse import quote

import dash
import dash_bootstrap_components as dbc

# import pandas as pd
import plotly.express as px

# import plotly.graph_objects as go
# import requests
# import xmltodict
from dash import Dash, Input, Output, State, dcc, html
from dash_bootstrap_templates import load_figure_template

from construct_sites import (
    add_stage_data,
    add_survey_data,
    construct_overview_page,
    construct_page,
    fetch_duration_df,
)

# from server_requests import get_latest_data, get_measurements, get_sites

load_figure_template("cyborg")

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
}

CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}
# I'm totally guessing these offsets by eyeballing the recent running average
sites = {
    "Tutaenui at Dam E4": {
        "datum": 166,  # Meters
        "offset": 120,  # Millimeters. I know.
    },
    "Tutaenui at Dam W3": {"datum": 175, "offset": -470},
    "Porewa at Dam 62": {"datum": 294, "offset": 10},
    "Porewa at Dam 73": {"datum": 274, "offset": 0},
    "Porewa at Dam 75": {"datum": 285, "offset": -5},
}

add_survey_data(sites)
add_stage_data(sites)

app = Dash(
    __name__,
    use_pages=True,
    pages_folder="",
    external_stylesheets=[dbc.themes.CYBORG],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
    ],
)

server = app.server

overview_page = construct_overview_page(sites)
dash.register_page("Overview", path="/", layout=overview_page)


sitename_lookup = {}
for sitename, sitedata in sites.items():
    page_content = construct_page(sitename, sitedata)
    sanitized = quote(sitename)
    sitepath = f"/{sanitized}"
    sitename_lookup[sitepath] = sitename
    dash.register_page(sitename, path=f"/{sanitized}", layout=page_content)


def sidebar():
    return html.Div(
        [
            html.H2("Dam Dash"),
            html.P("v0.1.0 (Beta)"),
            html.Hr(),
            html.P(
                "A dashboard for Tane's dams. "
            ),
            html.P("Please provide issues, feedback and comments to Nic."),
            html.Hr(),
            dbc.Nav(
                [dbc.NavLink("Overview Map", href="/", active="exact")],
                vertical=True,
                pills=True,
            ),
            html.Hr(),
            dbc.Nav(
                [
                    dbc.NavLink(
                        page["name"],
                        href=page["relative_path"],
                        active="exact",
                    )
                    for page in dash.page_registry.values()
                    if page["path"] != "/"
                ],
                vertical=True,
                pills=True,
            ),
        ],
        style=SIDEBAR_STYLE,
    )


app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=True),
        sidebar(),
        dbc.Container(
            [
                dash.page_container,
            ],
            fluid=True,
        ),
    ],
    style=CONTENT_STYLE,
)


@app.callback(
    Output("time-series-plot", "figure"),
    [Input("duration-selector", "value"), State("url", "pathname")],
)
def update_content(duration, pathname):
    sitename = sitename_lookup[pathname]
    df = fetch_duration_df(sitename, duration)

    df["Stage (mm)"] = df["Stage (mm)"] + (sites[sitename]["offset"])

    fig = px.line(
        df,
        x="Timestamp",
        y="Stage (mm)",
        color_discrete_sequence=[px.colors.qualitative.Prism[5]],
        # range_y=sites[sitename]["ylims"]
    )
    fig.add_hline(
        y=sites[sitename]["radar_level"] * 1000,
        annotation_text="RADAR LEVEL",
        line_dash="dot",
    )
    fig.add_hline(
        y=sites[sitename]["paver_level"] * 1000,
        annotation_text="PAVER LEVEL",
        line_dash="dot",
    )
    fig.add_hline(
        y=sites[sitename]["outflow"] * 1000,
        annotation_text="OUTFLOW LEVEL",
        line_dash="dot",
    )
    fig.add_hline(
        y=sites[sitename]["culvert_invert"] * 1000,
        annotation_text="CULVERT LEVEL",
        line_dash="dot",
    )
    fig.update_layout(
        margin={"r": 0, "t": 20, "l": 0, "b": 0},
        yaxis_range=(
            sites[sitename]["ylims"][0] * 1000,
            sites[sitename]["ylims"][1] * 1000,
        ),
    )
    return fig


@app.callback(
    Output("url", "pathname"),
    Input("map", "clickData"),
    prevent_initial_call=True,
)
def overview_map_clickthrough(click_data):
    if click_data is not None:
        site = click_data["points"][0]["customdata"]
        return f"/{site}"
    else:
        return "/"


if __name__ == "__main__":
    app.run(debug=True)  # DEVELOPMENT
    # app.run(host='0.0.0.0', port=8050, debug=False) # PRODUCTION
