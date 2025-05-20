import math
from src.distance_calc import haversine

def euclidean_distance(coord1, coord2):
    x1, y1 = coord1
    x2, y2 = coord2
    
    distance = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    return distance


#Assignment 2B update for longitude and latitude using haversine formula
#https://www.geeksforgeeks.org/haversine-formula-to-find-distance-between-two-points-on-a-sphere/
def haversine_heuristic(n1, n2, graph):
   
    if n1 not in graph.nodes or n2 not in graph.nodes:
        return float('inf')  # this fixes the error occured when integrating with yens_algo to prevent crash by returning very high cost

    lon1, lat1 = graph.nodes[n1]
    lon2, lat2 = graph.nodes[n2]

    return haversine(lat1, lon1, lat2, lon2)