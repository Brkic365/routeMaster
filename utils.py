import math

# Računa udaljenost u metrima između dvije točke na Zemlji.
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Radijus Zemlje u metrima
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

def calculate_turn_dir(lat1, lon1, lat2, lon2, lat3, lon3):
    """
    Računa smjer skretanja (Lijevo/Desno) na temelju tri točke:
    P1(lat1,lon1) -> P2(lat2,lon2) -> P3(lat3,lon3).
    Koristi se cross product vektora.
    """
    # Vektori P1->P2 (u) i P2->P3 (v)
    # Aproksimacija: pretvaramo lat/lon direktno u vektor (dovoljno za smjer na malim udaljenostima)
    # Pazi na skaliranje longitude (cos(lat)) ali za predznak cross producta to često nije presudno
    # ako je kut oštar. Ipak, napravimo basic projekciju.
    
    avg_lat = math.radians((lat1 + lat2 + lat3) / 3)
    cos_lat = math.cos(avg_lat)
    
    u_x = (lon2 - lon1) * cos_lat
    u_y = lat2 - lat1
    
    v_x = (lon3 - lon2) * cos_lat
    v_y = lat3 - lat2
    
    # 2D Cross Product (k-komponenta): u_x*v_y - u_y*v_x
    cross_product = u_x * v_y - u_y * v_x
    
    # Dot product za kut (da razlikujemo blago skretanje od oštrog, optional)
    # dot = u_x*v_x + u_y*v_y
    
    threshold = 0.000001
    
    if cross_product > threshold:
        return "lijevo"
    elif cross_product < -threshold:
        return "desno"
    else:
        return "ravno"