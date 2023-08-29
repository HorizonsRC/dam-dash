from dash import Dash, html, dash_table, dcc
import pandas as pd
import os
import requests
import pyproj
import plotly.express as px
import plotly.graph_objects as go
from server_requests import get_sites, get_measurements, get_latest_data
from construct_sites import add_survey_data, add_stage_data
import json
import xml.etree.ElementTree as ET
import xmltodict

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

print(json.dumps(sites, indent=4))
add_survey_data(sites)
print(json.dumps(sites, indent=4))
add_stage_data(sites)
print(json.dumps(sites, indent=4))
    
    # for meas in json.loads(measurements_xml.text)["Options"]:
        # print(meas)

# nztm_proj = pyproj.Proj(proj='tmerc', lat_0=0, lon_0=173, k=0.9996, x_0=1600000, y_0=10000000, ellps='GRS80')
# wgs84_proj = pyproj.Proj(proj='latlong', datum='WGS84')
#
# nztm_x = 1819375
# nztm_y = 5576891
#
# lon, lat = pyproj.transform(nztm_proj, wgs84_proj, nztm_x, nztm_y)
#
# linz_url = f"https://data.linz.govt.nz/services/query/v1/raster.json?key=64ff9b0949f04d47a4f5443e5da6d099&layer=102475&x={lon}&y={lat}"
# https://data.linz.govt.nz/services;key=64ff9b0949f04d47a4f5443e5da6d099/wmts/1.0.0/layer/102475/WMTSCapabilities.xml
#
# response = requests.request("GET", linz_url)
# print(dir(response.raw))
# print(response.raw.data)


print(json.dumps(sites, indent=4))
app = Dash(__name__)

app.layout = html.Div([
    html.Div(children=sites[""]),
    dash_table.DataTable(data=dams[1].to_dict('records'), page_size=10),
    # dcc.Graph(figure=graphs[0]),
    # dcc.Graph(figure=graphs[1]),
    # dcc.Graph(figure=graphs[2]),
    # dcc.Graph(figure=graphs[3]),
    # dcc.Graph(figure=graphs[4])
])


if __name__ == '__main__':
    app.run(debug=True)
