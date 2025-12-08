import math

# Calculates distance in meters between two coordinates.
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

def calculate_turn_dir(lat1, lon1, lat2, lon2, lat3, lon3):
    """
    Calculates turn direction (Left/Right) based on three points:
    P1->P2->P3 using cross product.
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
        return "lijevo"
    elif cross_product < -threshold:
        return "desno"
    else:
        return "ravno"