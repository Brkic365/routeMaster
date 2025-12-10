class Theme:
    # Road visualization styles
    ROAD_STYLES = {
        'motorway':     {'width': 5, 'color': '#00ffff'},  # Cyan
        'trunk':        {'width': 5, 'color': '#00ffff'},
        'primary':      {'width': 4, 'color': '#ff00ff'},  # Magenta
        'secondary':    {'width': 3, 'color': '#ffff00'},  # Yellow
        'tertiary':     {'width': 2, 'color': '#ffffff'},  # White
        'residential':  {'width': 1, 'color': '#555555'},  # Dark Grey
        'service':      {'width': 1, 'color': '#333333'},
        'motorway_link':{'width': 3, 'color': '#00ffff'},
        'primary_link': {'width': 3, 'color': '#ff00ff'},
        'unknown':      {'width': 1, 'color': '#333333'},
        
        # Simulation states
        'jammed':       {'width': 5, 'color': '#ff8800'}, 
        'blocked':      {'width': 5, 'color': '#ff0000'}
    }

    SPEED_LIMITS = {
        'motorway': 130, 'trunk': 110, 'primary': 80,
        'secondary': 60, 'tertiary': 50, 'residential': 30, 
        'motorway_link': 60, 'primary_link': 50, 'unknown': 30,
        'jammed': 10,
        'blocked': 0   # Blocked
    }

    COLORS = {
        'background': "#050505",
        'hud_bg': "#111111",
        'hud_text': "#888888",
        'legend_text': "#aaaaaa",
        'route_line': "#00ff00",
        'highlight': "yellow",
        
        # Sidebar
        'sidebar_bg': "#2a2a2a",
        'sidebar_text': "white",
        
        # Mode Colors
        'nav_mode': "#00ccff",
        'jam_mode': "#ff8800",
        'block_mode': "#ff0000",
        
        # FX
        'pulse': "#ffffff",
        'road_outline': "#222222"
    }
