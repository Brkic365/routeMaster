import heapq
import math
from utils import calculate_turn_dir, haversine_distance
from models import Graph, Node

def reconstruct_path(previous_nodes: dict[str, str | None], start: str, end: str) -> list[str]:
    """
    Reconstructs the path from start to end using the came_from map.
    Returns a list of node IDs.
    """
    path = []
    current_node = end
    
    if current_node not in previous_nodes:
        return []

    while current_node is not None:
        path.append(current_node)
        current_node = previous_nodes[current_node]
    
    path.reverse() 
    
    if path[0] != start:
        return []
        
    return path

def a_star(graph: Graph, start_id: str, end_id: str) -> tuple[list[str], float]:
    """
    A* algorithm with traffic awareness and Turn Costs.
    Penalty is added for sharp turns to encourage smoother paths.
    """
    # Priority Queue tuple: (f_score, node_id)
    pq = [(0.0, start_id)]
    
    g_score = {node: float('infinity') for node in graph.nodes}
    g_score[start_id] = 0.0
    
    came_from = {node: None for node in graph.nodes}
    
    while pq:
        current_f, current_node_id = heapq.heappop(pq)
        
        if current_node_id == end_id:
            return reconstruct_path(came_from, start_id, end_id), g_score[end_id]
            
        # Optimization: Lazy deletion
        current_h = haversine_distance(graph.nodes[current_node_id].lat, graph.nodes[current_node_id].lon, 
                                     graph.nodes[end_id].lat, graph.nodes[end_id].lon)
                                     
        if current_f > g_score[current_node_id] + current_h + 1e-9: # Epsilon for float comparisons
            continue

        u_node = graph.nodes[current_node_id]
        parent_id = came_from.get(current_node_id)
        
        for edge in graph.get_neighbors(current_node_id):
            neighbor_id = edge['to']
            v_node = graph.nodes[neighbor_id]
            
            # 1. Base Weight (Traffic)
            weight = edge['weight']
            status = edge.get('status')
            if status == 'jammed': weight *= 5.0
            elif status == 'blocked': weight = float('inf')
            
            # 2. Turn Penalty
            turn_penalty = 0
            if parent_id:
                p_node = graph.nodes[parent_id]
                # Angle Calculation
                # Vector P->U
                v1x, v1y = u_node.lat - p_node.lat, u_node.lon - p_node.lon
                # Vector U->V
                v2x, v2y = v_node.lat - u_node.lat, v_node.lon - u_node.lon
                
                # Dot product
                len1 = math.hypot(v1x, v1y)
                len2 = math.hypot(v2x, v2y)
                
                if len1 > 0 and len2 > 0:
                    dot = (v1x * v2x + v1y * v2y) / (len1 * len2)
                    dot = max(-1.0, min(1.0, dot))
                    # If dot is near 1, it's straight. If dot < 0.5 (60 deg), penalty.
                    if dot < 0.5:
                        turn_penalty = 20.0 # equivalent to 20m detour
            
            tentative_g = g_score[current_node_id] + weight + turn_penalty
            
            if tentative_g < g_score[neighbor_id]:
                came_from[neighbor_id] = current_node_id
                g_score[neighbor_id] = tentative_g
                
                # Heuristic
                h = haversine_distance(v_node.lat, v_node.lon, graph.nodes[end_id].lat, graph.nodes[end_id].lon)
                heapq.heappush(pq, (tentative_g + h, neighbor_id))
                
    return [], float('infinity')

def generate_instructions(graph, path):
    """ Generates turn-by-turn navigation instructions from a node path. """
    if not path or len(path) < 2:
        return ["You have reached your destination."]
        
    instructions = []
    current_street = None
    segment_dist = 0
    
    def get_street_name(u, v):
        if u in graph.edges:
            for e in graph.edges[u]:
                if e['to'] == v:
                    return e.get('name', 'Unknown Road')
        return "Unknown Road"

    # Initial street
    start_street = get_street_name(path[0], path[1])
    current_street = start_street
    instructions.append(f"Head on {start_street}")
    
    for i in range(len(path) - 1):
        u, v = path[i], path[i+1]
        
        # Get distance
        dist = 0
        if u in graph.edges:
            for e in graph.edges[u]:
                if e['to'] == v:
                    dist = e['weight']
                    break
        
        # Safety check for infinite distances (Crash prevention)
        if math.isinf(dist) or math.isnan(dist) or dist > 1e9:
             return ["Route blocked. Destination unreachable."]
        
        name = get_street_name(u, v)
        
        if name != current_street:
            # New Instruction
            dist_text = f"{int(segment_dist)}m"
            instructions.append(f"Go {dist_text}, then turn onto {name}")
            current_street = name
            segment_dist = 0
        
        segment_dist += dist
        
    # Final segment safety check
    if math.isinf(segment_dist) or math.isnan(segment_dist):
         return ["Route blocked. Destination unreachable."]

    instructions.append(f"Go {int(segment_dist)}m to destination.")
    return instructions