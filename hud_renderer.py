import tkinter as tk

class HudRenderer:
    """
    Handles drawing of Head-Up Display (HUD) elements on the visualizer canvas.
    separates UI rendering logic from the main application logic.
    """
    def __init__(self, canvas, width, height):
        self.canvas = canvas
        self.width = width
        self.height = height

    def draw_legend(self):
        """ Draws the map legend in the bottom-right corner. """
        w, h = 180, 130
        x = self.width - 200 - w - 20  # Offset from sidebar
        y = self.height - h - 20
        
        # Background
        self.canvas.create_rectangle(
            x, y, x+w, y+h, 
            fill="#111", outline="#444", width=2, tags="legend"
        )
        self.canvas.create_text(
            x+10, y+15, text="LEGENDA", 
            fill="white", font=("Arial", 10, "bold"), anchor="w", tags="legend"
        )
        
        items = [
            ("Ulica", "#00ffff"),
            ("Ruta", "#00ff00"), 
            ("Gužva", "#ff4400"), 
            ("Jednosmjerna", "#aaaaaa"), # Updated label
            ("Škola/POI", "#55ff55"),
            ("Dućan", "#ff55ff")
        ]
        
        for i, (label, color) in enumerate(items):
            iy = y + 40 + i*18
            self.canvas.create_oval(
                x+10, iy, x+20, iy+10, 
                fill=color, outline=color, tags="legend"
            )
            self.canvas.create_text(
                x+30, iy+5, text=label, 
                fill="#aaa", font=("Arial", 9), anchor="w", tags="legend"
            )

    def draw_speedometer(self, speed, limit):
        """ Draws the speedometer and speed limit in the bottom-left corner. """
        x, y = 20, self.height - 80
        
        # Background
        self.canvas.create_rectangle(
            x, y, x+120, y+60, 
            fill="#111", outline="#444", width=2, tags="hud_speed"
        )
        self.canvas.create_text(
            x+10, y+20, text="BRZINA", 
            fill="#888", font=("Arial", 8), anchor="w", tags="hud_speed"
        )
        
        color = "white"
        if speed > limit: 
            color = "#ff3333" # Softer red
        
        self.canvas.create_text(
            x+10, y+45, text=f"{int(speed)} km/h", 
            fill=color, font=("Consolas", 18, "bold"), anchor="w", tags="hud_speed"
        )
        
        # Speed Limit Sign
        lx, ly = x+90, y+30
        self.canvas.create_oval(
            lx-15, ly-15, lx+15, ly+15, 
            outline="#ff3333", width=3, tags="hud_speed"
        )
        self.canvas.create_text(
            lx, ly, text=str(limit), 
            fill="white", font=("Arial", 10, "bold"), tags="hud_speed"
        )

    def draw_navigation(self, text):
        """ Draws the navigation instruction HUD in the bottom-center. """
        w = 600
        x = (self.width - 200) / 2 - w/2
        y = self.height - 70 
        
        # Background
        self.canvas.create_rectangle(
            x, y, x+w, y+50, 
            fill="#000000", outline="#00ff00", width=2, stipple="gray50", tags="hud_instr"
        )
        # Text
        self.canvas.create_text(
            x+w/2, y+25, text=text, 
            fill="#00ff00", font=("Segoe UI", 14, "bold"), tags="hud_instr"
        )
