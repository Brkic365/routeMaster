import xml.etree.ElementTree as ET
from models import Graph, POI
from utils import haversine_distance
from collections import deque

def keep_only_largest_component(graph):
    """
    Zadržava samo najveću grupu povezanih ulica.
    """
    print("Filtriranje izoliranih otoka...")
    
    # 1. Pronađi sve komponente
    visited = set()
    largest_component = set()
    
    for node_id in graph.nodes:
        if node_id not in visited:
            current_component = set()
            # Koristimo listu kao stack za DFS/BFS
            stack = [node_id]
            visited.add(node_id)
            current_component.add(node_id)
            
            while stack:
                curr = stack.pop()
                # Pazi: get_neighbors može vratiti edges koji pokazuju na nepostojeće čvorove
                # ako parser nije savršen, ali ovdje je bitno samo traverseanje
                for edge in graph.get_neighbors(curr):
                    neighbor = edge['to']
                    if neighbor in graph.nodes and neighbor not in visited:
                        visited.add(neighbor)
                        current_component.add(neighbor)
                        stack.append(neighbor)
            
            if len(current_component) > len(largest_component):
                largest_component = current_component

    print(f"Zadržavam {len(largest_component)} od {len(graph.nodes)} čvorova.")
    
    # 2. Obriši čvorove koji nisu u glavnoj komponenti
    # Moramo napraviti listu ključeva jer ne smijemo mijenjati dict dok iteriramo
    all_nodes = list(graph.nodes.keys())
    for n in all_nodes:
        if n not in largest_component:
            del graph.nodes[n]
            if n in graph.edges:
                del graph.edges[n]

    # 3. KLJUČNI POPRAVAK: Očisti "viseće" veze (dangling edges)
    # Prolazimo kroz preostale čvorove i mičemo veze prema obrisanim čvorovima
    for n in largest_component:
        if n in graph.edges:
            # Zadrži samo one veze gdje odredište ('to') još uvijek postoji
            original_edges = graph.edges[n]
            cleaned_edges = [
                edge for edge in original_edges 
                if edge['to'] in largest_component
            ]
            graph.edges[n] = cleaned_edges


def load_osm_data(filepath):
    print(f"Parsiranje: {filepath}...")
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
    except Exception as e:
        print(f"Greška: {e}")
        return None

    graph = Graph()
    
    for node in root.findall('node'):
        graph.add_node(node.get('id'), node.get('lat'), node.get('lon'))
        
        # Check for POI tags
        tags = {tag.get('k'): tag.get('v') for tag in node.findall('tag')}
        poi_type = None
        if 'amenity' in tags: poi_type = tags['amenity']
        elif 'shop' in tags: poi_type = 'shop'
        elif 'leisure' in tags: poi_type = tags['leisure']
        
        if poi_type:
            name = tags.get('name', 'Unknown')
            graph.pois.append(POI(node.get('lat'), node.get('lon'), poi_type, name))

    allowed_highways = {
        'motorway', 'trunk', 'primary', 'secondary', 'tertiary', 
        'unclassified', 'residential', 'living_street', 'service',
        'motorway_link', 'trunk_link', 'primary_link', 
        'secondary_link', 'tertiary_link'
    }

    for way in root.findall('way'):
        tags = {tag.get('k'): tag.get('v') for tag in way.findall('tag')}
        
        if 'highway' in tags and tags['highway'] in allowed_highways:
            nd_refs = [nd.get('ref') for nd in way.findall('nd')]
            road_type = tags['highway']
            name = tags.get('name', 'Unknown Road')
            is_oneway = tags.get('oneway') == 'yes'

            for i in range(len(nd_refs) - 1):
                u, v = nd_refs[i], nd_refs[i+1]
                if u not in graph.nodes or v not in graph.nodes: continue
                
                u_node, v_node = graph.nodes[u], graph.nodes[v]
                dist = haversine_distance(u_node.lat, u_node.lon, v_node.lat, v_node.lon)
                
                graph.add_edge(u, v, dist, road_type, name)
                
                # Update Search Index
                if name and name != "Unknown Road":
                    # Store tuple (u, v) or just u? Storing u is enough to find the node.
                    # Actually storing u_id is better to jump to node.
                    graph.street_index[name.lower()].append(u)

                if not is_oneway:
                    graph.add_edge(v, u, dist, road_type, name)

    if len(graph.nodes) > 0:
        keep_only_largest_component(graph)
        
    return graph