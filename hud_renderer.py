from config import Theme

class HudRenderer:
    """
    Handles drawing of Head-Up Display (HUD) elements on the visualizer canvas.
    Separates UI rendering logic from the main application logic.
    """
    def __init__(self, canvas, width: int, height: int):
        self.canvas = canvas
        self.width = width
        self.height = height

    def update_dimensions(self, width: int, height: int):
        self.width = width
        self.height = height

    def draw_legend(self):
        """ Draws the map legend in the bottom-right corner. """
        w, h = 180, 160
        
        # Position Legend: Right side, minus margin
        x = self.width - w - 20  
        y = self.height - h - 20
        
        # Background
        self.canvas.create_rectangle(
            x, y, x+w, y+h, 
            fill=Theme.COLORS['hud_bg'], outline="#444", width=2, stipple="gray50", tags="legend"
        )
        self.canvas.create_text(
            x+10, y+15, text="LEGEND", 
            fill="white", font=("Arial", 10, "bold"), anchor="w", tags="legend"
        )
        
        items = [
            ("Road", Theme.ROAD_STYLES['motorway']['color']),
            ("Route", Theme.COLORS['route_line']), 
            ("Traffic Jam", Theme.ROAD_STYLES['jammed']['color']), 
            ("One-way", "#aaaaaa"), 
            ("School/POI", "#55ff55"),
            ("Shop", "#ff55ff")
        ]
        
        for i, (label, color) in enumerate(items):
            iy = y + 40 + i*18
            self.canvas.create_oval(
                x+10, iy, x+20, iy+10, 
                fill=color, outline=color, tags="legend"
            )
            self.canvas.create_text(
                x+30, iy+5, text=label, 
                fill=Theme.COLORS['legend_text'], font=("Arial", 9), anchor="w", tags="legend"
            )

    def draw_speedometer(self, speed: float, limit: int):
        """ Draws the speedometer and speed limit in the bottom-left corner. """
        # Box dimensions
        box_w, box_h = 160, 75
        
        # Position
        x = 20
        y = self.height - box_h - 20
        
        # Background
        self.canvas.create_rectangle(
            x, y, x + box_w, y + box_h, 
            fill=Theme.COLORS['hud_bg'], outline="#444", width=2, stipple="gray50", tags="hud_speed"
        )
        
        # Label "SPEED" (Top Left)
        self.canvas.create_text(
            x+15, y+20, text="SPEED", 
            fill=Theme.COLORS['hud_text'], font=("Arial", 9), anchor="w", tags="hud_speed"
        )
        
        # Current Speed (Bottom Left, Large Font)
        color = "white"
        if speed > limit: 
            color = "#ff3333" # Red if speeding
        
        self.canvas.create_text(
            x+15, y+50, text=f"{int(speed)} km/h", 
            fill=color, font=("Consolas", 22, "bold"), anchor="w", tags="hud_speed"
        )
        
        # Speed Limit Sign (Top Right)
        lx, ly = x + box_w - 25, y + 25
        radius = 15
        
        self.canvas.create_oval(
            lx-radius, ly-radius, lx+radius, ly+radius, 
            outline="#ff3333", width=3, tags="hud_speed"
        )
        self.canvas.create_text(
            lx, ly, text=str(limit), 
            fill="white", font=("Arial", 12, "bold"), tags="hud_speed"
        )

    def draw_navigation(self, text: str):
        """ Draws the navigation instruction HUD in the bottom-center. """
        w = 600
        # Center based on current width
        x = (self.width - w) / 2
        y = self.height - 70 
        
        # Safety margin
        if x < 150: x = 150

        # Background
        self.canvas.create_rectangle(
            x, y, x+w, y+50, 
            fill="#000000", outline=Theme.COLORS['route_line'], width=2, stipple="gray50", tags="hud_instr"
        )
        # Text
        self.canvas.create_text(
            x+w/2, y+25, text=text, 
            fill=Theme.COLORS['route_line'], font=("Segoe UI", 14, "bold"), tags="hud_instr"
        )