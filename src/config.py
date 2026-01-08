"""Configuration constants for RouteMaster traffic simulation.

All application constants are centralized here to ensure consistency
and easy maintenance.
"""


class Theme:
    """Visual theme constants for road styles, colors, and speed limits."""

    ROAD_STYLES = {
        'motorway': {'width': 5, 'color': '#00ffff'},
        'trunk': {'width': 5, 'color': '#00ffff'},
        'primary': {'width': 4, 'color': '#ff00ff'},
        'secondary': {'width': 3, 'color': '#ffff00'},
        'tertiary': {'width': 2, 'color': '#ffffff'},
        'residential': {'width': 1, 'color': '#555555'},
        'service': {'width': 1, 'color': '#333333'},
        'motorway_link': {'width': 3, 'color': '#00ffff'},
        'primary_link': {'width': 3, 'color': '#ff00ff'},
        'unknown': {'width': 1, 'color': '#333333'},
        'jammed': {'width': 5, 'color': '#ff8800'},
        'blocked': {'width': 5, 'color': '#ff0000'}
    }

    SPEED_LIMITS = {
        'motorway': 130,
        'trunk': 110,
        'primary': 80,
        'secondary': 60,
        'tertiary': 50,
        'residential': 30,
        'motorway_link': 60,
        'primary_link': 50,
        'unknown': 30,
        'jammed': 10,
        'blocked': 0
    }

    COLORS = {
        'background': "#050505",
        'hud_bg': "#111111",
        'hud_text': "#888888",
        'legend_text': "#aaaaaa",
        'route_line': "#00ff00",
        'highlight': "yellow",
        'sidebar_bg': "#2a2a2a",
        'sidebar_text': "white",
        'nav_mode': "#00ccff",
        'jam_mode': "#ff8800",
        'block_mode': "#ff0000",
        'pulse': "#ffffff",
        'road_outline': "#222222",
        'start_marker': "#00ff00",
        'end_marker': "#ff0000",
        'marker_outline': "white",
        'car_fill': "yellow",
        'car_outline': "white",
        'poi_school': '#55ff55',
        'poi_shop': '#ff55ff',
        'poi_park': '#00dd00',
        'poi_bench': '#aaaaaa',
        'poi_default': '#ffffff',
        'speed_normal': "white",
        'speed_over': "#ff3333",
        'speed_limit_outline': "#ff3333"
    }


class ViewConfig:
    """Viewport and rendering configuration constants."""

    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 900
    SIDEBAR_WIDTH = 200
    CANVAS_PADDING = 50
    VIEWPORT_PADDING_FACTOR = 0.2
    MIN_SCALE_DIFF = 1.0

    ZOOM_FACTOR = 1.1
    MIN_ZOOM = 0.1
    MAX_ZOOM = 10.0

    PIXEL_TOLERANCE_EDGE = 20.0
    PIXEL_TOLERANCE_NODE = 30.0
    POI_HOVER_RADIUS = 10
    POI_DISPLAY_LIMIT = 500


class AnimationConfig:
    """Animation and interpolation constants."""

    STEPS_PER_SEGMENT = 10
    ANIMATION_DELAY_MS = 50
    PULSE_ANIMATION_DELAY_MS = 30
    PULSE_MAX_RADIUS = 40
    PULSE_RADIUS_INCREMENT = 4

    CAR_SHAPE_POINTS = [(10, 0), (-6, -6), (-6, 6)]


class UIConfig:
    """User interface text and styling constants."""

    WINDOW_TITLE = "RouteMaster - Traffic Control"

    MODE_DESCRIPTIONS = {
        "NAVIGATE": "Left Click: Set Start/End",
        "JAM": "Left Click on road:\nSlow down traffic (x5)",
        "BLOCK": "Left Click on road:\nBlock road completely"
    }

    BUTTON_LABELS = {
        'navigate': "Navigate",
        'create_jam': "Create Traffic Jam",
        'block_road': "Block Road",
        'reset_traffic': "🔄 Reset Traffic",
        'search': "Search",
        'export_route': "Export Route",
        'animate_movement': "Animate Movement",
        'pause': "⏸️ Pause",
        'resume': "▶️ Resume",
        'complete_restart': "🔄 Complete Restart"
    }

    SIDEBAR_SECTIONS = {
        'controls': "CONTROLS",
        'street_search': "STREET SEARCH",
        'extras': "EXTRAS"
    }

    CHECKBOX_LABELS = {
        'show_pois': "Show POI (School/Shop)"
    }

    INFO_PLACEHOLDER = "Mode: NAVIGATE\nClick map to start."
    INSTRUCTIONS_PLACEHOLDER = "(Instructions on map)"
    NO_ROUTE_MESSAGE = "No route to export."
    ROUTE_BLOCKED_MESSAGE = "ROUTE BLOCKED!"
    NO_ROUTE_FOUND = "Route blocked."
    DESTINATION_REACHED = "You have reached your destination."

    HUD_LABELS = {
        'speed': "SPEED",
        'legend': "LEGEND",
        'route_stats': "ROUTE STATS",
        'distance': "Distance:",
        'time': "Time:"
    }

    LEGEND_ITEMS = [
        ("Road", Theme.ROAD_STYLES['motorway']['color']),
        ("Route", Theme.COLORS['route_line']),
        ("Traffic Jam", Theme.ROAD_STYLES['jammed']['color']),
        ("One-way", "#aaaaaa"),
        ("School/POI", Theme.COLORS['poi_school']),
        ("Shop", Theme.COLORS['poi_shop'])
    ]

    FONTS = {
        'sidebar_header': ("Segoe UI", 14, "bold"),
        'sidebar_button': ("Segoe UI", 10, "bold"),
        'sidebar_text': ("Segoe UI", 9),
        'sidebar_entry': ("Segoe UI", 11),
        'hud_title': ("Arial", 10, "bold"),
        'hud_text': ("Arial", 9),
        'hud_speed': ("Consolas", 22, "bold"),
        'hud_speed_limit': ("Arial", 12, "bold"),
        'hud_navigation': ("Segoe UI", 14, "bold"),
        'dashboard_title': ("Arial", 9, "bold"),
        'dashboard_text': ("Segoe UI", 12),
        'dashboard_time': ("Segoe UI", 12, "bold"),
        'tooltip': ("Arial", 10),
        'route_blocked': ("Arial", 16, "bold")
    }


class FileConfig:
    """File paths and export configuration."""

    DEFAULT_OSM_FILE = "data/mapa_trg.osm"
    EXPORT_FILENAME = "route_directions.txt"
    EXPORT_HEADER = "ROUTE MASTER NAVIGATION\n=======================\n\n"


class PhysicsConfig:
    """Physics and simulation constants."""

    EARTH_RADIUS_METERS = 6371000
    JAM_MULTIPLIER = 5.0
    TURN_PENALTY_METERS = 20.0
    TURN_THRESHOLD = 0.5
    SPEED_VARIANCE_MIN = 0.9
    SPEED_VARIANCE_MAX = 1.1
    METERS_PER_SECOND_CONVERSION = 3.6
