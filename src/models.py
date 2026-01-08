"""Data models for RouteMaster traffic simulation.

Pure data classes representing the graph structure, nodes, edges, and POIs.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List
from collections import defaultdict


@dataclass
class Node:
    """Represents a single geographic point (node) in the OSM graph.

    Attributes:
        id: Unique identifier for the node
        lat: Latitude coordinate
        lon: Longitude coordinate
    """

    id: str
    lat: float
    lon: float

    def __post_init__(self):
        """Ensure coordinates are floats."""
        self.lat = float(self.lat)
        self.lon = float(self.lon)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"Node(id='{self.id}', lat={self.lat:.6f}, lon={self.lon:.6f})"


@dataclass
class Edge:
    """Represents a directed edge between two nodes in the graph.

    Attributes:
        to: Destination node ID
        weight: Current edge weight (may be modified by traffic)
        base_weight: Original edge weight (for resetting)
        type: Road type (e.g., 'motorway', 'primary', 'residential')
        name: Street name
        status: Optional traffic status ('jammed', 'blocked', or None)
    """

    to: str
    weight: float
    base_weight: float
    type: str
    name: str
    status: Optional[str] = None

    def __repr__(self) -> str:
        """String representation for debugging."""
        status_str = f", status='{self.status}'" if self.status else ""
        return (f"Edge(to='{self.to}', weight={self.weight:.2f}, "
                f"type='{self.type}', name='{self.name}'{status_str})")


@dataclass
class POI:
    """Represents a Point of Interest (e.g., School, Shop).

    Attributes:
        lat: Latitude coordinate
        lon: Longitude coordinate
        type: POI type (e.g., 'school', 'shop', 'park')
        name: POI name
    """

    lat: float
    lon: float
    type: str
    name: str

    def __post_init__(self):
        """Ensure coordinates are floats."""
        self.lat = float(self.lat)
        self.lon = float(self.lon)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (f"POI(lat={self.lat:.6f}, lon={self.lon:.6f}, "
                f"type='{self.type}', name='{self.name}')")


class Graph:
    """Graph structure representing the road network.

    Attributes:
        nodes: Dictionary mapping node ID to Node objects
        edges: Dictionary mapping node ID to list of outgoing Edge objects
        pois: List of POI objects
        street_index: Dictionary mapping street name (lowercase) to list of node IDs
    """

    def __init__(self) -> None:
        """Initialize an empty graph."""
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, List[Edge]] = {}
        self.pois: List[POI] = []
        self.street_index: Dict[str, List[str]] = defaultdict(list)

    def add_node(self, node_id: str, lat: float, lon: float) -> None:
        """Add a node to the graph.

        Args:
            node_id: Unique identifier for the node
            lat: Latitude coordinate
            lon: Longitude coordinate
        """
        self.nodes[node_id] = Node(node_id, lat, lon)
        self.edges[node_id] = []

    def add_edge(
        self,
        from_id: str,
        to_id: str,
        weight: float,
        road_type: str = "unknown",
        name: str = "Unknown Road"
    ) -> None:
        """Add a directed edge to the graph.

        For bidirectional roads, this method should be called twice
        (once for each direction).

        Args:
            from_id: Source node ID
            to_id: Destination node ID
            weight: Edge weight (distance in meters)
            road_type: Road type classification
            name: Street name
        """
        if from_id in self.nodes and to_id in self.nodes:
            edge = Edge(
                to=to_id,
                weight=weight,
                base_weight=weight,
                type=road_type,
                name=name
            )
            self.edges[from_id].append(edge)

    def get_neighbors(self, node_id: str) -> List[Edge]:
        """Get all outgoing edges from a node.

        Args:
            node_id: Source node ID

        Returns:
            List of Edge objects representing outgoing edges
        """
        return self.edges.get(node_id, [])

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (f"Graph(nodes={len(self.nodes)}, "
                f"edges={sum(len(edges) for edges in self.edges.values())}, "
                f"pois={len(self.pois)})")
