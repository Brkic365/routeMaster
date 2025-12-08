import heapq
from utils import haversine_distance

def reconstruct_path(previous_nodes, start, end):
    """
    Vraća listu ID-ova čvorova od starta do cilja.
    Radi 'backtracking' od cilja prema startu.
    """
    path = []
    current_node = end
    
    # Ako cilj nije posjećen (nema ga u previous), nema puta
    if current_node not in previous_nodes:
        return []

    while current_node is not None:
        path.append(current_node)
        current_node = previous_nodes[current_node]
    
    path.reverse() # Okreni listu (Cilj->Start u Start->Cilj)
    
    if path[0] != start:
        return []
        
    return path

def a_star(graph, start_id, end_id):
    """
    A* (A-Star) algoritam za najkraći put.
    
    Koristi formulu: f(n) = g(n) + h(n)
    - g(n): Stvarna cijena puta od starta do n
    - h(n): Heuristika (zračna udaljenost od n do cilja)
    """
    print(f"Pokrećem A*: {start_id} -> {end_id}")
    
    # Priority Queue: pohranjuje (f_score, id_čvora)
    # heapq uvijek drži onaj s najmanjim f_score na vrhu
    pq = [(0, start_id)]
    
    # g_score: Najkraća poznata udaljenost od starta do svakog čvora
    # Inicijalno beskonačno za sve osim starta
    g_score = {node: float('infinity') for node in graph.nodes}
    g_score[start_id] = 0
    
    # Rječnik za rekonstrukciju puta
    previous_nodes = {node: None for node in graph.nodes}
    
    visited_count = 0

    while pq:
        # 1. Uzmi čvor koji "najviše obećava" (najmanji f)
        current_f, current_node = heapq.heappop(pq)
        
        # Ako smo došli do cilja, gotovo!
        if current_node == end_id:
            print(f"✅ Cilj pronađen! Obrađeno čvorova: {visited_count}")
            path = reconstruct_path(previous_nodes, start_id, end_id)
            return path, g_score[end_id]

        visited_count += 1
        
        # 2. Provjeri sve susjede
        for edge in graph.get_neighbors(current_node):
            neighbor = edge['to']
            weight = edge['weight'] # Ovdje simulacija kasnije mijenja težinu (gužve)
            
            # g(n) = put do trenutnog + težina do susjeda
            tentative_g = g_score[current_node] + weight
            
            # Ako smo našli brži put do susjeda nego prije...
            if tentative_g < g_score[neighbor]:
                previous_nodes[neighbor] = current_node
                g_score[neighbor] = tentative_g
                
                # Računamo heuristiku (h)
                neighbor_obj = graph.nodes[neighbor]
                end_obj = graph.nodes[end_id]
                
                h_score = haversine_distance(
                    neighbor_obj.lat, neighbor_obj.lon,
                    end_obj.lat, end_obj.lon
                )
                
                # f = g + h
                f_score = tentative_g + h_score
                heapq.heappush(pq, (f_score, neighbor))
                
    # Ako se petlja završi a nismo našli cilj:
    return [], float('infinity')

def generate_instructions(graph, path):
    """ Generira tekstualne upute za navigaciju. """
    if not path or len(path) < 2:
        return ["Stigli ste na odredište."]
        
    instructions = []
    current_street = None
    segment_dist = 0
    
    # helper da nađemo ime ulice
    def get_street_name(u, v):
        if u in graph.edges:
            for e in graph.edges[u]:
                if e['to'] == v:
                    return e.get('name', 'Nepoznata ulica')
        return "Nepoznata ulica"

    # Prva ulica
    start_street = get_street_name(path[0], path[1])
    current_street = start_street
    instructions.append(f"Krenite ulicom {start_street}")
    
    for i in range(len(path) - 1):
        u, v = path[i], path[i+1]
        
        # Dohvati udaljenost
        dist = 0
        if u in graph.edges:
            for e in graph.edges[u]:
                if e['to'] == v:
                    dist = e['weight']
                    break
        
        name = get_street_name(u, v)
        
        if name != current_street:
            # Nova instrukcija
            dist_text = f"{int(segment_dist)}m" if segment_dist > 1000 else f"{int(segment_dist)}m"
            instructions.append(f"Vozite {dist_text}, zatim skrenite u {name}")
            current_street = name
            segment_dist = 0
        
        segment_dist += dist
        
    # Zadnja dionica
    instructions.append(f"Vozite {int(segment_dist)}m do cilja.")
    return instructions