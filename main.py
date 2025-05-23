import json
import pandas as pd
import folium
from folium import PolyLine
from src.predict_vol import pred_vol_for_time
from src.lookup import build_travel_time_lookup
from src.astar.graph import Graph
from src.astar.Astar import astar
from src.astar.heuristics import haversine_heuristic
from src.astar.yens_algo import k_shortest_paths

# -------------------------- USER INPUTS ---------------------------
# we have to use API endpoint to get the user inputs through the frontend
origin_id = 970
destination_ids = [4821]
selected_time = "2006-10-31 08:00"

#==============================================================



output_path = "generated_astar_input.txt" #overwritten every time the script is run

# map visualization settings
LAT_OFFSET = 0.00151
LON_OFFSET = 0.00134
map_center = [-37.84, 145.05]
# ------------------------------------------------------------------

print("Loading data and building graph...") # Debugging message

# load edge list
with open("datasets/processed/edges.json") as f:
    raw_edges = json.load(f)

edges = [tuple(edge) for edge in raw_edges if edge[0] != edge[1]]

# load SCATS location info using the same file as main_map.py 
df = pd.read_csv("datasets/processed/SCAT_cord.csv")  
location_df = df[["SCATS Number", "NB_LATITUDE", "NB_LONGITUDE"]].drop_duplicates()

print("Predicting traffic volumes...")
# predict the traffic volumes for selected time
volume_dict = pred_vol_for_time(selected_time)

print("Building travel time lookup...")
# travel time graph
travel_time_lookup = build_travel_time_lookup(edges, volume_dict, location_df)

# unique list of all nodes used in the edge list
all_nodes = set()
for a, b in travel_time_lookup.keys():
    all_nodes.add(a)
    all_nodes.add(b)

# coordinate mapping from SCATS location dataframe
node_coords = {}

for node_id in sorted(all_nodes):
    match = location_df[location_df["SCATS Number"] == node_id]
    if not match.empty:
        lat = match["NB_LATITUDE"].values[0]
        lon = match["NB_LONGITUDE"].values[0]
        node_coords[node_id] = (lon, lat)  # coordinate values X = longitude, Y = latitude
    else:
        node_coords[node_id] = (0, 0)  # just in case if missing so that no errors come up

print("Generating A* input file...") # debugging message

# ---- create the input file for A* algorithm ----
with open(output_path, "w") as f:
    # write nodes
    f.write("Nodes:\n")
    for node_id, (x, y) in node_coords.items():
        f.write(f"{int(node_id)}: ({x},{y})\n")

    # write edges
    f.write("\nEdges:\n")
    for (a, b), cost in travel_time_lookup.items():
        f.write(f"({int(a)}, {int(b)}): {round(cost, 2)}\n")

    # write origin
    f.write("\nOrigin:\n")
    f.write(str(origin_id) + "\n")

    # write destination
    f.write("\nDestinations:\n")
    f.write("; ".join(str(d) for d in destination_ids) + "\n")

print(f"A* input file saved to: {output_path}")

# load the graph from the generated input file
graph = Graph()
graph.load_file(output_path)

# use the first destination only 
# this can be expanded to loop through multiple destinations later
destination = list(graph.destination.keys())[0]

print("Finding top 5 fastest routes using Yen's algorithm...")
# # run yens k shortest paths algorithm for the top 5 fastest routes
# #https://neo4j.com/docs/graph-data-science/current/algorithms/yens/
paths = k_shortest_paths(graph, graph.origin, destination,
                        heuristic=lambda n1, n2, g: haversine_heuristic(n1, n2, g),
                        K=5)

# -----------------  OUTPUT -----------------
if not paths:
    print("\nNo paths found between the selected SCATS sites.")
    exit()

