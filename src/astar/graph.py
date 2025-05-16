class Graph:
    def __init__(self):
        
        self.nodes = {}
        self.edges = {}
        self.origin = None
        self.destination = {}

# Add a node to the graph
    def add_node(self, node_no, x, y):

        self.nodes[node_no] = (x, y)
    
# Add an edge to the graph
    def add_edge(self, node1, node2, path_cost):

        self.edges[(node1, node2)] = path_cost

# Get path cost

    def path_cost(self, node1, node2):

        return self.edges.get((node1, node2))
    
# Get the neighbors of a node
    def neighbors(self, node):

        neighbors = []

        for (n1,n2),cost in self.edges.items():
            if n1 == node:
                neighbors.append((n2, cost))
        
        return neighbors
    
# Get details from input file

    def load_file(self,filename):

        section = None

        with open(filename, 'r') as File:
                
                for line in File:
                    line = line.strip()
                    if line == "":
                        continue

                    # Saves the current states as what sections are being read
                    if line[0] == 'N':
                        section = 'N' 
                        continue
                    elif line[0] == 'E':
                        section = 'E'
                        continue
                    elif line[0] == 'O':
                        section = 'O'
                        continue
                    elif line[0] == 'D':
                        section = 'D'
                        continue    

                    
                    if section == 'N':

                        parts = line.split(":")
                        node_no = int(parts[0].strip())
                        XYcords = parts[1].strip().strip("()").split(",")
                        x = float(XYcords[0])  # changed for longitude since its float
                        y = float(XYcords[1])  # same thing for latitude

                        self.add_node(node_no, x, y)

                    elif section == 'E':

                        parts = line.split(":")
                        nodes = parts[0].strip().strip("()").split(",")
                        node1 = int(nodes[0])
                        node2 = int(nodes[1])
                        path_cost = float(parts[1])
                        self.add_edge(node1, node2, path_cost)
                        
                    elif section == 'O':

            
                        self.origin = int(line.strip())
                    
                    elif section == 'D':

                        parts = line.split(";")
                        
                        for i in  parts:
                            self.destination[int(i.strip())] = True

                            