# simulation.py

class TrafficSimulator:
    def __init__(self, graph):
        self.graph = graph
        # Pamtimo promijenjene ceste da ih možemo resetirati
        self.affected_edges = set() 

    def apply_jam(self, u, v, factor=5.0):
        """ Usporava promet na cesti između u i v za zadani faktor. """
        self._update_edge(u, v, factor_multiplier=factor, is_blocked=False)
        self.affected_edges.add((u, v))

    def block_road(self, u, v):
        """ Potpuno zatvara cestu (težina = infinity). """
        self._update_edge(u, v, is_blocked=True)
        self.affected_edges.add((u, v))

    def reset_all(self):
        """ Vraća sve ceste u normalu. """
        print("Resetiranje prometa...")
        for u, v in self.affected_edges:
            # Vrati originalne težine
            self._reset_edge(u, v)
            self._reset_edge(v, u) # I suprotni smjer
        self.affected_edges.clear()

    def _update_edge(self, u, v, factor_multiplier=1.0, is_blocked=False):
        """ Interna funkcija za ažuriranje težine brida. """
        if u in self.graph.edges:
            for edge in self.graph.edges[u]:
                if edge['to'] == v:
                    if is_blocked:
                        edge['weight'] = float('infinity')
                        edge['status'] = 'blocked' # Za vizualizaciju
                    else:
                        edge['weight'] = edge['base_weight'] * factor_multiplier
                        edge['status'] = 'jammed'
                    break
        
        # Moramo ažurirati i suprotni smjer ako je dvosmjerna!
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
                    edge.pop('status', None) # Brišemo status