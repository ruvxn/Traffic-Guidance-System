import numpy as np

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  
    lat1_rad, lon1_rad = np.radians(lat1), np.radians(lon1)
    lat2_rad, lon2_rad = np.radians(lat2), np.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = np.sin(dlat / 2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    
    return R * c

def haversine_distance(scats_a, scats_b, location_df):
    try:
        row_a = location_df[location_df["SCATS Number"] == scats_a].iloc[0]
        row_b = location_df[location_df["SCATS Number"] == scats_b].iloc[0]
        
        return haversine(row_a["NB_LATITUDE"], row_a["NB_LONGITUDE"],
                         row_b["NB_LATITUDE"], row_b["NB_LONGITUDE"])
    except IndexError:
        print(f"Coordinates not found for SCATS {scats_a} or {scats_b}.")
        return None
