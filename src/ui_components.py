"""UI components for RouteMaster traffic simulation.

Handles HUD rendering and sidebar widget creation.
"""

import tkinter as tk
from typing import Callable, Optional
from config import Theme, UIConfig, ViewConfig


class HudRenderer:
    """Handles drawing of Head-Up Display (HUD) elements on the canvas.

    Separates UI rendering logic from the main application logic.
    """

    def __init__(self, canvas: tk.Canvas, width: int, height: int) -> None:
        """Initialize the HUD renderer.

        Args:
            canvas: Tkinter canvas to draw on
            width: Canvas width in pixels
            height: Canvas height in pixels
        """
        self.canvas = canvas
        self.width = width
        self.height = height

    def update_dimensions(self, width: int, height: int) -> None:
        """Update canvas dimensions.

        Args:
            width: New canvas width
            height: New canvas height
        """
        self.width = width
        self.height = height

    def draw_legend(self) -> None:
        """Draw the map legend in the bottom-right corner."""
        legend_width = 180
        legend_height = 160

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = self.width
            canvas_height = self.height

        x = canvas_width - legend_width - 20
        y = canvas_height - legend_height - 20

        self.canvas.create_rectangle(
            x, y, x + legend_width, y + legend_height,
            fill=Theme.COLORS['hud_bg'],
            outline="#444",
            width=2,
            stipple="gray50",
            tags="legend"
        )

        self.canvas.create_text(
            x + 10, y + 15,
            text=UIConfig.HUD_LABELS['legend'],
            fill="white",
            font=UIConfig.FONTS['hud_title'],
            anchor="w",
            tags="legend"
        )

        for i, (label, color) in enumerate(UIConfig.LEGEND_ITEMS):
            item_y = y + 40 + i * 18
            self.canvas.create_oval(
                x + 10, item_y, x + 20, item_y + 10,
                fill=color,
                outline=color,
                tags="legend"
            )
            self.canvas.create_text(
                x + 30, item_y + 5,
                text=label,
                fill=Theme.COLORS['legend_text'],
                font=UIConfig.FONTS['hud_text'],
                anchor="w",
                tags="legend"
            )

    def draw_speedometer(self, speed: float, limit: int) -> None:
        """Draw the speedometer and speed limit in the bottom-left corner.

        Args:
            speed: Current speed in km/h
            limit: Speed limit in km/h
        """
        box_width = 160
        box_height = 75

        canvas_height = self.canvas.winfo_height()
        if canvas_height <= 1:
            canvas_height = self.height

        x = 20
        y = canvas_height - box_height - 20

        self.canvas.create_rectangle(
            x, y, x + box_width, y + box_height,
            fill=Theme.COLORS['hud_bg'],
            outline="#444",
            width=2,
            stipple="gray50",
            tags="hud_speed"
        )

        self.canvas.create_text(
            x + 15, y + 20,
            text=UIConfig.HUD_LABELS['speed'],
            fill=Theme.COLORS['hud_text'],
            font=UIConfig.FONTS['hud_text'],
            anchor="w",
            tags="hud_speed"
        )

        color = Theme.COLORS['speed_normal']
        if speed > limit:
            color = Theme.COLORS['speed_over']

        self.canvas.create_text(
            x + 15, y + 50,
            text=f"{int(speed)} km/h",
            fill=color,
            font=UIConfig.FONTS['hud_speed'],
            anchor="w",
            tags="hud_speed"
        )

        limit_x = x + box_width - 25
        limit_y = y + 25
        radius = 15

        self.canvas.create_oval(
            limit_x - radius, limit_y - radius,
            limit_x + radius, limit_y + radius,
            outline=Theme.COLORS['speed_limit_outline'],
            width=3,
            tags="hud_speed"
        )
        self.canvas.create_text(
            limit_x, limit_y,
            text=str(limit),
            fill="white",
            font=UIConfig.FONTS['hud_speed_limit'],
            tags="hud_speed"
        )

    def draw_navigation(self, text: str) -> None:
        """Draw the navigation instruction HUD in the bottom-center.

        Args:
            text: Navigation instruction text
        """
        width = 600
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = self.width
            canvas_height = self.height

        x = (canvas_width - width) / 2
        y = canvas_height - 70

        if x < 150:
            x = 150

        self.canvas.create_rectangle(
            x, y, x + width, y + 50,
            fill="#000000",
            outline=Theme.COLORS['route_line'],
            width=2,
            stipple="gray50",
            tags="hud_instr"
        )

        self.canvas.create_text(
            x + width / 2, y + 25,
            text=text,
            fill=Theme.COLORS['route_line'],
            font=UIConfig.FONTS['hud_navigation'],
            tags="hud_instr"
        )


