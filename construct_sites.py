import os

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import pyproj
import xmltodict
from dash import dcc, html

from server_requests import get_data, get_latest_data
from dash_bootstrap_templates import load_figure_template


load_figure_template(["darkly", "sketchy", "slate"])

MAPBOX_TOKEN = "pk.eyJ1IjoibmljbW9zdGVydCIsImEiOiJjbGx3eDZ5ZHIxbzI0M2ZwaGR1ZHN5NnZzIn0.KDSOloWKwP8T6Uso9LEtcQ"

script_directory = os.path.dirname(os.path.abspath(__file__))
survey_path = os.path.join(script_directory, "23021-20230824-COORDINATES.xlsx")

DURATIONS = [
    {"label": "1 Year", "value": "P1Y"},
    {"label": "3 Months", "value": "P3M"},
    {"label": "1 Month", "value": "P1M"},
    {"label": "7 Days", "value": "P7D"},
    {"label": "3 Days", "value": "P3D"},
    {"label": "1 Day", "value": "P1D"},
]


def add_survey_data(sites):
    df = pd.read_excel(survey_path, header=None)
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

        sites[site]["name"] = site

        sites[site]["distance"] = list(split_df["running distance"].values)
        sites[site]["elevation"] = list(split_df["Z"].values)

        sites[site]["outflow"] = min(list(split_df["Z"].values))

        sites[site]["X"] = list(split_df["X"].values)
        sites[site]["Y"] = list(split_df["Y"].values)

        lats = []
        lons = []
        for nztm_x, nztm_y in zip(sites[site]["X"], sites[site]["Y"]):
            lat, lon = convert_nztm_to_latlon(nztm_x, nztm_y)
            lats += [lat]
            lons += [lon]
        sites[site]["lats"] = lats
        sites[site]["lons"] = lons

        sites[site]["centroid_nztm"] = calculate_centroid(
            list(zip(split_df["X"].values, split_df["Y"].values))
        )
        sites[site]["centroid_wgs84"] = calculate_centroid(
            list(zip(lats, lons))
        )
        sites[site]["min_height"] = split_df["Z"].min()
        sites[site]["max_height"] = split_df["Z"].max()
        sites[site]["radar_level"] = split_df["RADAR LEVEL : "].iloc[0]
        sites[site]["paver_level"] = split_df["PAVER LEVEL"].iloc[0]
        sites[site]["culvert_invert"] = split_df["CULVERT INVERT"].iloc[0]
        all_ys = [
            sites[site]["min_height"],
            sites[site]["max_height"],
            sites[site]["radar_level"],
            sites[site]["paver_level"],
        ]
        sites[site]["ymin"] = min(all_ys)
        sites[site]["ymax"] = max(all_ys)
        sites[site]["yrange"] = sites[site]["ymax"] - sites[site]["ymin"]

        sites[site]["ylims"] = (
            sites[site]["ymin"] - 0.1 * sites[site]["yrange"],
            sites[site]["ymax"] + 0.1 * sites[site]["yrange"],
        )


def fetch_duration_df(site, dur):
    ts_response = get_data(site, "Stage", dur)
    ts_data = xmltodict.parse(ts_response.content)
    measurement = ts_data["Hilltop"]["Measurement"]["Data"]["E"]
    dur_df = pd.DataFrame(measurement)
    dur_df.rename(columns={"T": "Timestamp", "I1": "Stage (mm)"}, inplace=True)
    dur_df["Stage (mm)"] = dur_df["Stage (mm)"].apply(pd.to_numeric)
    dur_df["Timestamp"] = pd.to_datetime(dur_df["Timestamp"])
    return dur_df


def add_stage_data(sites):
    for site in sites:
        data_xml = get_latest_data(site, "Stage")
        data_dict = xmltodict.parse(data_xml.content)
        sites[site]["last_updated"] = data_dict["Hilltop"]["Measurement"][
            "Data"
        ]["E"]["T"]
        sites[site]["last_raw_val"] = data_dict["Hilltop"]["Measurement"][
            "Data"
        ]["E"]["I1"]
        sites[site]["m_from_paver"] = (
            float(sites[site]["last_raw_val"]) + float(sites[site]["offset"])
        ) / 1000


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
    crossec_fig = go.Figure(go.Scatter(
        # data,
        x=data["distance"],
        y=data["elevation"],
        showlegend=False,
        fill='tozeroy',
        marker=dict(
            opacity=0,
            color=px.colors.qualitative.Prism[5],
        ),
        hovertemplate=None,
        name="Dam height"
    ))
    level_df = fetch_duration_df(data["name"], "P1D")
    latest_level = (level_df.iloc[-1]["Stage (mm)"] + data["offset"])/1000
    crossec_fig.add_trace(go.Scatter(
        x = data["distance"],
        y = [latest_level]*len(data["distance"]),
        showlegend=False,
        fill='tozeroy',
        marker=dict(
            opacity=0,
            color=px.colors.qualitative.Prism[2],
        ),
        name="Radar level"
    ))
    crossec_fig.add_hline(
        y=latest_level,
        annotation_text="RADAR LEVEL",
        annotation_position="top left",
        annotation_font=dict(
            color=px.colors.qualitative.Prism[2],
            size=16
        ),
        line={
            "color":px.colors.qualitative.Prism[2],
            "width":4
        },
    )
    crossec_fig.add_hline(
        y=data["radar_level"], annotation_text="RADAR HEIGHT", line_dash="dot"
    )
    crossec_fig.add_hline(
        y=data["paver_level"], annotation_text="PAVER LEVEL", line_dash="dot"
    )
    crossec_fig.add_hline(
        y=data["outflow"], annotation_text="OUTFLOW LEVEL", line_dash="dot"
    )
    crossec_fig.add_hline(
        y=data["culvert_invert"],
        annotation_text="CULVERT LEVEL",
        line_dash="dot",
    )
    
    crossec_fig.update_traces(hovertemplate=None)

    crossec_fig.update_layout(
        yaxis_range=data["ylims"],
        xaxis_title="Distance along dam wall (m)",
        yaxis_title="Elevation (m)",
        hovermode="x",
    )
    return crossec_fig


