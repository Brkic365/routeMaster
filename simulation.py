# simulation.py

class TrafficSimulator:
    def __init__(self, graph):
        self.graph = graph
        # Track changed edges to allow resetting
        self.affected_edges = set() 

    def apply_jam(self, u, v, factor=5.0):
        """ Slows down traffic on the edge between u and v by a given factor. """
        self._update_edge(u, v, factor_multiplier=factor, is_blocked=False)
        self.affected_edges.add((u, v))

    def block_road(self, u, v):
        """ Blocks the road completely (sets weight to infinity). """
        self._update_edge(u, v, is_blocked=True)
        self.affected_edges.add((u, v))

    def reset_all(self):
        """ Resets all modified roads to their original state. """
        print("Resetting traffic...")
        for u, v in self.affected_edges:
            # Restore original weights
            self._reset_edge(u, v)
            self._reset_edge(v, u) # And the reverse direction
        self.affected_edges.clear()

    def _update_edge(self, u, v, factor_multiplier=1.0, is_blocked=False):
        """ Internal helper to update edge weight. """
        if u in self.graph.edges:
            for edge in self.graph.edges[u]:
                if edge['to'] == v:
                    if is_blocked:
                        edge['weight'] = float('infinity')
                        edge['status'] = 'blocked' # For visualization
                    else:
                        edge['weight'] = edge['base_weight'] * factor_multiplier
                        edge['status'] = 'jammed'
                    break
        
        # Update reverse direction if it exists (bidirectional graph)
        if v in self.graph.edges:
            for edge in self.graph.edges[v]:
                if edge['to'] == u:
                    if is_blocked:
                        edge['weight'] = float('infinity')
                        edge['status'] = 'blocked'
                    else:
                        edge['weight'] = edge['base_weight'] * factor_multiplier
                        edge['status'] = 'jammed'
                    break

    def _reset_edge(self, u, v):
        if u in self.graph.edges:
            for edge in self.graph.edges[u]:
                if edge['to'] == v:
                    edge['weight'] = edge['base_weight']
                    edge.pop('status', None) # Remove status