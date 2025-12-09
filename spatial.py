from models import Graph
import math

class SpatialGrid:
    """
    A Spatial Hash Grid for efficient 2D spatial queries.
    Maps geographic coordinates (lat, lon) to a grid of cells (buckets).
    Allows O(1) average time complexity for finding nearby edges.
    """
    def __init__(self, graph: Graph, rows: int = 50, cols: int = 50):
        self.graph = graph
        self.rows = rows
        self.cols = cols
        self.grid = {}  # (r, c) -> list of (u_id, v_id)
        
        # Determine bounds
        lats = [n.lat for n in graph.nodes.values()]
        lons = [n.lon for n in graph.nodes.values()]
        
        self.min_lat = min(lats)
        self.max_lat = max(lats)
        self.min_lon = min(lons)
        self.max_lon = max(lons)
        
        self.lat_step = (self.max_lat - self.min_lat) / self.rows
        self.lon_step = (self.max_lon - self.min_lon) / self.cols
        
        # Build the grid immediately
        self.build()

    def _get_cell(self, lat, lon):
        r = int((lat - self.min_lat) / self.lat_step)
        c = int((lon - self.min_lon) / self.lon_step)
        
        # Clamp to bounds (handle edge cases like max_lat)
        r = max(0, min(r, self.rows - 1))
        c = max(0, min(c, self.cols - 1))
        return r, c

    def build(self):
        print("Building spatial grid...")
        count = 0
        for u_id in self.graph.edges:
            if u_id not in self.graph.nodes: continue
            u = self.graph.nodes[u_id]
            
            for edge in self.graph.edges[u_id]:
                v_id = edge['to']
                if v_id not in self.graph.nodes: continue
                v = self.graph.nodes[v_id]
                
                # We add the edge to the cells of both endpoints
                # Technically, a long edge could span empty cells, but for city streets
                # endpoint cells are usually sufficient coverage.
                r1, c1 = self._get_cell(u.lat, u.lon)
                r2, c2 = self._get_cell(v.lat, v.lon)
                
                self._add_to_cell(r1, c1, u_id, v_id)
                if (r1, c1) != (r2, c2):
                    self._add_to_cell(r2, c2, u_id, v_id)
                count += 1
        print(f"Spatial grid built with {count} edge references.")

    def _add_to_cell(self, r, c, u, v):
        if (r, c) not in self.grid:
            self.grid[(r, c)] = []
        self.grid[(r, c)].append((u, v))

    def query(self, lat: float, lon: float) -> list:
        """ Returns a list of candidate edges in the cell around specific lat, lon. """
        r, c = self._get_cell(lat, lon)
        candidates = []
        
        # Check current cell and immediate neighbors (3x3 block)
        # because the point might be near a boundary
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    if (nr, nc) in self.grid:
                        candidates.extend(self.grid[(nr, nc)])
        
        return candidates

    def query_bbox(self, min_lat: float, max_lat: float, min_lon: float, max_lon: float) -> set:
        """ Returns a set of unique edge tuples found in the grid cells covered by the bounding box. """
        
        # Determine grid index ranges
        r_min, c_min = self._get_cell(min_lat, min_lon)
        r_max, c_max = self._get_cell(max_lat, max_lon)
        
        # Ensure correct ordering (lat increases with index or not depending on implementation, 
        # but _get_cell handles that logic. We just need min/max indices)
        # Note: _get_cell logic: r = (lat - min_lat) / step. Higher lat = higher r.
        
        r_start = min(r_min, r_max)
        r_end = max(r_min, r_max)
        c_start = min(c_min, c_max)
        c_end = max(c_min, c_max)
        
        unique_edges = set()
        
        # Iterate through the range of cells (inclusive)
        for r in range(r_start, r_end + 1):
            for c in range(c_start, c_end + 1):
                if (r, c) in self.grid:
                    unique_edges.update(self.grid[(r, c)])
                    
        return unique_edges