def map_sat_image(name, data):
    map_url = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    # response = requests.get(map_url)

    map_layout = go.Layout(
        mapbox=dict(
            style="open-street-map",  # Use 'mapbox://styles/mapbox/satellite-streets-v11' for satellite view
            # accesstoken=mapbox_token,
            center=dict(
                lat=data["centroid_wgs84"][0], lon=data["centroid_wgs84"][1]
            ),
            zoom=16,
            layers=[
                {
                    "below": "traces",
                    "sourcetype": "raster",
                    "sourceattribution": "Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community",
                    "source": [map_url],
                }
            ],
        ),
        showlegend=False,
    )
    map_fig = go.Figure(layout=map_layout)

    # map_fig.add_trace(
    #     go.Scattermapbox(
    #         lat=data["lats"],
    #         lon=data["lons"],
    #         mode="markers",
    #         marker=dict(
    #             size=10,
    #             color=px.colors.qualitative.Prism[1],
    #         ),
    #         text=name,
    #         hoverinfo=None,
    #         name=name
    #     )
    # )
    map_fig.add_trace(
        go.Scattermapbox(
            lat=data["lats"],
            lon=data["lons"],
            mode="markers",
            hoverlabel=None,
            marker=dict(
                size=6,
                color=px.colors.qualitative.Prism[5],
            ),
            text=name,
        )
    )
    map_fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
    )
    return map_fig


def map_overview(sites):
    centroid_lat = []
    centroid_lon = []

    map_fig = go.Figure()

    for i, (name, data) in enumerate(sites.items()):
        centroid_lat += [data["centroid_wgs84"][0]]
        centroid_lon += [data["centroid_wgs84"][1]]

        map_fig.add_trace(
            go.Scattermapbox(
                lat=centroid_lat,
                lon=centroid_lon,
                mode="markers",
                marker=go.scattermapbox.Marker(
                    size=20,
                    color=px.colors.qualitative.Prism[5],
                ),
                hoverinfo="none",
            ),
        )
        map_fig.add_trace(
            go.Scattermapbox(
                lat=centroid_lat,
                lon=centroid_lon,
                mode="markers",
                marker=go.scattermapbox.Marker(
                    size=17,
                    color=px.colors.qualitative.Prism[1],
                ),
                hoverinfo="none",
            ),
        )
        map_fig.add_trace(
            go.Scattermapbox(
                lat=centroid_lat,
                lon=centroid_lon,
                mode="markers",
                marker=go.scattermapbox.Marker(
                    size=14,
                    color=px.colors.qualitative.Prism[5],
                ),
                hoverinfo="lat+lon+text",
            ),
        )
    mid_lat = sum(centroid_lat) / len(centroid_lat)
    mid_lon = sum(centroid_lon) / len(centroid_lon)

    map_fig.update_traces(
        customdata=list(sites.keys()),
        text=list(sites.keys()),
        selector=dict(type="scattermapbox"),
    )

    map_fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        mapbox=dict(
            style="mapbox://styles/mapbox/satellite-streets-v12",  # Use 'mapbox://styles/mapbox/satellite-streets-v11' for satellite view
            accesstoken=MAPBOX_TOKEN,
            center=dict(lat=mid_lat, lon=mid_lon),
            zoom=11,
        ),
        showlegend=False,
        height=900,
    )
    return map_fig


def construct_page(name, data):
    # Create TS plot
    # ts_fig = plot_timeseries_duration(data)

    # Create the cross section plot
    crossec_fig = plot_cross_section(data)

    # Create a Scattermapbox trace
    map_fig = map_sat_image(name, data)

    content = html.Div(
        [
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H4(name, id="site-label"),
                    ]
                )
            ),
            dbc.Card(
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Div(
                                            [
                                                html.Label("Select Duration:"),
                                                dbc.RadioItems(
                                                    id="duration-selector",
                                                    className="btn-group",
                                                    inputClassName="btn-check",
                                                    labelClassName="btn btn-outline-primary",
                                                    labelCheckedClassName="active",
                                                    options=DURATIONS,
                                                    value=DURATIONS[-1][
                                                        "value"
                                                    ],
                                                ),
                                                dcc.Graph(
                                                    figure=go.Figure(),
                                                    id="time-series-plot",
                                                ),
                                            ],
                                            className="p-5 radio-group",
                                        )
                                    ],
                                    width=12,
                                ),
                            ],
                            align="center",
                        ),
                        # html.Br(),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [dcc.Graph(figure=crossec_fig)], width=6
                                ),
                                dbc.Col([dcc.Graph(figure=map_fig)], width=6),
                            ],
                            align="center",
                        ),
                        # html.Br(),
                        # dbc.Row([
                        #     dbc.Col([
                        #         dcc.Graph(figure=dem_fig)
                        #     ], width=6),
                        #     dbc.Col([
                        #         # dcc.Graph(figure=im_fig)
                        #     ], width=6),
                        # ], align="center"),
                    ]
                )
            ),
        ]
    )
    return content


def construct_overview_page(sites):
    return dcc.Graph(figure=map_overview(sites), id="map")
