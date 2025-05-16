from src.distance_calc import haversine_distance
from src.travel_time_calc import travel_time_calculator
import pandas as pd

def compute_travel_time(site_a, site_b, predicted_volume, location_df):
    
    distance_km = haversine_distance(site_a, site_b, location_df)

    if distance_km is None:
        return None  

    return travel_time_calculator(predicted_volume, distance_km)

def build_travel_time_lookup(edges, volume_dict, location_df):
    
    travel_times = {}

    

    for site_a, site_b in edges:
        volume = volume_dict.get(site_b)

        if volume is None:
            continue  # Skip if we don't have a prediction

        time = compute_travel_time(site_a, site_b, volume, location_df)

        if time is not None:
            travel_times[(site_a, site_b)] = time

    return travel_times
