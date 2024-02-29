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
from flask import Flask

from construct_sites import (
    add_stage_data,
    add_survey_data,
    construct_overview_page,
    construct_page,
    fetch_duration_df,
)

logo_path = "assets/logo_edited.png"

load_figure_template("solar")

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
}
# IMG_STYLE = {
#     "background-color": px.colors.qualitative.Prism[2],
# }

CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}
# These offsets MUST be zero unless Tane gives written instruction to change them.
sites = {
    "Tutaenui at Dam E4": {
        "datum": 166,  # Meters
        "offset": 0,  # Millimeters. I know.
    },
    "Tutaenui at Dam W3": {"datum": 175, "offset": 0},
    "Porewa at Dam 62": {"datum": 294, "offset": 0},
    "Porewa at Dam 73": {"datum": 274, "offset": 0},
    "Porewa at Dam 75": {"datum": 285, "offset": 0},
}

add_survey_data(sites)
add_stage_data(sites)

server = Flask(__name__)

app = Dash(
    server=server,
    use_pages=True,
    pages_folder="",
    external_stylesheets=[dbc.themes.SOLAR],
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
    return dbc.Col(
        [
            html.Img(src=logo_path, width=290),
            html.H2("Dam Dash"),
            html.P("v0.1.1 (Beta)"),
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
                        sitename_lookup[page["path"]],
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
        align="end"
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
        y=["Stage (mm)"],
        color_discrete_sequence=[px.colors.qualitative.Prism[5]],
        labels=dict(value="Stage (mm)"),
    )
    fig.update_traces(
        name="RADAR LEVEL",
        line=dict(width=4),
        hovertemplate=None
    )
    fig.add_hline(
        y=sites[sitename]["radar_level"] * 1000,
        annotation_text="RADAR HEIGHT",
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
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            xanchor="left",
            y=-0.17,
            title=None,
        ),
        hovermode="x"
    )
    fig.update_traces(
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
