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

load_figure_template("solar")

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
        "datum": 166, # Meters
        "offset": -60 # Millimeters. I know.
    },
    "Tutaenui at Dam W3": {
        "datum": 175,
        "offset": -62
    },
    "Porewa at Dam 62": {
        "datum": 294,
        "offset": -474
    },
    "Porewa at Dam 73": {
        "datum": 274,
        "offset": +50
    },
    "Porewa at Dam 75": {
        "datum": 285,
        "offset": -703
    },
}

# print(json.dumps(sites, indent=4))
add_survey_data(sites)
# print(json.dumps(sites, indent=4))
add_stage_data(sites)
# print(json.dumps(sites, indent=4))
    
# add_timeseries_data(sites)
    # for meas in json.loads(measurements_xml.text)["Options"]:
        # print(meas)

    #
# linz_url = f"https://data.linz.govt.nz/services/query/v1/raster.json?key=64ff9b0949f04d47a4f5443e5da6d099&layer=102475&x={lon}&y={lat}"
# https://data.linz.govt.nz/services;key=64ff9b0949f04d47a4f5443e5da6d099/wmts/1.0.0/layer/102475/WMTSCapabilities.xml
#
# response = requests.request("GET", linz_url)
# print(dir(response.raw))
# print(response.raw.data)


# print(json.dumps(sites, indent=4))
# print(dir(sites))
# print(list(sites.keys()))
app = Dash(__name__, use_pages=True,
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
    return html.Div(
        [
            html.H2("Dam Buoy*"),
            html.Hr(),
            html.P(
                "*Working title. Also considering Dam It, Dam Dash, or Hot Dam. Send your thoughts and ideas to nic@fakemail.coom"
            ),
            html.Hr(),
            dbc.Nav([
                dbc.NavLink("Overview Map", href="/", active="exact")
            ], vertical=True, pills=True),
            html.Hr(),
            dbc.Nav([
                dbc.NavLink(page['name'], href=page["relative_path"], active="exact")
                for page in dash.page_registry.values() if page["path"] != "/"
            ], vertical=True, pills=True),
            
        ],
        style=SIDEBAR_STYLE
    )
        
app.layout = html.Div([
    dcc.Location(id='url', refresh=True),
    sidebar(),
    dbc.Container([
        dash.page_container,
    ], fluid=True)
], style=CONTENT_STYLE)

@app.callback(
    Output("time-series-plot", "figure"),
    [Input("duration-selector", "value"), State("url", "pathname")]
)
def update_content(duration, pathname):
    sitename = sitename_lookup[pathname]
    df = fetch_duration_df(sitename, duration)
    fig = px.line(df, x="Timestamp", y="Stage (mm)")
    fig.update_layout(margin={"r":0, "t":20, "l":0, "b":0})
    # fig.add_hline(y=sites[sitename]["paver_level"],
    #               annotation_text='PAVER LEVEL',
    #               line_dash='dot')
    # fig.add_hline(y=sites[sitename]["outflow"],
    #               annotation_text='OUTFLOW',
    #               line_dash='dot')
    return fig

@app.callback(
    Output("url", "pathname"),
    Input("map", "clickData"),
    prevent_initial_call=True
)
def overview_map_clickthrough(click_data):
    if click_data is not None:
        site = click_data["points"][0]["customdata"]
        return f"/{site}"
    else:
        return "/"
if __name__ == '__main__':
    # app.run(debug=True) # DEVELOPMENT
    app.run(host='0.0.0.0', port=8050, debug=False) # PRODUCTION
