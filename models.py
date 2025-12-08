class Node:
    def __init__(self, id, lat, lon):
        self.id = id
        self.lat = float(lat)
        self.lon = float(lon)

    def __repr__(self):
        return f"Node({self.id}, {self.lat}, {self.lon})"

class POI:
    def __init__(self, lat, lon, type_name, name):
        self.lat = float(lat)
        self.lon = float(lon)
        self.type = type_name # 'school', 'shop', 'park'...
        self.name = name

from collections import defaultdict

class Graph:
    def __init__(self):
        self.nodes = {}  # id -> Node objekt
        self.edges = {} 
        self.pois = []   # List of POI objects 
        self.street_index = defaultdict(list) # name -> list of edge_ids 

    def add_node(self, id, lat, lon):
        self.nodes[id] = Node(id, lat, lon)
        self.edges[id] = []

    def add_edge(self, u, v, weight, road_type="unknown", name="Unknown Road"):
        # Add directed edge. For bidirectional roads, this is called twice.
        if u in self.nodes and v in self.nodes:
            self.edges[u].append({'to': v, 
                                  'weight': weight, 
                                  'base_weight': weight,
                                  'type': road_type,
                                  'name': name})
        
    def get_neighbors(self, node_id):
        return self.edges.get(node_id, [])