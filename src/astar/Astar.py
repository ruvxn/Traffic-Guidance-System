from .heuristics import euclidean_distance

from queue import PriorityQueue


class ASTAR:
    def search(self, graph, origin, destinations, heuristic):

        visited_count = 0 
        target = list(destinations.keys())[0]

        OpenSet = PriorityQueue()  #creates OpenSet as a priorityQueue 
        
        OpenSet.put((0,0, [origin]))  #pushes origin into the OpenSet 

        Parent = set() #initalizes an empty set for visted (Since no nodes have been visited yet)
        
        while not OpenSet.empty():  # Opens a loop that will only end when the Prio queue (Openset) is empty
            
            Fscore, SumCost, Path = OpenSet.get()    #from the open set, it retrieves the Fscore and cost/weight + its path (for the first time looping it will be the origin node)
            
            CurrentNode = Path[-1]   
            
            if CurrentNode == target: 
                print("Destination Node Found!:", Path) #debugging 
                print("Total nodes visited:", visited_count)
                
                return Path, SumCost
            
            if CurrentNode not in Parent: 
                Parent.add(CurrentNode) 
                #print("Entered second if") #debugging
                for neighbor, Weight in graph.neighbors(CurrentNode): #referenced your code (assume my python is why the "graph.neighors" isn't working check on yours)
                    #print("Entered For loop") #debugging
                    if neighbor not in Parent: 
                        #print("Entered if statement 3")
                        Gscore = (SumCost + Weight)
                        #print(Gscore) #debugging
                        Hscore = heuristic(neighbor, target, graph) #check this since my imports are being cooked #calls the Eculidean function and the return value is assigned to Hscore 
                        #print(Hscore) #debugging
                        Fscore = (Hscore + Gscore) #Fscore is used to determine is the algorithm is moving in the correct direction. 

                        
                        #print(Fscore) #debugging
                        UpdatedPath = Path + [neighbor]    #updates the path with the new path 
                        OpenSet.put((Fscore, Gscore, UpdatedPath)) #this into the openset (prio q)

        return None, float('inf')




def astar(graph, origin, destination, heuristic):
    searcher = ASTAR()
    return searcher.search(graph, origin, {destination: True}, heuristic)



        



