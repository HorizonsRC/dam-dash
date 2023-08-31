from server_requests import get_latest_data, get_measurements, get_data
from dash import Dash, html, dash_table, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import xmltodict
import plotly.graph_objects as go
import plotly.express as px
import plotly.colors as pc
import pyproj
import requests
import json
import numpy as np
from PIL import Image
import io

DURATIONS = [
    {"label": "1 Year", "value": "P1Y"},
    {"label": "3 Months", "value": "P3M"},
    {"label": "1 Month", "value": "P1M"},
    {"label": "7 Days", "value": "P7D"},
    {"label": "3 Days", "value": "P3D"},
    {"label": "1 Day", "value": "P1D"},
]


def add_survey_data(sites):
    df = pd.read_excel("23021-20230824-COORDINATES.xlsx", header=None)
    split_rows = list(df[df[0] == "X"].index.values)
    split_rows.append(len(df))
    dams = []
    bottom = 0
    for site, row in zip(sites, split_rows[1:]):
        split_df = df[bottom:row]
        split_df.columns = split_df.iloc[0]
        split_df = split_df[1:]
        dams += [split_df]
        bottom = row

        sites[site]["distance"] = list(split_df['running distance'].values)
        sites[site]["elevation"] = list(split_df['Z'].values)

        sites[site]["outflow"] = min(list(split_df['Z'].values))
        
        sites[site]["X"] = list(split_df['X'].values)
        sites[site]["Y"] = list(split_df['Y'].values)
        
        lats = []
        lons = []
        for nztm_x, nztm_y in zip(sites[site]["X"], sites[site]["Y"]):
            lat, lon = convert_nztm_to_latlon(nztm_x, nztm_y)
            lats += [lat]
            lons += [lon]
        sites[site]["lats"] = lats
        sites[site]["lons"] = lons
        
        sites[site]["centroid_nztm"] = calculate_centroid(list(zip(split_df["X"].values, split_df["Y"].values)))
        sites[site]["centroid_wgs84"] = calculate_centroid(list(zip(lats, lons)))
        sites[site]["min_height"] = split_df['Z'].min()
        sites[site]["max_height"] = split_df['Z'].max()
        sites[site]["radar_level"] = split_df['RADAR LEVEL : '].iloc[0]
        sites[site]["paver_level"] = split_df['PAVER LEVEL'].iloc[0]
        sites[site]["culvert_invert"] = split_df['CULVERT INVERT'].iloc[0]
        all_ys = [
            sites[site]["min_height"], 
            sites[site]["max_height"], 
            sites[site]["radar_level"],
            sites[site]["paver_level"]
        ]
        sites[site]["ymin"] = min(all_ys)
        sites[site]["ymax"] = max(all_ys)
        sites[site]["yrange"] = sites[site]["ymax"] - sites[site]["ymin"] 
        
        sites[site]["ylims"] = (
            sites[site]["ymin"] - 0.1*sites[site]["yrange"],
            sites[site]["ymax"] + 0.1*sites[site]["yrange"]
        )


def fetch_duration_df(site, dur):
    ts_response = get_data(site, "Stage", dur)
    ts_data = xmltodict.parse(ts_response.content)
    measurement = ts_data["Hilltop"]["Measurement"]["Data"]["E"]
    dur_df = pd.DataFrame(measurement)
    dur_df.rename(columns={"T":"Timestamp", "I1": "Stage (mm)"}, inplace=True)
    dur_df["Stage (mm)"] = dur_df["Stage (mm)"].apply(pd.to_numeric)
    dur_df["Timestamp"] = pd.to_datetime(dur_df["Timestamp"])
    return dur_df


def add_stage_data(sites):
    for site in sites:
        data_xml = get_latest_data(site, "Stage")
        measurements_xml = get_measurements(site)
        data_dict = xmltodict.parse(data_xml.content)
        sites[site]["last_updated"] = data_dict["Hilltop"]["Measurement"]["Data"]["E"]["T"]
        sites[site]["last_raw_val"] = data_dict["Hilltop"]["Measurement"]["Data"]["E"]["I1"]
        sites[site]["m_from_paver"] = (
            float(sites[site]["last_raw_val"]) + float(sites[site]["offset"])
        )/1000


