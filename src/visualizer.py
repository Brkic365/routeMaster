"""Main visualizer for RouteMaster traffic simulation.

Coordinates between simulation logic, UI rendering, and user interaction.
"""

import tkinter as tk
import math
from typing import Optional, Tuple, List
from utils import calculate_turn_dir, rotate_point
from algorithms import a_star, generate_instructions
from simulation import TrafficSimulator
from spatial import SpatialGrid
from ui_components import HudRenderer, SidebarManager
from models import Graph
from config import (
    Theme, ViewConfig, AnimationConfig, UIConfig, FileConfig
)


class MapVisualizer:
    """Main controller for the map visualization and user interaction."""

    class ViewManager:
        """Manages coordinate transformations and viewport state."""

        def __init__(
            self,
            graph: Graph,
            canvas_width: int,
            canvas_height: int
        ) -> None:
            """Initialize the view manager.

            Args:
                graph: The road network graph
                canvas_width: Canvas width in pixels
                canvas_height: Canvas height in pixels
            """
            self.graph = graph
            self.canvas_width = canvas_width
            self.canvas_height = canvas_height

            lats = [n.lat for n in graph.nodes.values()]
            lons = [n.lon for n in graph.nodes.values()]

            if not lats or not lons:
                self.min_lat, self.max_lat = 0.0, 1.0
                self.min_lon, self.max_lon = 0.0, 1.0
            else:
                self.min_lat, self.max_lat = min(lats), max(lats)
                self.min_lon, self.max_lon = min(lons), max(lons)

            avg_lat = (self.min_lat + self.max_lat) / 2
            self.aspect_ratio = math.cos(math.radians(avg_lat))

            lat_diff = self.max_lat - self.min_lat
            lon_diff = (self.max_lon - self.min_lon) * self.aspect_ratio
            if lat_diff == 0:
                lat_diff = 1.0
            if lon_diff == 0:
                lon_diff = 1.0

            canvas_avail_width = canvas_width - ViewConfig.SIDEBAR_WIDTH
            self.scale = min(
                (canvas_avail_width - 2 * ViewConfig.CANVAS_PADDING) / lon_diff,
                (canvas_height - 2 * ViewConfig.CANVAS_PADDING) / lat_diff
            )

            self.center_x = canvas_avail_width / 2
            self.center_y = canvas_height / 2
            self.mid_lat = (self.min_lat + self.max_lat) / 2
            self.mid_lon = (self.min_lon + self.max_lon) / 2

            self.zoom = 1.0
            self.offset_x = 0.0
            self.offset_y = 0.0

        def geo_to_screen(self, lat: float, lon: float) -> Tuple[int, int]:
            """Convert geographic coordinates to screen coordinates.

            Args:
                lat: Latitude
                lon: Longitude

            Returns:
                (x, y) screen coordinates
            """
            base_x = (lon - self.mid_lon) * self.aspect_ratio * self.scale
            base_y = -(lat - self.mid_lat) * self.scale

            x = int(self.center_x + (base_x * self.zoom) + self.offset_x)
            y = int(self.center_y + (base_y * self.zoom) + self.offset_y)
            return x, y

        def screen_to_geo(self, x: int, y: int) -> Tuple[float, float]:
            """Convert screen coordinates to geographic coordinates.

            Args:
                x: Screen x coordinate
                y: Screen y coordinate

            Returns:
                (lat, lon) geographic coordinates
            """
            x_rel = (x - self.center_x - self.offset_x) / self.zoom
            y_rel = (y - self.center_y - self.offset_y) / self.zoom

            lon = (x_rel / (self.aspect_ratio * self.scale)) + self.mid_lon
            lat = -(y_rel / self.scale) + self.mid_lat
            return lat, lon

        def get_visible_bounds(self) -> Tuple[float, float, float, float]:
            """Calculate geographic bounds of the visible viewport.

            Returns:
                (min_lat, max_lat, min_lon, max_lon) tuple
            """
            x0, y0 = 0, 0
            x1, y1 = self.canvas_width, self.canvas_height

            lat0, lon0 = self.screen_to_geo(x0, y0)
            lat1, lon1 = self.screen_to_geo(x1, y1)

            min_lat = min(lat0, lat1)
            max_lat = max(lat0, lat1)
            min_lon = min(lon0, lon1)
            max_lon = max(lon0, lon1)

            lat_span = max_lat - min_lat
            lon_span = max_lon - min_lon

            padding_factor = ViewConfig.VIEWPORT_PADDING_FACTOR
            min_lat -= lat_span * padding_factor
            max_lat += lat_span * padding_factor
            min_lon -= lon_span * padding_factor
            max_lon += lon_span * padding_factor

            min_lat = max(self.min_lat, min_lat)
            max_lat = min(self.max_lat, max_lat)
            min_lon = max(self.min_lon, min_lon)
            max_lon = min(self.max_lon, max_lon)

            return min_lat, max_lat, min_lon, max_lon

        def fit_to_bounds(
            self,
            min_lat: float,
            max_lat: float,
            min_lon: float,
            max_lon: float
        ) -> None:
            """Auto-zoom and pan to fit defined geographic bounds.

            Args:
                min_lat: Minimum latitude
                max_lat: Maximum latitude
                min_lon: Minimum longitude
                max_lon: Maximum longitude
            """
            if min_lat >= max_lat or min_lon >= max_lon:
                return

            self.zoom = 1.0
            self.offset_x = 0.0
            self.offset_y = 0.0

            lat_span = max_lat - min_lat
            lon_span = max_lon - min_lon

            canvas_avail_width = self.canvas_width - ViewConfig.SIDEBAR_WIDTH
            target_scale_x = (
                (canvas_avail_width * 0.8) / (lon_span * self.aspect_ratio)
                if lon_span > 0 else self.scale
            )
            target_scale_y = (
                (self.canvas_height * 0.8) / lat_span
                if lat_span > 0 else self.scale
            )

            self.scale = min(target_scale_x, target_scale_y)

            center_lat = (min_lat + max_lat) / 2
            center_lon = (min_lon + max_lon) / 2

            self.offset_x = -((center_lon - self.mid_lon) * self.aspect_ratio * self.scale)
            self.offset_y = -(-(center_lat - self.mid_lat) * self.scale)

        def update_dimensions(self, width: int, height: int) -> None:
            """Update canvas dimensions.

            Args:
                width: New canvas width
                height: New canvas height
            """
            self.canvas_width = width
            self.canvas_height = height
            self.center_x = (width - ViewConfig.SIDEBAR_WIDTH) / 2
            self.center_y = height / 2

    def __init__(
        self,
        graph: Graph,
        width: int = ViewConfig.WINDOW_WIDTH,
        height: int = ViewConfig.WINDOW_HEIGHT
    ) -> None:
        """Initialize the map visualizer.

        Args:
            graph: The road network graph
            width: Window width in pixels
            height: Window height in pixels
        """
        self.graph = graph
        self.simulator = TrafficSimulator(graph)
        self.width = width
        self.height = height

        canvas_width = width - ViewConfig.SIDEBAR_WIDTH
        self.view_manager = self.ViewManager(graph, canvas_width, height)
        self.grid = SpatialGrid(graph)

        self.start_node: Optional[str] = None
        self.end_node: Optional[str] = None
        self.click_state = 0
        self.mode = "NAVIGATE"

        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.is_paused = False

        self.current_route_path: Optional[List[str]] = None
        self.current_route_dist = 0.0
        self.current_instructions: List[str] = []
        self.trajectory_points: List[Tuple[float, float]] = []
        self.anim_index = 0
        self.anim_running = False

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Initialize the Tkinter UI components."""
        self.root = tk.Tk()
        self.root.title(UIConfig.WINDOW_TITLE)

        self.main_frame = tk.Frame(
            self.root,
            bg=Theme.COLORS['background']
        )
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        canvas_width = self.width - ViewConfig.SIDEBAR_WIDTH
        self.canvas = tk.Canvas(
            self.main_frame,
            width=canvas_width,
            height=self.height,
            bg=Theme.COLORS['background'],
            highlightthickness=0
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.hud = HudRenderer(self.canvas, canvas_width, self.height)

        self.sidebar = tk.Frame(
            self.main_frame,
            width=ViewConfig.SIDEBAR_WIDTH,
            bg=Theme.COLORS['sidebar_bg']
        )
        self.sidebar.pack(side=tk.RIGHT, fill=tk.Y)

        self.sidebar_manager = SidebarManager(self.sidebar)
        self._setup_sidebar()

        self._bind_events()

        self.tooltip = tk.Label(
            self.canvas,
            text="",
            bg="#333333",
            fg="#00ffff",
            font=UIConfig.FONTS['tooltip'],
            padx=5,
            pady=2,
            relief=tk.SOLID,
            borderwidth=1
        )
        self.tooltip.place(x=-100, y=-100)

    def _setup_sidebar(self) -> None:
        """Create sidebar widgets."""
        self.sidebar_manager.create_header(UIConfig.SIDEBAR_SECTIONS['controls'])

        self.btn_nav = self.sidebar_manager.create_styled_button(
            UIConfig.BUTTON_LABELS['navigate'],
            Theme.COLORS['nav_mode'],
            lambda: self.set_mode("NAVIGATE")
        )

        self.btn_jam = self.sidebar_manager.create_styled_button(
            UIConfig.BUTTON_LABELS['create_jam'],
            Theme.COLORS['jam_mode'],
            lambda: self.set_mode("JAM")
        )

        self.btn_block = self.sidebar_manager.create_styled_button(
            UIConfig.BUTTON_LABELS['block_road'],
            Theme.COLORS['block_mode'],
            lambda: self.set_mode("BLOCK")
        )

        self.sidebar_manager.create_spacer()

        self.btn_pause = self.sidebar_manager.create_styled_button(
            UIConfig.BUTTON_LABELS['pause'],
            "#777777",
            self.toggle_pause
        )

        self.sidebar_manager.create_styled_button(
            UIConfig.BUTTON_LABELS['complete_restart'],
            "#ff3333",
            self._complete_restart
        )

        self.lbl_info = self.sidebar_manager.create_text_label(
            UIConfig.INFO_PLACEHOLDER
        )
        self.lbl_info.pack(side=tk.BOTTOM, pady=30, padx=15, anchor="w")

        self.sidebar_manager.create_header(
            UIConfig.SIDEBAR_SECTIONS['street_search'],
            pady=10
        )

        self.entry_search = self.sidebar_manager.create_entry()
        self.entry_search.pack(fill=tk.X, padx=15, ipady=5)

        self.sidebar_manager.create_styled_button(
            UIConfig.BUTTON_LABELS['search'],
            "#444444",
            self.search_street
        )

        self.sidebar_manager.create_spacer()

        label = tk.Label(
            self.sidebar,
            text=UIConfig.INSTRUCTIONS_PLACEHOLDER,
            bg=Theme.COLORS['sidebar_bg'],
            fg="#777",
            font=("Segoe UI", 9, "italic")
        )
        label.pack(pady=5)

        self.sidebar_manager.create_styled_button(
            UIConfig.BUTTON_LABELS['export_route'],
            "#444444",
            self.export_route
        )

        self.sidebar_manager.create_spacer()

        self.sidebar_manager.create_header(UIConfig.SIDEBAR_SECTIONS['extras'])

        self.show_pois = tk.BooleanVar(value=False)
        checkbox = self.sidebar_manager.create_checkbox(
            UIConfig.CHECKBOX_LABELS['show_pois'],
            self.show_pois,
            self.draw_map
        )
        checkbox.pack(anchor="w", padx=15, pady=5)

    def _bind_events(self) -> None:
        """Bind event handlers to canvas."""
        self.canvas.bind("<Button-1>", self.handle_click)
        self.canvas.bind("<Button-3>", self.start_pan)
        self.canvas.bind("<B3-Motion>", self.do_pan)
        self.canvas.bind("<MouseWheel>", self.do_zoom)
        self.canvas.bind("<Button-4>", self.do_zoom)
        self.canvas.bind("<Button-5>", self.do_zoom)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Configure>", self.on_resize)

    def set_mode(self, mode: str) -> None:
        """Set the current interaction mode.

        Args:
            mode: Mode name ("NAVIGATE", "JAM", or "BLOCK")
        """
        self.mode = mode
        colors = {
            "NAVIGATE": Theme.COLORS['nav_mode'],
            "JAM": Theme.COLORS['jam_mode'],
            "BLOCK": Theme.COLORS['block_mode']
        }
        description = UIConfig.MODE_DESCRIPTIONS.get(mode, "")
        self.lbl_info.config(
            text=f"MODE: {mode}\n\n{description}",
            fg=colors.get(mode, "white")
        )

    def on_resize(self, event: tk.Event) -> None:
        """Handle window resize event.

        Args:
            event: Tkinter event
        """
        self.width = event.width
        self.height = event.height
        canvas_width = self.width - ViewConfig.SIDEBAR_WIDTH

        self.hud.update_dimensions(canvas_width, self.height)
        self.view_manager.update_dimensions(canvas_width, self.height)
        self.draw_map()

    def start_pan(self, event: tk.Event) -> None:
        """Start panning operation.

        Args:
            event: Mouse event
        """
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y
        self.canvas.bind("<ButtonRelease-3>", self.end_pan)

    def do_pan(self, event: tk.Event) -> None:
        """Perform panning operation.

        Args:
            event: Mouse event
        """
        dx = event.x - self.last_mouse_x
        dy = event.y - self.last_mouse_y
        self.view_manager.offset_x += dx
        self.view_manager.offset_y += dy
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y

        tags_to_move = [
            "map_bg", "map_fg", "route", "marker", "highlight",
            "poi", "pulse_effect"
        ]

        for tag in tags_to_move:
            self.canvas.move(tag, dx, dy)

        if hasattr(self, 'car_id') and self.car_id:
            self.canvas.move(self.car_id, dx, dy)

    def end_pan(self, event: tk.Event) -> None:
        """End panning operation.

        Args:
            event: Mouse event
        """
        self.canvas.unbind("<ButtonRelease-3>")
        self.draw_map()

    def do_zoom(self, event: tk.Event) -> None:
        """Handle zoom operation.

        Args:
            event: Mouse wheel event
        """
        factor = ViewConfig.ZOOM_FACTOR
        if event.num == 5 or (hasattr(event, 'delta') and event.delta < 0):
            self.view_manager.zoom /= factor
        else:
            self.view_manager.zoom *= factor

        self.view_manager.zoom = max(
            ViewConfig.MIN_ZOOM,
            min(ViewConfig.MAX_ZOOM, self.view_manager.zoom)
        )
        self.draw_map()

    def draw_map(self) -> None:
        """Render the map, roads, and active overlays."""
        tags_to_clear = [
            "map_bg", "map_fg", "route", "marker", "highlight", "poi",
            "dashboard", "legend", "hud_speed", "hud_instr", "pulse_effect"
        ]
        for tag in tags_to_clear:
            self.canvas.delete(tag)

        min_lat, max_lat, min_lon, max_lon = self.view_manager.get_visible_bounds()
        visible_edges = self.grid.query_bbox(min_lat, max_lat, min_lon, max_lon)

        all_edges = []
        seen = set()

        for u_id, v_id in visible_edges:
            if u_id not in self.graph.nodes:
                continue

            edges = self.graph.edges.get(u_id, [])
            u = self.graph.nodes[u_id]
            ux, uy = self.view_manager.geo_to_screen(u.lat, u.lon)

            for edge in edges:
                if edge.to != v_id:
                    continue

                if v_id not in self.graph.nodes:
                    continue

                pair = tuple(sorted((u_id, v_id)))
                if pair in seen:
                    continue
                seen.add(pair)

                v = self.graph.nodes[v_id]
                vx, vy = self.view_manager.geo_to_screen(v.lat, v.lon)

                if edge.status == 'blocked':
                    style = Theme.ROAD_STYLES['blocked']
                elif edge.status == 'jammed':
                    style = Theme.ROAD_STYLES['jammed']
                else:
                    style = Theme.ROAD_STYLES.get(edge.type, Theme.ROAD_STYLES['unknown'])

                is_oneway = True
                if v_id in self.graph.edges:
                    for e_back in self.graph.edges[v_id]:
                        if e_back.to == u_id:
                            is_oneway = False
                            break

                all_edges.append((
                    style['width'], style['color'], ux, uy, vx, vy, is_oneway
                ))

        all_edges.sort(key=lambda x: x[0])

        outline_color = Theme.COLORS['road_outline']
        for w, c, ux, uy, vx, vy, is_oneway in all_edges:
            self.canvas.create_line(
                ux, uy, vx, vy,
                fill=outline_color,
                width=w + 2,
                capstyle=tk.ROUND,
                tags="map_bg"
            )

        for w, c, ux, uy, vx, vy, is_oneway in all_edges:
            self.canvas.create_line(
                ux, uy, vx, vy,
                fill=c,
                width=w,
                capstyle=tk.ROUND,
                tags="map_fg"
            )
            if is_oneway and w > 2:
                mx, my = (ux + vx) / 2, (uy + vy) / 2
                self.canvas.create_oval(
                    mx - 1, my - 1, mx + 1, my + 1,
                    fill="#000",
                    tags="map_fg"
                )

        if self.show_pois.get():
            self._draw_pois()

        if not self.anim_running:
            self.hud.draw_speedometer(0, 50)

        if hasattr(self, 'current_instruction_text'):
            self.hud.draw_navigation(self.current_instruction_text)

        self.hud.draw_legend()

        if self.start_node and self.end_node and self.click_state == 2:
            self._draw_route_markers()
            if self.current_route_path:
                self._draw_route_line()
                time_sec = self.simulator.calculate_route_time(self.current_route_path)
                dist = self.simulator.calculate_route_distance(self.current_route_path)

                if math.isinf(time_sec) or math.isnan(time_sec) or math.isinf(dist):
                    self._draw_route_blocked()
                else:
                    self._draw_dashboard(dist, int(time_sec // 60), int(time_sec % 60))
            else:
                self._draw_route_blocked()

        self.canvas.tag_raise("legend")
        self.canvas.tag_raise("hud_speed")
        self.canvas.tag_raise("hud_instr")
        self.canvas.tag_raise("dashboard")
        if hasattr(self, 'car_id'):
            self.canvas.tag_raise("car")

        if self.trajectory_points and self.anim_index >= 0:
            self._redraw_car()

    def _draw_route_markers(self) -> None:
        """Draw start and end route markers."""
        if not self.start_node or not self.end_node:
            return

        start_node = self.graph.nodes[self.start_node]
        end_node = self.graph.nodes[self.end_node]

        sx, sy = self.view_manager.geo_to_screen(start_node.lat, start_node.lon)
        ex, ey = self.view_manager.geo_to_screen(end_node.lat, end_node.lon)

        self.canvas.create_oval(
            sx - 6, sy - 6, sx + 6, sy + 6,
            fill=Theme.COLORS['start_marker'],
            outline=Theme.COLORS['marker_outline'],
            width=2,
            tags="marker"
        )
        self.canvas.create_oval(
            ex - 6, ey - 6, ex + 6, ey + 6,
            fill=Theme.COLORS['end_marker'],
            outline=Theme.COLORS['marker_outline'],
            width=2,
            tags="marker"
        )

    def _draw_route_line(self) -> None:
        """Draw the route path line."""
        if not self.current_route_path:
            return

        coords = []
        for node_id in self.current_route_path:
            node = self.graph.nodes[node_id]
            x, y = self.view_manager.geo_to_screen(node.lat, node.lon)
            coords.extend([x, y])

        self.canvas.create_line(
            coords,
            fill=Theme.COLORS['route_line'],
            width=8,
            stipple="gray50",
            tags="route"
        )
        self.canvas.create_line(
            coords,
            fill=Theme.COLORS['route_line'],
            width=4,
            tags="route"
        )

    def _draw_route_blocked(self) -> None:
        """Draw route blocked message."""
        self.canvas.create_text(
            135, 65,
            text=UIConfig.ROUTE_BLOCKED_MESSAGE,
            fill="red",
            font=UIConfig.FONTS['route_blocked'],
            tags="dashboard"
        )
        self.canvas.create_rectangle(
            20, 20, 250, 110,
            outline="red",
            width=3,
            tags="dashboard"
        )

    def _draw_dashboard(self, distance: float, minutes: int, seconds: int) -> None:
        """Draw route statistics dashboard.

        Args:
            distance: Distance in meters
            minutes: Time minutes
            seconds: Time seconds
        """
        self.canvas.create_rectangle(
            20, 20, 250, 110,
            fill="#222222",
            outline="#444444",
            width=2,
            tags="dashboard"
        )
        self.canvas.create_text(
            35, 35,
            text=UIConfig.HUD_LABELS['route_stats'],
            fill="#888888",
            font=UIConfig.FONTS['dashboard_title'],
            anchor="w",
            tags="dashboard"
        )

        dist_str = (
            f"{distance / 1000:.2f} km" if distance > 1000
            else f"{int(distance)} m"
        )
        self.canvas.create_text(
            35, 60,
            text=f"{UIConfig.HUD_LABELS['distance']}    {dist_str}",
            fill="white",
            font=UIConfig.FONTS['dashboard_text'],
            anchor="w",
            tags="dashboard"
        )

        time_str = f"{minutes} min {seconds} s"
        self.canvas.create_text(
            35, 85,
            text=f"{UIConfig.HUD_LABELS['time']}        {time_str}",
            fill=Theme.COLORS['route_line'],
            font=UIConfig.FONTS['dashboard_time'],
            anchor="w",
            tags="dashboard"
        )

    def _draw_pois(self) -> None:
        """Draw Points of Interest on the canvas."""
        poi_colors = {
            'school': Theme.COLORS['poi_school'],
            'shop': Theme.COLORS['poi_shop'],
            'park': Theme.COLORS['poi_park'],
            'bench': Theme.COLORS['poi_bench']
        }

        count = 0
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width <= 1:
            canvas_width = self.width
        if canvas_height <= 1:
            canvas_height = self.height
            
        for poi in self.graph.pois:
            px, py = self.view_manager.geo_to_screen(poi.lat, poi.lon)

            if px < 0 or px > canvas_width or py < 0 or py > canvas_height:
                continue

            color = poi_colors.get(poi.type, Theme.COLORS['poi_default'])
            radius = 3
            self.canvas.create_oval(
                px - radius, py - radius, px + radius, py + radius,
                fill=color,
                outline="black",
                tags="poi"
            )

            count += 1
            if count > ViewConfig.POI_DISPLAY_LIMIT:
                break

    def _redraw_car(self) -> None:
        """Redraw car at current animation position."""
        if not self.trajectory_points:
            return

        safe_idx = min(self.anim_index, len(self.trajectory_points) - 1)
        if safe_idx < 0:
            return

        lat, lon = self.trajectory_points[safe_idx]
        cx, cy = self.view_manager.geo_to_screen(lat, lon)

        angle = 0.0
        if safe_idx > 0:
            plat, plon = self.trajectory_points[safe_idx - 1]
            px, py = self.view_manager.geo_to_screen(plat, plon)
            angle = math.atan2(cy - py, cx - px)
        elif len(self.trajectory_points) > 1:
            nlat, nlon = self.trajectory_points[safe_idx + 1]
            nx, ny = self.view_manager.geo_to_screen(nlat, nlon)
            angle = math.atan2(ny - cy, nx - cx)

        self.canvas.delete("car")
        self.car_id = self.canvas.create_polygon(
            0, 0, 0, 0, 0, 0,
            fill=Theme.COLORS['car_fill'],
            outline=Theme.COLORS['car_outline'],
            width=1,
            tags="car"
        )

        rotated_pts = []
        for px, py in AnimationConfig.CAR_SHAPE_POINTS:
            rx, ry = rotate_point(px, py, 0, 0, angle)
            rotated_pts.extend([cx + rx, cy + ry])

        self.canvas.coords(self.car_id, *rotated_pts)
        self.canvas.tag_raise("car")

    def recalculate_route(self) -> None:
        """Recalculate route with current traffic conditions."""
        if not self.start_node or not self.end_node:
            return

        path, dist = a_star(self.graph, self.start_node, self.end_node)

        if path:
            self.current_route_path = path
            self.current_route_dist = dist
            self.current_instructions = generate_instructions(self.graph, path)
            self.draw_map()
            
            if not self.anim_running:
                self.start_animation()
        else:
            self.current_route_path = None
            self.current_instructions = [UIConfig.NO_ROUTE_FOUND]
            self.draw_map()
            self.hud.draw_navigation("NO ROUTE (BLOCKED)")

    def export_route(self) -> None:
        """Export current route to text file."""
        if not self.current_instructions:
            print(UIConfig.NO_ROUTE_MESSAGE)
            return

        with open(FileConfig.EXPORT_FILENAME, "w", encoding="utf-8") as f:
            f.write(FileConfig.EXPORT_HEADER)
            for line in self.current_instructions:
                f.write(line + "\n")

        print(f"Route saved to {FileConfig.EXPORT_FILENAME}")
        self.lbl_info.config(
            text=f"Saved to:\n{FileConfig.EXPORT_FILENAME}",
            fg="#00ff00"
        )

    def toggle_pause(self) -> None:
        """Toggle animation pause state."""
        self.is_paused = not self.is_paused
        text = (
            UIConfig.BUTTON_LABELS['resume'] if self.is_paused
            else UIConfig.BUTTON_LABELS['pause']
        )
        bg = "#44aa44" if self.is_paused else "#777777"
        self.btn_pause.config(text=text, bg=bg)
        if not self.is_paused and self.anim_running:
            self.animate_step()

    def _complete_restart(self) -> None:
        """Completely restart simulation: reset traffic, clear route, stop animation."""
        self.simulator.reset_all()
        
        self.anim_running = False
        self.is_paused = False
        self.anim_index = 0
        self.trajectory_points = []
        self.current_route_path = None
        self.current_route_dist = 0.0
        self.current_instructions = []
        
        self.start_node = None
        self.end_node = None
        self.click_state = 0
        
        self.canvas.delete("car")
        self.canvas.delete("route")
        self.canvas.delete("marker")
        self.canvas.delete("dashboard")
        self.canvas.delete("hud_speed")
        self.canvas.delete("hud_instr")
        
        self.btn_pause.config(
            text=UIConfig.BUTTON_LABELS['pause'],
            bg="#777777"
        )
        
        self.lbl_info.config(
            text=UIConfig.INFO_PLACEHOLDER,
            fg="#aaaaaa"
        )
        
        self.draw_map()

    def find_nearest_edge(self, ex: int, ey: int) -> Optional[Tuple[str, str]]:
        """Find the nearest road edge to screen coordinates.

        Args:
            ex: Screen x coordinate
            ey: Screen y coordinate

        Returns:
            (u_id, v_id) tuple if found, None otherwise
        """
        lat, lon = self.view_manager.screen_to_geo(ex, ey)
        candidates = self.grid.query(lat, lon)

        best_edge = None
        min_dist = ViewConfig.PIXEL_TOLERANCE_EDGE

        for u_id, v_id in candidates:
            if u_id not in self.graph.nodes or v_id not in self.graph.nodes:
                continue

            edge = None
            for e in self.graph.edges[u_id]:
                if e.to == v_id:
                    edge = e
                    break

            if not edge:
                continue

            u = self.graph.nodes[u_id]
            v = self.graph.nodes[v_id]

            ux, uy = self.view_manager.geo_to_screen(u.lat, u.lon)
            vx, vy = self.view_manager.geo_to_screen(v.lat, v.lon)

            dx, dy = vx - ux, vy - uy
            if dx == 0 and dy == 0:
                continue

            t = ((ex - ux) * dx + (ey - uy) * dy) / (dx * dx + dy * dy)
            t = max(0, min(1, t))

            nearest_x = ux + t * dx
            nearest_y = uy + t * dy

            dist = math.hypot(ex - nearest_x, ey - nearest_y)

            if dist < min_dist:
                min_dist = dist
                best_edge = (u_id, v_id)

        return best_edge

    def find_nearest_node(self, ex: int, ey: int) -> Optional[str]:
        """Find the nearest node to screen coordinates.

        Args:
            ex: Screen x coordinate
            ey: Screen y coordinate

        Returns:
            Node ID if found, None otherwise
        """
        best_node = None
        min_dist = ViewConfig.PIXEL_TOLERANCE_NODE

        for node in self.graph.nodes.values():
            nx, ny = self.view_manager.geo_to_screen(node.lat, node.lon)
            dist = math.hypot(ex - nx, ey - ny)

            if dist < min_dist:
                min_dist = dist
                best_node = node.id

        return best_node

    def handle_click(self, event: tk.Event) -> None:
        """Handle mouse click events.

        Args:
            event: Mouse event
        """
        if self.mode == "NAVIGATE":
            node = self.find_nearest_node(event.x, event.y)
            if not node:
                return

            nx, ny = self.view_manager.geo_to_screen(
                self.graph.nodes[node].lat,
                self.graph.nodes[node].lon
            )

            if self.click_state == 0:
                self.start_node = node
                self.canvas.delete("marker")
                self.canvas.delete("route")
                self.canvas.delete("dashboard")
                self.canvas.create_oval(
                    nx - 6, ny - 6, nx + 6, ny + 6,
                    fill=Theme.COLORS['start_marker'],
                    outline=Theme.COLORS['marker_outline'],
                    width=2,
                    tags="marker"
                )
                self.click_state = 1
                self._animate_click(event.x, event.y)
            elif self.click_state == 1:
                self.end_node = node
                self.click_state = 2
                self.recalculate_route()
                self._animate_click(event.x, event.y)
            elif self.click_state == 2:
                self.start_node = node
                self.end_node = None
                self.canvas.delete("marker")
                self.canvas.delete("route")
                self.canvas.delete("dashboard")
                self.canvas.create_oval(
                    nx - 6, ny - 6, nx + 6, ny + 6,
                    fill=Theme.COLORS['start_marker'],
                    outline=Theme.COLORS['marker_outline'],
                    width=2,
                    tags="marker"
                )
                self.click_state = 1
                self._animate_click(event.x, event.y)

        elif self.mode in ["JAM", "BLOCK"]:
            edge = self.find_nearest_edge(event.x, event.y)
            if edge:
                u, v = edge
                if self.mode == "JAM":
                    self.simulator.apply_jam(u, v)
                    print(f"Traffic jammed at: {u}-{v}")
                elif self.mode == "BLOCK":
                    self.simulator.block_road(u, v)
                    print(f"Road blocked: {u}-{v}")

                if self.start_node and self.end_node and self.click_state == 2:
                    if self.anim_running and self.current_route_path:
                        self._reroute_live()
                        self.draw_map()
                        self.canvas.tag_raise("car")
                    else:
                        self.recalculate_route()
                else:
                    self.draw_map()

    def _animate_click(self, x: int, y: int, radius: int = 5) -> None:
        """Create a pulse animation at click location.

        Args:
            x: Screen x coordinate
            y: Screen y coordinate
            radius: Current pulse radius
        """
        if radius > AnimationConfig.PULSE_MAX_RADIUS:
            return

        tag = f"pulse_{id(x)}_{radius}"
        self.canvas.create_oval(
            x - radius, y - radius, x + radius, y + radius,
            outline=Theme.COLORS['highlight'],
            width=2,
            tags=(tag, "pulse_effect")
        )

        def next_frame() -> None:
            self.canvas.delete(tag)
            self._animate_click(x, y, radius + AnimationConfig.PULSE_RADIUS_INCREMENT)

        self.root.after(AnimationConfig.PULSE_ANIMATION_DELAY_MS, next_frame)

    def search_street(self) -> None:
        """Search for a street by name and center the map on it."""
        query = self.entry_search.get().lower().strip()
        if not query:
            return

        nodes = self.graph.street_index.get(query)

        if nodes:
            target_node_id = nodes[0]
            if target_node_id in self.graph.nodes:
                target_node = self.graph.nodes[target_node_id]

                self.view_manager.offset_x = (
                    -target_node.lon * self.view_manager.scale + self.width / 2
                )
                self.view_manager.offset_y = (
                    target_node.lat * self.view_manager.scale + self.height / 2
                )

                self.draw_map()
                self.lbl_info.config(
                    text=f"Found: {query.title()}",
                    fg="#00ff00"
                )

                cx, cy = self.view_manager.geo_to_screen(
                    target_node.lat,
                    target_node.lon
                )
                self.canvas.create_oval(
                    cx - 15, cy - 15, cx + 15, cy + 15,
                    outline="yellow",
                    width=4,
                    tags="highlight"
                )
            else:
                self.lbl_info.config(text="Data Error", fg="red")
        else:
            self.lbl_info.config(text=f"Not found:\n{query}", fg="red")

    def on_mouse_move(self, event: tk.Event) -> None:
        """Handle mouse movement for tooltips.

        Args:
            event: Mouse event
        """
        if self.show_pois.get():
            for poi in self.graph.pois:
                px, py = self.view_manager.geo_to_screen(poi.lat, poi.lon)
                if abs(event.x - px) < ViewConfig.POI_HOVER_RADIUS and \
                   abs(event.y - py) < ViewConfig.POI_HOVER_RADIUS:
                    self.tooltip.config(
                        text=f"{poi.name} ({poi.type})",
                        fg="#55ff55"
                    )
                    self.tooltip.place(x=event.x + 15, y=event.y + 15)
                    return

        edge = self.find_nearest_edge(event.x, event.y)
        if edge:
            u_id, v_id = edge
            name = "Unknown Road"
            if u_id in self.graph.edges:
                for e in self.graph.edges[u_id]:
                    if e.to == v_id:
                        name = e.name
                        break

            self.tooltip.config(text=name)
            self.tooltip.place(x=event.x + 15, y=event.y + 15)
        else:
            self.tooltip.place(x=-100, y=-100)

    def start_animation(self) -> None:
        """Initialize and start car animation along current route."""
        if not self.current_route_path:
            return

        self.trajectory_points = self.simulator.interpolate_route_path(
            self.current_route_path
        )

        self.anim_index = 0
        self.canvas.delete("car")
        self.car_id = self.canvas.create_polygon(
            0, 0, 0, 0, 0, 0,
            fill=Theme.COLORS['car_fill'],
            outline=Theme.COLORS['car_outline'],
            width=1,
            tags="car"
        )

        self.animate_step()

    def animate_step(self) -> None:
        """Handle a single frame of car animation."""
        if self.is_paused:
            return

        if self.anim_index < len(self.trajectory_points):
            self.anim_running = True

            current_pos = self.simulator.calculate_car_position(
                self.trajectory_points,
                self.anim_index
            )

            if not current_pos:
                return

            lat, lon = current_pos
            x, y = self.view_manager.geo_to_screen(lat, lon)

            next_pos = self.simulator.calculate_car_position(
                self.trajectory_points,
                self.anim_index + 1
            )
            previous_pos = self.simulator.calculate_car_position(
                self.trajectory_points,
                self.anim_index - 1
            )

            angle = self.simulator.calculate_car_rotation(
                current_pos,
                next_pos,
                previous_pos
            )

            self.canvas.delete("car")
            self.car_id = self.canvas.create_polygon(
                0, 0, 0, 0, 0, 0,
                fill=Theme.COLORS['car_fill'],
                outline=Theme.COLORS['car_outline'],
                width=1,
                tags="car"
            )

            rotated_pts = []
            for px, py in AnimationConfig.CAR_SHAPE_POINTS:
                rx, ry = rotate_point(px, py, 0, 0, angle)
                rotated_pts.extend([x + rx, y + ry])

            self.canvas.coords(self.car_id, *rotated_pts)
            self.canvas.tag_raise(self.car_id)

            if self.current_route_path and len(self.current_route_path) > 1:
                total_steps = len(self.trajectory_points)
                segment_idx = int(
                    (self.anim_index / total_steps) * (len(self.current_route_path) - 1)
                )
                segment_idx = min(segment_idx, len(self.current_route_path) - 2)

                u, v = (
                    self.current_route_path[segment_idx],
                    self.current_route_path[segment_idx + 1]
                )

                current_speed = self.simulator.calculate_current_speed(u, v)
                speed_limit = self.simulator.get_speed_limit(u, v)

                self.canvas.delete("hud_speed")
                self.hud.draw_speedometer(current_speed, speed_limit)

                hud_text = self._update_navigation_hud(
                    segment_idx,
                    self.current_route_path
                )
                self.canvas.delete("hud_instr")
                self.hud.draw_navigation(hud_text)

            self.anim_index += 1
            self.root.after(AnimationConfig.ANIMATION_DELAY_MS, self.animate_step)
        else:
            self.anim_running = False
            self.canvas.delete("hud_speed")
            self.canvas.delete("hud_instr")

    def _update_navigation_hud(
        self,
        segment_idx: int,
        path_nodes: List[str]
    ) -> str:
        """Calculate navigation instruction text for HUD.

        Args:
            segment_idx: Current segment index
            path_nodes: List of node IDs in route

        Returns:
            Instruction text string
        """
        if segment_idx >= len(path_nodes) - 1:
            return "Navigating..."

        u, v = path_nodes[segment_idx], path_nodes[segment_idx + 1]
        edge = None
        for e in self.graph.edges[u]:
            if e.to == v:
                edge = e
                break

        if not edge or math.isinf(edge.weight):
            return "Route blocked ahead."

        current_road_name = edge.name
        steps = AnimationConfig.STEPS_PER_SEGMENT
        local_step = self.anim_index % steps
        t = local_step / steps
        current_seg_dist_remaining = edge.weight * (1.0 - t)

        next_turn_dist = current_seg_dist_remaining
        turn_direction = "straight"
        next_street_name = "Destination"
        found_turn = False

        for i in range(segment_idx + 1, len(path_nodes) - 1):
            u2, v2 = path_nodes[i], path_nodes[i + 1]

            seg_edge = None
            for e in self.graph.edges[u2]:
                if e.to == v2:
                    seg_edge = e
                    break

            if not seg_edge or math.isinf(seg_edge.weight):
                return "Route blocked ahead."

            seg_name = seg_edge.name
            seg_len = seg_edge.weight

            if seg_name != current_road_name and seg_name not in ["Unknown Road", "Unknown"]:
                next_street_name = seg_name
                found_turn = True
                if i > 0:
                    p_prev = self.graph.nodes[path_nodes[i - 1]]
                    p_curr = self.graph.nodes[u2]
                    p_next = self.graph.nodes[v2]
                    turn_direction = calculate_turn_dir(
                        p_prev.lat, p_prev.lon,
                        p_curr.lat, p_curr.lon,
                        p_next.lat, p_next.lon
                    )
                break
            else:
                next_turn_dist += seg_len

        if math.isinf(next_turn_dist) or math.isnan(next_turn_dist):
            return "Recalculating..."

        if found_turn:
            if turn_direction == "straight":
                return f"In {int(next_turn_dist)}m: Continue straight onto {next_street_name}"
            else:
                return f"In {int(next_turn_dist)}m: Turn {turn_direction} onto {next_street_name}"
        else:
            return f"Go {int(next_turn_dist)}m to destination"

    def _reroute_live(self) -> None:
        """Dynamically recalculate route from car's current position."""
        print("Recalculating live route...")

        if not self.current_route_path:
            return

        path_nodes = self.current_route_path
        total_steps = len(self.trajectory_points)
        if total_steps == 0 or self.anim_index >= total_steps:
            return

        current_seg_idx = self.anim_index // AnimationConfig.STEPS_PER_SEGMENT
        current_seg_idx = min(current_seg_idx, len(path_nodes) - 2)

        next_node_id = path_nodes[current_seg_idx + 1]

        new_tail_path, new_dist = a_star(self.graph, next_node_id, self.end_node)

        if not new_tail_path:
            print("Rerouting failed: Path blocked.")
            self.anim_running = False
            self.trajectory_points = self.trajectory_points[:self.anim_index]
            self.hud.draw_navigation("ROUTE BLOCKED! NO PASSAGE.")
            self.draw_map()
            return

        final_path = path_nodes[:current_seg_idx + 1] + new_tail_path
        self.current_route_path = final_path

        points_to_keep_count = (current_seg_idx + 1) * AnimationConfig.STEPS_PER_SEGMENT
        if points_to_keep_count > len(self.trajectory_points):
            points_to_keep_count = len(self.trajectory_points)

        kept_anim_path = self.trajectory_points[:points_to_keep_count]

        new_visual_points = self.simulator.interpolate_route_path(new_tail_path)
        self.trajectory_points = kept_anim_path + new_visual_points

        self.current_instructions = generate_instructions(self.graph, final_path)
        self.draw_map()


    def show(self) -> None:
        """Start the Tkinter event loop."""
        self.root.mainloop()