class SidebarManager:
    """Manages sidebar widget creation and styling."""

    def __init__(self, sidebar_frame: tk.Frame) -> None:
        """Initialize the sidebar manager.

        Args:
            sidebar_frame: Tkinter frame for the sidebar
        """
        self.sidebar = sidebar_frame
        self.widgets: dict[str, tk.Widget] = {}

    def create_styled_button(
        self,
        text: str,
        bg_color: str,
        command: Callable[[], None]
    ) -> tk.Button:
        """Create a styled button with hover effects.

        Args:
            text: Button text
            bg_color: Background color (hex string)
            command: Callback function

        Returns:
            Configured button widget
        """
        fg_color = "white"
        if bg_color in [Theme.COLORS['nav_mode'], "#e39e54"]:
            fg_color = "black"

        btn = tk.Button(
            self.sidebar,
            text=text,
            bg=bg_color,
            fg=fg_color,
            font=UIConfig.FONTS['sidebar_button'],
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
            activebackground=bg_color,
            activeforeground="white",
            command=command
        )
        btn.pack(fill=tk.X, padx=15, pady=6)

        def on_enter(e: tk.Event) -> None:
            btn.config(bg=self._adjust_color_brightness(bg_color, 1.2))

        def on_leave(e: tk.Event) -> None:
            btn.config(bg=bg_color)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

        return btn

    def _adjust_color_brightness(self, hex_color: str, factor: float) -> str:
        """Adjust color brightness by a factor.

        Args:
            hex_color: Hex color string (e.g., "#ff0000")
            factor: Brightness multiplier (>1.0 = brighter)

        Returns:
            Adjusted hex color string
        """
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)

        r = min(255, int(r * factor))
        g = min(255, int(g * factor))
        b = min(255, int(b * factor))

        return f"#{r:02x}{g:02x}{b:02x}"

    def create_header(self, text: str, pady: int = 25) -> tk.Label:
        """Create a section header label.

        Args:
            text: Header text
            pady: Vertical padding

        Returns:
            Configured label widget
        """
        label = tk.Label(
            self.sidebar,
            text=text,
            bg=Theme.COLORS['sidebar_bg'],
            fg="white",
            font=UIConfig.FONTS['sidebar_header'],
            pady=pady
        )
        label.pack()
        return label

    def create_text_label(
        self,
        text: str,
        justify: str = tk.LEFT,
        wraplength: int = 200
    ) -> tk.Label:
        """Create a text label.

        Args:
            text: Label text
            justify: Text justification
            wraplength: Text wrap length in pixels

        Returns:
            Configured label widget
        """
        label = tk.Label(
            self.sidebar,
            text=text,
            bg=Theme.COLORS['sidebar_bg'],
            fg="#aaaaaa",
            justify=justify,
            wraplength=wraplength,
            font=UIConfig.FONTS['sidebar_text']
        )
        return label

    def create_entry(self) -> tk.Entry:
        """Create a styled text entry widget.

        Returns:
            Configured entry widget
        """
        entry = tk.Entry(
            self.sidebar,
            bg="#3a3a3a",
            fg="white",
            insertbackground="white",
            relief="flat",
            font=UIConfig.FONTS['sidebar_entry']
        )
        return entry

    def create_checkbox(
        self,
        text: str,
        variable: tk.BooleanVar,
        command: Optional[Callable[[], None]] = None
    ) -> tk.Checkbutton:
        """Create a styled checkbox.

        Args:
            text: Checkbox label
            variable: BooleanVar to bind to
            command: Optional callback function

        Returns:
            Configured checkbox widget
        """
        checkbox = tk.Checkbutton(
            self.sidebar,
            text=text,
            variable=variable,
            bg=Theme.COLORS['sidebar_bg'],
            fg="#dddddd",
            selectcolor=Theme.COLORS['sidebar_bg'],
            activebackground=Theme.COLORS['sidebar_bg'],
            activeforeground="white",
            font=UIConfig.FONTS['sidebar_text'],
            command=command
        )
        return checkbox

    def create_spacer(self, pady: int = 10) -> tk.Label:
        """Create a vertical spacer.

        Args:
            pady: Vertical padding

        Returns:
            Spacer label widget
        """
        spacer = tk.Label(self.sidebar, bg=Theme.COLORS['sidebar_bg'])
        spacer.pack(pady=pady)
        return spacer