print("\nTOP 5 FASTEST ROUTES:")
for i, (path, cost) in enumerate(paths, 1):
    minutes = int(cost // 60)
    seconds = int(cost % 60)
    print(f"\nRoute {i}: {' -> '.join(str(node) for node in path)}")
    print(f"Estimated Travel Time: {minutes} min {seconds} sec ({round(cost, 2)} seconds)")

# -----------------  MAP VISUALISATION -----------------
print("\nGenerating map visualization...") # Debugging message
# Create a folium map centered at the average coordinates of the SCATS sites

# Create the map
m = folium.Map(location=map_center, zoom_start=13)

# all of tje unique nodes in the paths for visualisation
route_nodes = set()
for path, _ in paths:
    route_nodes.update(path)

# Plot ALL SCATS sites first (this will be the base layer)
all_plotted_nodes = set()
for _, row in location_df.iterrows():
    node_id = row["SCATS Number"]
    if node_id not in all_plotted_nodes:  # Prevent duplicates
        # Apply the same offset that was working before
        adjusted_lat = row["NB_LATITUDE"] + LAT_OFFSET
        adjusted_lon = row["NB_LONGITUDE"] + LON_OFFSET
        
        # use different colors for route nodes and normal nodes
        if node_id in route_nodes:
            color = "darkblue"
            fill_color = "lightblue"
            radius = 4
        else:
            color = "blue"
            fill_color = "blue"
            radius = 5
            
        folium.CircleMarker(
            location=[adjusted_lat, adjusted_lon],
            radius=radius,
            popup=f"SCATS {node_id}",
            color=color,
            fill=True,
            fill_color=fill_color
        ).add_to(m)
        all_plotted_nodes.add(node_id)

# use of different colors for different routes
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

    minutes = int(cost // 60)
    seconds = int(cost % 60)

    # add route polyline
    PolyLine(
        coords,
        color=colors[(i - 1) % len(colors)],
        weight=7 if i == 1 else 4,
        opacity=0.7,
        popup=f"Route {i} - {minutes} min {seconds} sec ({round(cost, 2)} sec)"
    ).add_to(m)

    # i =1 gets the fastest route
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
                         Fastest of Route<br>{minutes} min {seconds} sec
                    </div>
                '''
            )
        ).add_to(m)

# the origin and destination markers are added using coordinates from the first route
if paths:
    first_route_coords = []
    for node in paths[0][0]:
        match = location_df[location_df["SCATS Number"] == node]
        if not match.empty:
            lat = match["NB_LATITUDE"].values[0]
            lon = match["NB_LONGITUDE"].values[0]
            first_route_coords.append((lat + LAT_OFFSET, lon + LON_OFFSET))
    
    if first_route_coords:
        folium.Marker(
            location=first_route_coords[0],
            popup="Origin",
            icon=folium.Icon(color="green", icon="play")
        ).add_to(m)

        folium.Marker(
            location=first_route_coords[-1],
            popup="Destination",
            icon=folium.Icon(color="red", icon="stop")
        ).add_to(m)


# Save the map
map_output_path = "visualisation/templates/map_with_routes.html"
m.save(map_output_path)
print(f"Map with top 5 predicted routes saved as {map_output_path}")

print(f"- A* input file: {output_path}")
print(f"- Map visualization: {map_output_path}")


#  import json
# import pandas as pd
# from src.predict_vol import pred_vol_for_time
# from src.lookup import build_travel_time_lookup
# from src.astar.graph import Graph
# from src.astar.Astar import astar
# from src.astar.heuristics import haversine_heuristic
# from src.astar.yens_algo import k_shortest_paths

# # -------------------------- USER INPUTS ---------------------------
# # we have to use API endpoint to get the user inputs through the frontend
# origin_id = 3002
# destination_ids = [4324]

# selected_time = "2006-10-31 08:00"
# output_path = "generated_astar_input.txt" #overwritten every time the  script is run
# # ------------------------------------------------------------------


# # load edge list
# with open("datasets/processed/edges.json") as f:
#     raw_edges = json.load(f)

# edges = [tuple(edge) for edge in raw_edges if edge[0] != edge[1]]

# # Load SCATS location info
# df = pd.read_csv("datasets/processed/df_15min.csv")
# location_df = df[["SCATS Number", "NB_LATITUDE", "NB_LONGITUDE"]].drop_duplicates()

# # predict the traffic volumes for selected time
# volume_dict = pred_vol_for_time(selected_time)

# #  travel time graph. 
# travel_time_lookup = build_travel_time_lookup(edges, volume_dict, location_df) #on the go, so its not rquired to be saved

# #  unique list of all nodes used in the edge list
# all_nodes = set()
# for a, b in travel_time_lookup.keys():
#     all_nodes.add(a)
#     all_nodes.add(b)

# # coordinate mapping from SCATS location dataframe
# node_coords = {}

# for node_id in sorted(all_nodes):
#     match = location_df[location_df["SCATS Number"] == node_id]
#     if not match.empty:
#         lat = match["NB_LATITUDE"].values[0]
#         lon = match["NB_LONGITUDE"].values[0]
#         node_coords[node_id] = (lon, lat)  # cooridnate values X = longitude, Y = latitude
#     else:
#         node_coords[node_id] = (0, 0)  # just in case if missing so that no erros come up


# # ---- create the input file for A* algorithm ----
# with open(output_path, "w") as f:
#     # Write nodes
#     f.write("Nodes:\n")
#     for node_id, (x, y) in node_coords.items():
#         f.write(f"{int(node_id)}: ({x},{y})\n")


#     # Write edges
#     f.write("\nEdges:\n")
#     for (a, b), cost in travel_time_lookup.items():
#         f.write(f"({int(a)}, {int(b)}): {round(cost, 2)}\n")


#     # Write origin
#     f.write("\nOrigin:\n")
#     f.write(str(origin_id) + "\n")

#     # Write destination(s)
#     f.write("\nDestinations:\n")
#     f.write("; ".join(str(d) for d in destination_ids) + "\n")

# print(f" A* input file saved to: {output_path}")

# # load the graph from the generated input file
# graph = Graph()
# graph.load_file(output_path)

# # use the first destination only 
# # this can be expanded to loop through multiple destinations later
# destination = list(graph.destination.keys())[0]

# # run yens k shortest paths algorithm for the top 5 fastest routes
# #https://neo4j.com/docs/graph-data-science/current/algorithms/yens/

# paths = k_shortest_paths(graph, graph.origin, destination,
#                               heuristic=lambda n1, n2, g: haversine_heuristic(n1, n2, g),
#                               K=5)

# # -----------------  OUTPUT -----------------
# #this should be displayed on the frontend when implemeneted 
# #try to implement by next friday



# if not paths:
#     print("\n No paths found between the selected SCATS sites.")
# else:
#     print("\n TOP 5 FASTEST ROUTES:")
#     for i, (path, cost) in enumerate(paths, 1):
#         minutes = int(cost // 60)
#         seconds = int(cost % 60)
#         print(f"\nRoute {i}: {' -> '.join(str(node) for node in path)}")
#         print(f"Estimated Travel Time: {minutes} min {seconds} sec ({round(cost, 2)} seconds)")


