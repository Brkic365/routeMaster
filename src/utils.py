"""Utility functions for RouteMaster traffic simulation.

Provides geometric and geographic calculation helpers.
"""

import math
from typing import Tuple


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in meters between two geographic coordinates.

    Uses the Haversine formula to compute the great-circle distance
    between two points on Earth.

    Args:
        lat1: Latitude of first point in degrees
        lon1: Longitude of first point in degrees
        lat2: Latitude of second point in degrees
        lon2: Longitude of second point in degrees

    Returns:
        Distance in meters
    """
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

def calculate_turn_dir(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    lat3: float,
    lon3: float
) -> str:
    """Calculate turn direction based on three geographic points.

    Determines whether the path P1->P2->P3 turns left, right, or continues
    straight using cross product calculation.

    Args:
        lat1: Latitude of first point
        lon1: Longitude of first point
        lat2: Latitude of second point (current position)
        lon2: Longitude of second point (current position)
        lat3: Latitude of third point (next position)
        lon3: Longitude of third point (next position)

    Returns:
        'left', 'right', or 'straight'
    """
    # Vectors P1->P2 (u) and P2->P3 (v)
    
    avg_lat = math.radians((lat1 + lat2 + lat3) / 3)
    cos_lat = math.cos(avg_lat)
    
    u_x = (lon2 - lon1) * cos_lat
    u_y = lat2 - lat1
    
    v_x = (lon3 - lon2) * cos_lat
    v_y = lat3 - lat2
    
    # 2D Cross Product (k-component)
    cross_product = u_x * v_y - u_y * v_x
    
    threshold = 0.000001
    
    if cross_product > threshold:
        return "left"
    elif cross_product < -threshold:
        return "right"
    else:
        return "straight"

def rotate_point(
    x: float,
    y: float,
    cx: float,
    cy: float,
    angle_rad: float
) -> Tuple[float, float]:
    """Rotate a point around a center by a given angle.

    Args:
        x: X coordinate of point to rotate
        y: Y coordinate of point to rotate
        cx: X coordinate of rotation center
        cy: Y coordinate of rotation center
        angle_rad: Rotation angle in radians

    Returns:
        Tuple of (rotated_x, rotated_y)
    """
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    
    # Translate to origin
    tx = x - cx
    ty = y - cy
    
    # Rotate
    rx = tx * cos_a - ty * sin_a
    ry = tx * sin_a + ty * cos_a
    
    # Translate back
    return rx + cx, ry + cy