from server_requests import get_latest_data, get_measurements
import pandas as pd
import xmltodict


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
        print(all_ys)        
        sites[site]["ymin"] = min(all_ys)
        sites[site]["ymax"] = max(all_ys)
        sites[site]["yrange"] = sites[site]["ymax"] - sites[site]["ymin"] 
        
        sites[site]["ylims"] = (
            sites[site]["ymin"] - 0.1*sites[site]["yrange"],
            sites[site]["ymax"] + 0.1*sites[site]["yrange"]
        )
    
    # fig.add_hline(y=split_df['RADAR LEVEL : '].iloc[0],
    #               annotation_text='RADAR LEVEL',
    #               line_dash='dot')
    # fig.add_hline(y=split_df['PAVER LEVEL'].iloc[0],
    #               annotation_text='PAVER LEVEL')
    # fig.add_hline(y=split_df['CULVERT INVERT'].iloc[0],
    #               annotation_text='CULVERT INVERT')
    # fig.update_layout(yaxis_range=ylims)
    # graphs += [fig]

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
