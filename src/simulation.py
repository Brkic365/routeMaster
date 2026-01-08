"""Traffic simulation logic for RouteMaster.

Handles traffic state management (jams, blocks) and car physics calculations.
"""

import math
import random
from typing import List, Tuple, Optional
from models import Graph, Edge
from config import PhysicsConfig, AnimationConfig, Theme


class TrafficSimulator:
    """Manages traffic simulation state and car physics calculations.

    Attributes:
        graph: The road network graph
        affected_edges: Set of edge tuples (u, v) that have been modified
    """

    def __init__(self, graph: Graph) -> None:
        """Initialize the traffic simulator.

        Args:
            graph: The road network graph
        """
        self.graph = graph
        self.affected_edges: set[Tuple[str, str]] = set()

    def apply_jam(self, u: str, v: str, factor: float = PhysicsConfig.JAM_MULTIPLIER) -> None:
        """Slow down traffic on the edge between u and v by a given factor.

        Args:
            u: Source node ID
            v: Destination node ID
            factor: Multiplier for edge weight (default: 5.0)
        """
        self._update_edge(u, v, factor_multiplier=factor, is_blocked=False)
        self.affected_edges.add((u, v))

    def block_road(self, u: str, v: str) -> None:
        """Block the road completely (sets weight to infinity).

        Args:
            u: Source node ID
            v: Destination node ID
        """
        self._update_edge(u, v, is_blocked=True)
        self.affected_edges.add((u, v))

    def reset_all(self) -> None:
        """Reset all modified roads to their original state."""
        print("Resetting traffic...")
        for u, v in self.affected_edges:
            self._reset_edge(u, v)
            self._reset_edge(v, u)
        self.affected_edges.clear()

    def _update_edge(
        self,
        u: str,
        v: str,
        factor_multiplier: float = 1.0,
        is_blocked: bool = False
    ) -> None:
        """Internal helper to update edge weight and status.

        Args:
            u: Source node ID
            v: Destination node ID
            factor_multiplier: Multiplier for edge weight
            is_blocked: Whether to block the edge completely
        """
        if u in self.graph.edges:
            for edge in self.graph.edges[u]:
                if edge.to == v:
                    if is_blocked:
                        edge.weight = float('inf')
                        edge.status = 'blocked'
                    else:
                        edge.weight = edge.base_weight * factor_multiplier
                        edge.status = 'jammed'
                    break

        if v in self.graph.edges:
            for edge in self.graph.edges[v]:
                if edge.to == u:
                    if is_blocked:
                        edge.weight = float('inf')
                        edge.status = 'blocked'
                    else:
                        edge.weight = edge.base_weight * factor_multiplier
                        edge.status = 'jammed'
                    break

    def _reset_edge(self, u: str, v: str) -> None:
        """Reset an edge to its original state.

        Args:
            u: Source node ID
            v: Destination node ID
        """
        if u in self.graph.edges:
            for edge in self.graph.edges[u]:
                if edge.to == v:
                    edge.weight = edge.base_weight
                    edge.status = None
                    break

    def interpolate_route_path(
        self,
        path: List[str],
        steps_per_segment: int = AnimationConfig.STEPS_PER_SEGMENT
    ) -> List[Tuple[float, float]]:
        """Generate interpolated geographic coordinates along a route path.

        Args:
            path: List of node IDs representing the route
            steps_per_segment: Number of interpolation steps per edge

        Returns:
            List of (lat, lon) tuples representing the trajectory
        """
        trajectory_points: List[Tuple[float, float]] = []

        for i in range(len(path) - 1):
            u_node = self.graph.nodes[path[i]]
            v_node = self.graph.nodes[path[i + 1]]

            for step in range(steps_per_segment):
                t = step / steps_per_segment
                lat = u_node.lat + (v_node.lat - u_node.lat) * t
                lon = u_node.lon + (v_node.lon - u_node.lon) * t
                trajectory_points.append((lat, lon))

        return trajectory_points

    def calculate_car_position(
        self,
        trajectory_points: List[Tuple[float, float]],
        index: int
    ) -> Optional[Tuple[float, float]]:
        """Calculate car position from trajectory at a given index.

        Args:
            trajectory_points: List of (lat, lon) coordinates
            index: Current position index in trajectory

        Returns:
            (lat, lon) tuple if valid index, None otherwise
        """
        if not trajectory_points or index < 0 or index >= len(trajectory_points):
            return None
        return trajectory_points[index]

    def calculate_car_rotation(
        self,
        current_pos: Tuple[float, float],
        next_pos: Optional[Tuple[float, float]],
        previous_pos: Optional[Tuple[float, float]]
    ) -> float:
        """Calculate car rotation angle in radians based on movement direction.

        Args:
            current_pos: Current (lat, lon) position
            next_pos: Next (lat, lon) position (if available)
            previous_pos: Previous (lat, lon) position (if available)

        Returns:
            Rotation angle in radians (0 if no direction can be determined)
        """
        if next_pos:
            lat_diff = next_pos[0] - current_pos[0]
            lon_diff = next_pos[1] - current_pos[1]
        elif previous_pos:
            lat_diff = current_pos[0] - previous_pos[0]
            lon_diff = current_pos[1] - previous_pos[1]
        else:
            return 0.0

        return math.atan2(lat_diff, lon_diff)

    def calculate_current_speed(
        self,
        from_node_id: str,
        to_node_id: str
    ) -> float:
        """Calculate current car speed based on road type and traffic status.

        Args:
            from_node_id: Source node ID
            to_node_id: Destination node ID

        Returns:
            Current speed in km/h
        """
        edge = self._find_edge(from_node_id, to_node_id)
        if not edge:
            return 0.0

        if edge.status == 'blocked':
            limit = Theme.SPEED_LIMITS['blocked']
        elif edge.status == 'jammed':
            limit = Theme.SPEED_LIMITS['jammed']
        else:
            limit = Theme.SPEED_LIMITS.get(edge.type, 30)

        variance = PhysicsConfig.SPEED_VARIANCE_MIN + (
            random.random() * (PhysicsConfig.SPEED_VARIANCE_MAX - PhysicsConfig.SPEED_VARIANCE_MIN)
        )
        current_speed = limit * variance
        return max(0.0, current_speed)

    def get_speed_limit(
        self,
        from_node_id: str,
        to_node_id: str
    ) -> int:
        """Get the speed limit for a given edge.

        Args:
            from_node_id: Source node ID
            to_node_id: Destination node ID

        Returns:
            Speed limit in km/h
        """
        edge = self._find_edge(from_node_id, to_node_id)
        if not edge:
            return 30

        if edge.status == 'blocked':
            return Theme.SPEED_LIMITS['blocked']
        elif edge.status == 'jammed':
            return Theme.SPEED_LIMITS['jammed']
        else:
            return Theme.SPEED_LIMITS.get(edge.type, 30)

    def calculate_route_time(self, path: List[str]) -> float:
        """Calculate total travel time for a route in seconds.

        Args:
            path: List of node IDs representing the route

        Returns:
            Total time in seconds (infinity if route is blocked)
        """
        total_seconds = 0.0

        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            edge = self._find_edge(u, v)

            if not edge:
                return float('inf')

            if edge.status == 'blocked' or math.isinf(edge.weight):
                return float('inf')

            if edge.status == 'jammed':
                speed_limit = Theme.SPEED_LIMITS['jammed']
            else:
                speed_limit = Theme.SPEED_LIMITS.get(edge.type, 30)

            speed_ms = max(1, speed_limit) / PhysicsConfig.METERS_PER_SECOND_CONVERSION

            if math.isinf(edge.weight):
                return float('inf')

            total_seconds += edge.weight / speed_ms

        return total_seconds

    def calculate_route_distance(self, path: List[str]) -> float:
        """Calculate total distance for a route in meters.

        Args:
            path: List of node IDs representing the route

        Returns:
            Total distance in meters (infinity if route is blocked)
        """
        total_distance = 0.0

        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            edge = self._find_edge(u, v)

            if not edge:
                return float('inf')

            if math.isinf(edge.weight):
                return float('inf')

            total_distance += edge.weight

        return total_distance

    def _find_edge(self, from_id: str, to_id: str) -> Optional[Edge]:
        """Find an edge between two nodes.

        Args:
            from_id: Source node ID
            to_id: Destination node ID

        Returns:
            Edge object if found, None otherwise
        """
        if from_id in self.graph.edges:
            for edge in self.graph.edges[from_id]:
                if edge.to == to_id:
                    return edge
        return None
