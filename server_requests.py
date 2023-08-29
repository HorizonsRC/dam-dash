import requests
import urllib


def get_sites():
    payload = {
        "Service": "Hilltop",
        "Request": "SiteList",
        "Location": "Yes",
        "Target": "HtmlSelect"
    }
    params = urllib.parse.urlencode(payload, quote_via=urllib.parse.quote)
    url = "http://hilltopserver.horizons.govt.nz/environmentaldata.hts"
    return requests.get(url, params=params)


def get_measurements(site_name):
    payload = {
        "Service": "Hilltop",
        "Request": "MeasurementList",
        "Site": site_name,
        "Target": "HtmlSelect"
    }
    params = urllib.parse.urlencode(payload, quote_via=urllib.parse.quote)
    url = "http://hilltopserver.horizons.govt.nz/environmentaldata.hts"
    return requests.get(url, params=params)


def get_latest_data(site_name, measurement):
    payload = {
        "Service": "Hilltop",
        "Request": "GetData",
        "Site": site_name,
        "Measurement": measurement,
    }
    params = urllib.parse.urlencode(payload, quote_via=urllib.parse.quote)
    url = "http://hilltopserver.horizons.govt.nz/environmentaldata.hts"
    return requests.get(url, params=params)
