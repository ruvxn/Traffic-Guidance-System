import folium
import pandas as pd
from folium import PolyLine
from src.astar.yens_algo import k_shortest_paths
from src.astar.graph import Graph
from src.predict_vol import pred_vol_for_time
from src.lookup import build_travel_time_lookup
from src.astar.heuristics import haversine_heuristic

# cleaned scats dataset
df = pd.read_csv("datasets/processed/SCAT_cord.csv")
location_df = df[["SCATS Number", "NB_LATITUDE", "NB_LONGITUDE"]].drop_duplicates()

# === Step 2: Create the base map ===
#map_center = [-37.84, 145.05]
#m = folium.Map(location=map_center, zoom_start=13)

# Plot SCATS sites
#for _, row in location_df.iterrows():
 #   folium.CircleMarker(
   #     location=[row["NB_LATITUDE"], row["NB_LONGITUDE"]],
    #    radius=3,
    #    popup=str(row["SCATS Number"]),
     #   color="blue",
       # fill=True,
    #    fill_color="blue"
   # ).add_to(m)

# create initial map
map_center = [-37.84, 145.05]
m = folium.Map(location=map_center, zoom_start=13)



import json
with open("datasets/processed/edges.json") as f:
    raw_edges = json.load(f)
edges = [tuple(edge) for edge in raw_edges if edge[0] != edge[1]]

#----------- HARDCODED VALUES----------
#----- chanfe later with user inputs-----
# \------ this is just for testing ------

selected_time = "2006-10-31 08:00"
origin_id = 4270
destination_id = 4034

#--------------------------------------

volume_dict = pred_vol_for_time(selected_time)
travel_time_lookup = build_travel_time_lookup(edges, volume_dict, location_df)

# Build graph and load paths
output_path = "generated_astar_input.txt"
with open(output_path, "w") as f:
    
    f.write("Nodes:\n")
    for _, row in location_df.iterrows():
        node_id = int(row["SCATS Number"])  
        lon = row["NB_LONGITUDE"]
        lat = row["NB_LATITUDE"]
        f.write(f"{node_id}: ({lon},{lat})\n")

    f.write("\nEdges:\n")
    for (a, b), cost in travel_time_lookup.items():
        f.write(f"({a}, {b}): {round(cost, 2)}\n")

    f.write("\nOrigin:\n" + str(origin_id) + "\n")
    f.write("\nDestinations:\n" + str(destination_id) + "\n")

graph = Graph()
graph.load_file(output_path)

#yens algorithm to find the top 5 routes
paths = k_shortest_paths(
    graph,
    origin_id,
    destination_id,
    heuristic=lambda n1, n2, g: haversine_heuristic(n1, n2, g),
    K=5
)


# find all unique nodes in the paths
route_nodes = set()
for path, _ in paths:
    route_nodes.update(path)

#offset created to handle the error with misaligning of the SCATS sites with the actual longitude latitude.
#this was done by comparing the SCATS cordinates with the actual location shown on google maps
LAT_OFFSET = 0.00151
LON_OFFSET = 0.00134



# plot SCATS sites
for _, row in location_df.iterrows():
    node_id = row["SCATS Number"]
    if node_id not in route_nodes:
        adjusted_lat = row["NB_LATITUDE"] + 0.00151
        adjusted_lon = row["NB_LONGITUDE"] + 0.00134
        folium.CircleMarker(
            location=[adjusted_lat, adjusted_lon],
            radius=3,
            popup=str(node_id),
            color="blue",
            fill=True,
            fill_color="blue"
        ).add_to(m)



# plor routes with different colors
colors = ["red", "blue", "green", "purple", "orange"]

for i, (path, cost) in enumerate(paths, 1):
    coords = []
    for node in path:
        match = location_df[location_df["SCATS Number"] == node]
        if not match.empty:
            lat = match["NB_LATITUDE"].values[0]
            lon = match["NB_LONGITUDE"].values[0]
            jitter = 0.000025 * (i - 1)  # adjust this factor as needed
            coords.append((lat + LAT_OFFSET + jitter, lon + LON_OFFSET + jitter))



    #folium.Marker(location=coords[0], popup="Origin", icon=folium.Icon(color="green", icon="play")).add_to(m)
    #folium.Marker(location=coords[-1], popup="Destination", icon=folium.Icon(color="red", icon="stop")).add_to(m)

    minutes = int(cost // 60)
    seconds = int(cost % 60)

    PolyLine(
        coords,
        color=colors[(i - 1) % len(colors)],
        weight=7 if i == 1 else 4,
        opacity=0.7,
        
        popup=f"Route {i} - {minutes} min {seconds} sec ({round(cost, 2)} sec)"

    ).add_to(m)

# this will show the details of the fastest route without having to hover
    if i == 1:
        mid_idx = len(coords) // 2
        midpoint = coords[mid_idx] 
     
        folium.Marker(
         location=midpoint,
            icon=folium.DivIcon(
                icon_size=(56,36),
                icon_anchor=(0,0),
                html=f'''
                    <div style="font-size: 10px; font-weight: bold; color: darkred;
                              background-color: white; border: 1px solid darkred; 
                              padding: 2px; border-radius: 6px;">
                         Fastest Route<br>{minutes} min {seconds} sec
                    </div>
             '''
        )
    ).add_to(m)
        
#overlay origin and destination markers
#this is a temporary fix since when i added a jitter to the routes, each route inside the loop got one marker each.
origin_coords = coords[0]
destination_coords = coords[-1]

folium.Marker(
    location=origin_coords,
    popup="Origin",
    icon=folium.Icon(color="green", icon="play")
).add_to(m)

folium.Marker(
    location=destination_coords,
    popup="Destination",
    icon=folium.Icon(color="red", icon="stop")
).add_to(m)



# overlay SCAT nodes 
#this is a temporary fix since when the routes are plotted the scats were overriden.

for node_id in route_nodes:
    match = location_df[location_df["SCATS Number"] == node_id]
    if not match.empty:
        lat = match["NB_LATITUDE"].values[0]
        lon = match["NB_LONGITUDE"].values[0]
        adjusted_lat = lat + LAT_OFFSET
        adjusted_lon = lon + LON_OFFSET
        folium.CircleMarker(
            location=[adjusted_lat, adjusted_lon],
            radius=3,
            color="blue",
            fill=True,
            fill_color="blue",
            popup=f"SCATS {node_id}"
        ).add_to(m)




m.save("visualisation/templates/map_with_routes.html")
print("Map with top 5 predicted routes saved as map_with_routes.html")
