class Node:
    """ Represents a single geographic point (node) in the OSM graph. """
    def __init__(self, id: str, lat: float, lon: float):
        self.id = id
        self.lat = float(lat)
        self.lon = float(lon)

    def __repr__(self):
        return f"Node({self.id}, {self.lat}, {self.lon})"

class POI:
    """ Represents a Point of Interest (e.g., School, Shop). """
    def __init__(self, lat: float, lon: float, type_name: str, name: str):
        self.lat = float(lat)
        self.lon = float(lon)
        self.type = type_name # 'school', 'shop', 'park'...
        self.name = name

from collections import defaultdict

class Graph:
    def __init__(self):
        self.nodes: dict[str, Node] = {}  # id -> Node objekt
        self.edges: dict[str, list[dict]] = {} 
        self.pois: list[POI] = []   # List of POI objects 
        self.street_index: dict[str, list[str]] = defaultdict(list) # name -> list of edge_ids 

    def add_node(self, id: str, lat: float, lon: float):
        self.nodes[id] = Node(id, lat, lon)
        self.edges[id] = []

    def add_edge(self, u: str, v: str, weight: float, road_type: str="unknown", name: str="Unknown Road"):
        # Add directed edge. For bidirectional roads, this is called twice.
        if u in self.nodes and v in self.nodes:
            self.edges[u].append({'to': v, 
                                  'weight': weight, 
                                  'base_weight': weight,
                                  'type': road_type,
                                  'name': name})
        
    def get_neighbors(self, node_id: str) -> list[dict]:
        return self.edges.get(node_id, [])