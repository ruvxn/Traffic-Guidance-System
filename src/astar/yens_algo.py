import copy
from src.astar.Astar import astar
from queue import PriorityQueue

def k_shortest_paths(graph, origin, destination, heuristic, K=5):
    paths = []
    seen = set()

    #get the hsortest path using ASTAR
    first_path, first_cost = astar(graph, origin, destination, heuristic)
    if first_path is None:
        return []

    paths.append((first_path, first_cost))
    candidates = PriorityQueue()

    for k in range(1, K):
        for i in range(len(paths[-1][0]) - 1):
            spur_node = paths[-1][0][i]
            root_path = paths[-1][0][:i + 1]

            #teporary copy to remove edges, to prevent the algorithm from returning the same path
            graph_copy = copy.deepcopy(graph)

            for p, _ in paths:
                if p[:i + 1] == root_path and len(p) > i + 1:
                    node_a = p[i]
                    node_b = p[i + 1]
                    if (node_a, node_b) in graph_copy.edges:
                        del graph_copy.edges[(node_a, node_b)]

            for node in root_path[:-1]:
                if node in graph_copy.nodes:
                    del graph_copy.nodes[node]

            #recalculate the path from the spur node to the destination
            spur_path, spur_cost = astar(graph_copy, spur_node, destination, heuristic)
            if spur_path is not None:
                total_path = root_path[:-1] + spur_path
                total_cost = compute_path_cost(total_path, graph)
                if tuple(total_path) not in seen:
                    candidates.put((total_cost, total_path))
                    seen.add(tuple(total_path))

        if candidates.empty():
            break

        cost, path = candidates.get()
        paths.append((path, cost))

    return paths

def compute_path_cost(path, graph):
    cost = 0
    for i in range(len(path) - 1):
        cost += graph.path_cost(path[i], path[i + 1])
    return cost
