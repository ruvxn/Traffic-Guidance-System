import json
import pandas as pd
from src.predict_vol import pred_vol_for_time
from src.lookup import build_travel_time_lookup
from src.astar.graph import Graph
from src.astar.Astar import astar
from src.astar.heuristics import haversine_heuristic

# -------------------------- USER INPUTS ---------------------------
# we have to use API endpoint to get the user inputs through the frontend
origin_id = 4057
destination_ids = [3180]

selected_time = "2006-10-31 08:00"
output_path = "generated_astar_input.txt" #overwritten every time the  script is run
# ------------------------------------------------------------------


# load edge list
with open("datasets/processed/edges.json") as f:
    raw_edges = json.load(f)

edges = [tuple(edge) for edge in raw_edges if edge[0] != edge[1]]

# Load SCATS location info
df = pd.read_csv("datasets/processed/df_15min.csv")
location_df = df[["SCATS Number", "NB_LATITUDE", "NB_LONGITUDE"]].drop_duplicates()

# predict the traffic volumes for selected time
volume_dict = pred_vol_for_time(selected_time)

#  travel time graph. 
travel_time_lookup = build_travel_time_lookup(edges, volume_dict, location_df) #on the go, so its not rquired to be saved

#  unique list of all nodes used in the edge list
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
        node_coords[node_id] = (lon, lat)  # cooridnate values X = longitude, Y = latitude
    else:
        node_coords[node_id] = (0, 0)  # just in case if missing so that no erros come up


# ---- create the input file for A* algorithm ----
with open(output_path, "w") as f:
    # Write nodes
    f.write("Nodes:\n")
    for node_id, (x, y) in node_coords.items():
        f.write(f"{node_id}: ({x},{y})\n")

    # Write edges
    f.write("\nEdges:\n")
    for (a, b), cost in travel_time_lookup.items():
        f.write(f"({a}, {b}): {round(cost, 2)}\n")

    # Write origin
    f.write("\nOrigin:\n")
    f.write(str(origin_id) + "\n")

    # Write destination(s)
    f.write("\nDestinations:\n")
    f.write("; ".join(str(d) for d in destination_ids) + "\n")

print(f" A* input file saved to: {output_path}")

# load the graph from the generated input file
graph = Graph()
graph.load_file(output_path)

# use the first destination only 
# this can be expanded to loop through multiple destinations later
destination = list(graph.destination.keys())[0]

# run Astar search
path, cost = astar(graph, graph.origin, destination,heuristic=lambda n1, n2, g: haversine_heuristic(n1, n2, g))


# -----------------  OUTPUT -----------------
#this should be displayed on the frontend when implemeneted 
#try to implement by next friday
if path is None:
    print("\n No path found between the selected SCATS sites.")
else:
    print("\n FASTEST PATH FOUND:")
    print(" -> ".join(str(node) for node in path))

    minutes = int(cost // 60)
    seconds = int(cost % 60)
    print(f"\n  Estimated Travel Time: {minutes} minutes {seconds} seconds ({round(cost, 2)} seconds)")