def convert_nztm_to_latlon(nztm_x, nztm_y):
    nztm_epsg = "EPSG:2193"
    wgs84_epsg = "EPSG:4326"
    transformer = pyproj.Transformer.from_crs(nztm_epsg, wgs84_epsg)
    lat, lon = transformer.transform(nztm_y, nztm_x)

    return lat, lon

def calculate_centroid(coords):
    total_x = 0
    total_y = 0
    num_coords = len(coords)

    for x, y in coords:
        total_x += x
        total_y += y

    centroid_x = total_x / num_coords
    centroid_y = total_y / num_coords

    return centroid_x, centroid_y

def plot_cross_section(data):
    color_sequence = pc.qualitative.Plotly
    
    crossec_fig = go.Figure()
    crossec_fig.add_trace(go.Scatter(x=data["distance"],
                             y=data["elevation"],
                             fill='tozeroy'))
    crossec_fig.add_hline(y=data["radar_level"],
                  annotation_text='RADAR LEVEL',
                  line_dash='dot')
    crossec_fig.add_hline(y=data["paver_level"],
                  annotation_text='PAVER LEVEL',
                  line_dash='dot')
    crossec_fig.add_hline(y=data["outflow"],
                  annotation_text='OVERTOP POINT',
                  line_dash='dot')
    crossec_fig.add_hline(y=data["culvert_invert"],
                  annotation_text='CULVERT LEVEL',
                  line_dash='dot')
    crossec_fig.update_layout(yaxis_range=data["ylims"])
    
    crossec_fig.update_layout(margin={"r":0, "t":0, "l":0, "b":0})
    return crossec_fig

def map_sat_image(name, data):
    map_url = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    # response = requests.get(map_url)
    map_trace = go.Scattermapbox(
        lat=data['lats'],
        lon=data['lons'],
        mode='markers',
        marker=dict(
            size=6,
        ),
        text=name
    )

    map_layout = go.Layout(
        mapbox=dict(
            style='open-street-map',  # Use 'mapbox://styles/mapbox/satellite-streets-v11' for satellite view
            # accesstoken=mapbox_token,
            center=dict(lat=data["centroid_wgs84"][0], lon=data["centroid_wgs84"][1]),
            zoom=16,
            layers=[{
                "below": 'traces',
                "sourcetype": 'raster',
                "sourceattribution": 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
                "source": [map_url]
            }]
        ),
        showlegend=False
    )
    map_fig = go.Figure(data=[map_trace], layout=map_layout)

    map_fig.update_layout(margin={"r":0, "t":0, "l":0, "b":0})
    return map_fig


def construct_page(name, data):

    # Create TS plot 
    # ts_fig = plot_timeseries_duration(data)
    
    # Create the cross section plot
    crossec_fig = plot_cross_section(data)
    
    # Create a Scattermapbox trace
    map_fig = map_sat_image(name, data) 
    
    content = html.Div([
        dbc.Card(
            dbc.CardBody([
                html.H4(name, id="site-label"),
            ])    
        ),
        dbc.Card(
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Label("Select Duration:"),
                            dbc.RadioItems(
                                id="duration-selector",
                                className="btn-group",
                                inputClassName="btn-check",
                                labelClassName="btn btn-outline-primary",
                                labelCheckedClassName="active",
                                options=DURATIONS,
                                value=DURATIONS[-1]["value"],
                            ),
                            dcc.Graph(id="time-series-plot")
                        ], className="p-5 radio-group")
                    ], width=12),
                ], align="center"),
                # html.Br(),
                dbc.Row([
                    dbc.Col([
                        dcc.Graph(figure=crossec_fig)
                    ], width=6),
                    dbc.Col([
                        dcc.Graph(figure=map_fig)
                    ], width=6),
                ], align="center"),
                # html.Br(),
                # dbc.Row([
                #     dbc.Col([
                #         dcc.Graph(figure=dem_fig)
                #     ], width=6),
                #     dbc.Col([
                #         # dcc.Graph(figure=im_fig)
                #     ], width=6),
                # ], align="center"),
            ])
        )
    ])
    return content
