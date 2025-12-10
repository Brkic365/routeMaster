import tkinter as tk
import math
from utils import calculate_turn_dir
from algorithms import a_star, generate_instructions
from simulation import TrafficSimulator
from spatial import SpatialGrid
from hud_renderer import HudRenderer
from utils import calculate_turn_dir, rotate_point

# Road visualization styles
from config import Theme

# Road visualization styles and Speed Limits are now in config.Theme

class MapVisualizer:
    def __init__(self, graph, width=1200, height=900):
        self.graph = graph
        self.simulator = TrafficSimulator(graph)
        
        self.width = width
        self.height = height
        self.bg_color = "#050505"

        # Geo-calculations (Bounds)
        lats = [n.lat for n in graph.nodes.values()]
        lons = [n.lon for n in graph.nodes.values()]
        
        if not lats or not lons:
            # Fallback for empty graph
            self.min_lat, self.max_lat = 0, 1
            self.min_lon, self.max_lon = 0, 1
        else:
            self.min_lat, self.max_lat = min(lats), max(lats)
            self.min_lon, self.max_lon = min(lons), max(lons)
            
        self.padding = 50 
        avg_lat = (self.min_lat + self.max_lat) / 2
        self.aspect_ratio = math.cos(math.radians(avg_lat))
        
        # Initial Scale Logic
        lat_diff = self.max_lat - self.min_lat
        lon_diff = (self.max_lon - self.min_lon) * self.aspect_ratio
        if lat_diff == 0: lat_diff = 1.0
        if lon_diff == 0: lon_diff = 1.0
        
        self.scale = min((self.width - 200 - 2 * self.padding) / lon_diff,
                         (self.height - 2 * self.padding) / lat_diff)
                         
        self.center_x = (self.width - 200) / 2
        self.center_y = self.height / 2
        self.mid_lat = (self.min_lat + self.max_lat) / 2
        self.mid_lon = (self.min_lon + self.max_lon) / 2

        self.grid = SpatialGrid(graph)
        self.start_node = None
        self.end_node = None
        self.click_state = 0 
        self.mode = "NAVIGATE" 
        
        self.zoom = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.last_mouse_x = 0
        self.last_mouse_y = 0

        self.root = tk.Tk()
        self.root.title("RouteMaster - Traffic Control")
        
        self.main_frame = tk.Frame(self.root, bg=self.bg_color)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.main_frame, width=self.width-200, height=self.height, bg=self.bg_color, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.hud = HudRenderer(self.canvas, self.width - 200, self.height)

        self.sidebar = tk.Frame(self.main_frame, width=200, bg="#2a2a2a")
        self.sidebar.pack(side=tk.RIGHT, fill=tk.Y)
        self.setup_sidebar()

        self.canvas.bind("<Button-1>", self.handle_click)
        self.canvas.bind("<Button-3>", self.start_pan)
        self.canvas.bind("<B3-Motion>", self.do_pan)
        self.canvas.bind("<MouseWheel>", self.do_zoom)
        self.canvas.bind("<Button-4>", self.do_zoom)
        self.canvas.bind("<Button-5>", self.do_zoom)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Configure>", self.on_resize)
        
        self.is_paused = False

        # Tooltip
        self.tooltip = tk.Label(self.canvas, text="", bg="#333333", fg="#00ffff", 
                                font=("Arial", 10), padx=5, pady=2, relief=tk.SOLID, borderwidth=1)
        self.tooltip.place(x=-100, y=-100)

    def fit_to_bounds(self, min_lat: float, max_lat: float, min_lon: float, max_lon: float):
        """ Auto-zooms and pans to fit the defined geographic bounds with padding. """
        if min_lat >= max_lat or min_lon >= max_lon: return
        
        # Reset Zoom/Pan state
        self.zoom = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
        # Determine strict bounds in pixels would require current scale
        # Instead, we calculate required scale to fit into width/height
        
        # Geo dimensions
        lat_span = max_lat - min_lat
        lon_span = max_lon - min_lon
        
        # Target scale
        target_scale_x = (self.width * 0.8) / (lon_span * self.aspect_ratio) if lon_span > 0 else self.scale
        target_scale_y = (self.height * 0.8) / lat_span if lat_span > 0 else self.scale
        
        self.scale = min(target_scale_x, target_scale_y)
        
        # Center point
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        
        # Offset calculation
        self.offset_x = -((center_lon - self.mid_lon) * self.aspect_ratio * self.scale)
        self.offset_y = -(-(center_lat - self.mid_lat) * self.scale)
        
        self.draw_map()

    def get_visible_bounds(self) -> tuple[float, float, float, float]:
        """ Calculates the geographic bounds of the currently visible canvas area. """
        # Get screen corners
        x0, y0 = 0, 0
        x1, y1 = self.width, self.height
        
        # Convert to Geo
        lat0, lon0 = self.screen_to_geo(x0, y0)
        lat1, lon1 = self.screen_to_geo(x1, y1)
        
        min_lat = min(lat0, lat1)
        max_lat = max(lat0, lat1)
        min_lon = min(lon0, lon1)
        max_lon = max(lon0, lon1)
        
        # Add padding (20%) to prevent popping
        lat_span = max_lat - min_lat
        lon_span = max_lon - min_lon
        
        min_lat -= lat_span * 0.2
        max_lat += lat_span * 0.2
        min_lon -= lon_span * 0.2
        max_lon += lon_span * 0.2
        
        # Clamp to world bounds (optional, but good practice)
        min_lat = max(self.min_lat, min_lat)
        max_lat = min(self.max_lat, max_lat)
        min_lon = max(self.min_lon, min_lon)
        max_lon = min(self.max_lon, max_lon)
        
        return min_lat, max_lat, min_lon, max_lon

    def create_styled_button(self, parent, text, bg_color, command):
        btn = tk.Button(
            parent, text=text, bg=bg_color, fg="white" if bg_color != "#00ccff" and bg_color != "#e39e54" else "black",
            font=("Segoe UI", 10, "bold"), relief="flat", padx=20, pady=8, cursor="hand2",
            activebackground=bg_color, activeforeground="white", command=command
        )
        btn.pack(fill=tk.X, padx=15, pady=6)
        
        # Hover Effect
        def on_enter(e):
            btn.config(bg=self.adjust_color_brightness(bg_color, 1.2))
        def on_leave(e):
            btn.config(bg=bg_color)
            
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def adjust_color_brightness(self, hex_color, factor):
        # Simple brightness adjuster
        r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
        r = min(255, int(r * factor))
        g = min(255, int(g * factor))
        b = min(255, int(b * factor))
        return f"#{r:02x}{g:02x}{b:02x}"

    def setup_sidebar(self):
        # Header
        tk.Label(self.sidebar, text="CONTROLS", bg="#2a2a2a", fg="white", font=("Segoe UI", 14, "bold"), pady=25).pack()

        # Mode Buttons
        self.btn_nav = self.create_styled_button(self.sidebar, "Navigate", "#00ccff", lambda: self.set_mode("NAVIGATE"))
        self.btn_jam = self.create_styled_button(self.sidebar, "Create Traffic Jam", "#ff8800", lambda: self.set_mode("JAM"))
        self.btn_block = self.create_styled_button(self.sidebar, "Block Road", "#ff3333", lambda: self.set_mode("BLOCK"))

        # Spacer
        tk.Label(self.sidebar, bg="#2a2a2a").pack(pady=10)

        # Reset
        self.btn_reset = self.create_styled_button(self.sidebar, "🔄 Reset Traffic", "#555555", self.reset_traffic)
        
        # Info Panel
        self.lbl_info = tk.Label(self.sidebar, text="Mode: NAVIGATE\nClick map to start.", 
                                 bg="#2a2a2a", fg="#aaaaaa", justify=tk.LEFT, wraplength=200, font=("Segoe UI", 9))
        self.lbl_info.pack(side=tk.BOTTOM, pady=30, padx=15, anchor="w")

        # Search
        tk.Label(self.sidebar, text="STREET SEARCH", bg="#2a2a2a", fg="white", font=("Segoe UI", 10, "bold"), pady=10).pack()
        self.entry_search = tk.Entry(
            self.sidebar, 
            bg="#3a3a3a", fg="white", 
            insertbackground="white", 
            relief="flat", font=("Segoe UI", 11)
        )
        self.entry_search.pack(fill=tk.X, padx=15, ipady=5) # ipady for inner padding
        
        self.create_styled_button(self.sidebar, "Search", "#444444", self.search_street)

        # Spacer
        tk.Label(self.sidebar, bg="#2a2a2a").pack(pady=10)

        # Instructions Placeholder
        tk.Label(self.sidebar, text="(Instructions on map)", bg="#2a2a2a", fg="#777", font=("Segoe UI", 9, "italic")).pack(pady=5)
        
        # Export
        self.create_styled_button(self.sidebar, "Export Route", "#444444", self.export_route)

        # Spacer
        tk.Label(self.sidebar, bg="#2a2a2a").pack(pady=10)
        
        # Extras
        tk.Label(self.sidebar, text="EXTRAS", bg="#2a2a2a", fg="white", font=("Segoe UI", 10, "bold")).pack()
        self.show_pois = tk.BooleanVar(value=False)
        
        # Checkbox Styling
        chk = tk.Checkbutton(self.sidebar, text="Show POI (School/Shop)", variable=self.show_pois, 
                       bg="#2a2a2a", fg="#dddddd", selectcolor="#2a2a2a", activebackground="#2a2a2a", activeforeground="white",
                       font=("Segoe UI", 9), command=self.draw_map)
        chk.pack(anchor="w", padx=15, pady=5)
                       
        self.create_styled_button(self.sidebar, "Animate Movement", "#e39e54", self.start_animation)
        self.btn_pause = self.create_styled_button(self.sidebar, "⏸️ Pause", "#777777", self.toggle_pause)

    def on_resize(self, event):
        self.width = event.width
        self.height = event.height
        
        self.hud.update_dimensions(self.width, self.height)
        
        self.center_x = self.width / 2
        self.center_y = self.height / 2
        
        self.draw_map()

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        text = "Resume" if self.is_paused else "Pause"
        bg = "#44aa44" if self.is_paused else "#777777"
        self.btn_pause.config(text=text, bg=bg)
        if not self.is_paused:
             self.animate_step()

    def set_mode(self, mode):
        self.mode = mode
        colors = {"NAVIGATE": "#00ccff", "JAM": "#ff8800", "BLOCK": "#ff0000"}
        descriptions = {
            "NAVIGATE": "Left Click: Set Start/End",
            "JAM": "Left Click on road:\nSlow down traffic (x5)",
            "BLOCK": "Left Click on road:\nBlock road completely"
        }
        self.lbl_info.config(text=f"MODE: {mode}\n\n{descriptions[mode]}", fg=colors[mode])

    def to_screen(self, lat, lon):
        # Base projection
        base_x = (lon - self.mid_lon) * self.aspect_ratio * self.scale
        base_y = -(lat - self.mid_lat) * self.scale
        
        # Apply Zoom & Pan
        x = self.center_x + (base_x * self.zoom) + self.offset_x
        y = self.center_y + (base_y * self.zoom) + self.offset_y
        return x, y

    def screen_to_geo(self, sx, sy):
        # Reverse Pan
        x = (sx - self.center_x - self.offset_x) / self.zoom
        y = (sy - self.center_y - self.offset_y) / self.zoom
        
        # Reverse Projection
        lon = (x / (self.aspect_ratio * self.scale)) + self.mid_lon
        lat = -(y / self.scale) + self.mid_lat
        return lat, lon

    def start_pan(self, event):
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y
        self.canvas.bind("<ButtonRelease-3>", self.end_pan)

    def do_pan(self, event):
        dx = event.x - self.last_mouse_x
        dy = event.y - self.last_mouse_y
        self.offset_x += dx
        self.offset_y += dy
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y
        
        # Move map elements only. HUD stays in place.
        tags_to_move = ["map_bg", "map_fg", "route", "marker", "highlight", "poi", "pulse_effect"]
        
        for tag in tags_to_move:
            self.canvas.move(tag, dx, dy)
        
        if hasattr(self, 'car_id') and self.car_id:
             self.canvas.move(self.car_id, dx, dy)

    def end_pan(self, event):
        self.canvas.unbind("<ButtonRelease-3>")
        self.draw_map()

    def do_zoom(self, event):
        factor = 1.1
        if event.num == 5 or event.delta < 0:
            self.zoom /= factor
        else:
            self.zoom *= factor
        self.draw_map()

    
    def draw_map(self):
        """ Renders the map, roads, and active overlays. Uses strict layering. """
        # 1. CLEAR: Wipe everything to prevent ghosting
        tags_to_clear = [
            "map_bg", "map_fg", "route", "marker", "highlight", "poi",
            "dashboard", "legend", "hud_speed", "hud_instr", "pulse_effect"
        ]
        for tag in tags_to_clear:
            self.canvas.delete(tag)
        
        # Car is manually managed during animation

        all_edges = []
        seen = set()
        
        # 2. CULLING: Get only visible edges
        min_lat, max_lat, min_lon, max_lon = self.get_visible_bounds()
        visible_edges = self.grid.query_bbox(min_lat, max_lat, min_lon, max_lon)
        
        # 3. DATA GATHERING
        for u_id, v_id in visible_edges:
            if u_id not in self.graph.nodes: continue
            edges = self.graph.edges.get(u_id, [])
            u = self.graph.nodes[u_id]
            ux, uy = self.to_screen(u.lat, u.lon)

            for edge in edges:
                if edge['to'] != v_id: continue
                v_id = edge['to']
                if v_id not in self.graph.nodes: continue
                
                # Deduplicate
                pair = tuple(sorted((u_id, v_id)))
                if pair in seen: continue
                seen.add(pair)
                
                v = self.graph.nodes[v_id]
                vx, vy = self.to_screen(v.lat, v.lon)
                
                status = edge.get('status', None)
                rtype = edge.get('type', 'unknown')
                
                if status == 'blocked': style = Theme.ROAD_STYLES['blocked']
                elif status == 'jammed': style = Theme.ROAD_STYLES['jammed']
                else: style = Theme.ROAD_STYLES.get(rtype, Theme.ROAD_STYLES['unknown'])
                
                is_oneway = True
                if v_id in self.graph.edges:
                    for e_back in self.graph.edges[v_id]:
                        if e_back['to'] == u_id:
                            is_oneway = False
                            break
                
                all_edges.append((style['width'], style['color'], ux, uy, vx, vy, is_oneway))

        # Sort by width (wider roads at bottom)
        all_edges.sort(key=lambda x: x[0])
        
        # 4. DRAWING (Pass 1: Outlines)
        outline_color = Theme.COLORS.get('road_outline', '#333333')
        for w, c, ux, uy, vx, vy, is_oneway in all_edges:
             self.canvas.create_line(ux, uy, vx, vy, fill=outline_color, width=w+2, capstyle=tk.ROUND, tags="map_bg")

        # 4. DRAWING (Pass 2: Fills)
        for w, c, ux, uy, vx, vy, is_oneway in all_edges:
            self.canvas.create_line(ux, uy, vx, vy, fill=c, width=w, capstyle=tk.ROUND, tags="map_fg")
            if is_oneway and w > 2:
                 mx, my = (ux+vx)/2, (uy+vy)/2
                 self.canvas.create_oval(mx-1, my-1, mx+1, my+1, fill="#000", tags="map_fg") 

        # 5. POIs & HUD
        if self.show_pois.get(): self.draw_pois()

        # HUD Speedometer - only draw if not animating (animate_step handles it otherwise)
        if not hasattr(self, 'anim_running') or not self.anim_running:
            self.hud.draw_speedometer(0, 50) 
            
        if hasattr(self, 'current_instruction_text'):
            self.hud.draw_navigation(self.current_instruction_text)
            
        self.hud.draw_legend()

        # 6. ACTIVE ROUTE & DASHBOARD
        if self.start_node and self.end_node and self.click_state == 2:
            sx, sy = self.to_screen(self.graph.nodes[self.start_node].lat, self.graph.nodes[self.start_node].lon)
            ex, ey = self.to_screen(self.graph.nodes[self.end_node].lat, self.graph.nodes[self.end_node].lon)
            self.canvas.create_oval(sx-6, sy-6, sx+6, sy+6, fill="#00ff00", outline="white", width=2, tags="marker")
            self.canvas.create_oval(ex-6, ey-6, ex+6, ey+6, fill="#ff0000", outline="white", width=2, tags="marker")
            
            if hasattr(self, 'current_route_path') and self.current_route_path:
                self.draw_route_line(self.current_route_path)
                
                time_sec = self.calculate_time(self.current_route_path)
                dist = getattr(self, 'current_route_dist', 0)
                
                if math.isinf(time_sec) or math.isnan(time_sec) or math.isinf(dist):
                    self.canvas.create_text(135, 65, text="ROUTE BLOCKED!", fill="red", font=("Arial", 16, "bold"), tags="dashboard")
                    self.canvas.create_rectangle(20, 20, 250, 110, outline="red", width=3, tags="dashboard")
                else:
                    self.draw_dashboard(dist, int(time_sec // 60), int(time_sec % 60))
            else:
                 self.canvas.create_text(135, 65, text="ROUTE BLOCKED!", fill="red", font=("Arial", 16, "bold"), tags="dashboard")

        # 7. LAYERS
        self.canvas.tag_raise("legend")
        self.canvas.tag_raise("hud_speed")
        self.canvas.tag_raise("hud_instr")
        self.canvas.tag_raise("dashboard")
        if hasattr(self, 'car_id'): self.canvas.tag_raise("car")

        # Redraw Car if animation is active or paused
        # Fix: Static Redraw ensures car remains visible during pan/zoom even if paused
        if hasattr(self, 'anim_path') and self.anim_path:
            # 1. Clamp Index
            safe_idx = min(self.anim_index, len(self.anim_path) - 1)
            
            # If list is empty (e.g., just started), skip
            if safe_idx >= 0:
                # 2. Get Lat/Lon
                lat, lon = self.anim_path[safe_idx]
                
                # 3. Project to new screen coords
                cx, cy = self.to_screen(lat, lon)
                
                # 4. Calculate Rotation (Look behind or ahead)
                angle = 0
                if safe_idx > 0:
                    plat, plon = self.anim_path[safe_idx - 1]
                    px, py = self.to_screen(plat, plon)
                    angle = math.atan2(cy - py, cx - px)
                elif len(self.anim_path) > 1:
                    nlat, nlon = self.anim_path[safe_idx + 1]
                    nx, ny = self.to_screen(nlat, nlon)
                    angle = math.atan2(ny - cy, nx - cx)
                
                # 5. Draw Car
                self.canvas.delete("car")
                self.car_id = self.canvas.create_polygon(0,0,0,0,0,0, fill="yellow", outline="white", width=1, tags="car")
                
                pts = [(10, 0), (-6, -6), (-6, 6)]
                rotated_pts = []
                for px, py in pts:
                    rx, ry = rotate_point(px, py, 0, 0, angle)
                    rotated_pts.extend([cx + rx, cy + ry])
                
                self.canvas.coords(self.car_id, *rotated_pts)
                self.canvas.tag_raise("car")



    


    def recalculate_route(self):
        """ Recalculates route with current traffic conditions. """
        path, dist = a_star(self.graph, self.start_node, self.end_node)
        
        if path:
            self.current_route_path = path
            self.current_route_dist = dist
            self.draw_map()
            # Generate instructions only if a path exists
            self.current_instructions = generate_instructions(self.graph, path) 
        else:
            # No path found (blocked)
            self.current_route_path = None
            self.current_instructions = ["Route blocked."]
            self.draw_map()
            # Explicitly write to HUD
            self.hud.draw_navigation("NO ROUTE (BLOCKED)")

    def export_route(self):
        if not hasattr(self, 'current_instructions') or not self.current_instructions:
            print("No route to export.")
            return
            
        filename = "route_directions.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("ROUTE MASTER NAVIGATION\n")
            f.write("=======================\n\n")
            for line in self.current_instructions:
                f.write(line + "\n")
        print(f"Route saved to {filename}")
        self.lbl_info.config(text=f"Saved to:\n{filename}", fg="#00ff00")

    def draw_route_line(self, path):
        coords = []
        for nid in path:
            n = self.graph.nodes[nid]
            coords.extend(self.to_screen(n.lat, n.lon))
        self.canvas.create_line(coords, fill="#00ff00", width=8, stipple="gray50", tags="route") 
        self.canvas.create_line(coords, fill="#00ff00", width=4, tags="route")

    def animate_click(self, x, y, radius=5, alpha=1.0):
        """ Creates a pulse animation at the click location. """
        if radius > 40: return
        
        # Draw ring
        tag = f"pulse_{id(x)}_{radius}"
        self.canvas.create_oval(x-radius, y-radius, x+radius, y+radius, 
                                outline=Theme.COLORS['highlight'], width=2, 
                                tags=(tag, "pulse_effect")) 
        
        # Fade out logic is hard in Tkinter Canvas without alpha
        # So we just expand and delete
        
        def next_frame():
            self.canvas.delete(tag)
            self.animate_click(x, y, radius + 4)
            
        self.root.after(30, next_frame)

    def reset_traffic(self):
        self.simulator.reset_all()
        if self.start_node and self.end_node and self.click_state == 2:
            self.recalculate_route()
        else:
            self.draw_map()

    # --- Geometry & Interaction ---
    def find_nearest_edge(self, ex, ey):
        """ Finds the nearest road edge using the Spatial Grid. """
        lat, lon = self.screen_to_geo(ex, ey)
        candidates = self.grid.query(lat, lon)
        
        best_edge = None
        min_dist = 20.0 # Pixel tolerance
        
        for u_id, v_id in candidates:
            if u_id not in self.graph.nodes or v_id not in self.graph.nodes: continue
            
            # Get edge object
            # We need to find the actual edge object in the list
            edge_obj = None
            for e in self.graph.edges[u_id]:
                if e['to'] == v_id:
                    edge_obj = e
                    break
            if not edge_obj: continue

            u = self.graph.nodes[u_id]
            v = self.graph.nodes[v_id]
            
            ux, uy = self.to_screen(u.lat, u.lon)
            vx, vy = self.to_screen(v.lat, v.lon)

            # --- Distance Logic ---
            dx, dy = vx - ux, vy - uy
            if dx == 0 and dy == 0: continue
            
            t = ((ex - ux) * dx + (ey - uy) * dy) / (dx*dx + dy*dy)
            t = max(0, min(1, t))
            
            nearest_x = ux + t * dx
            nearest_y = uy + t * dy
            
            dist = math.hypot(ex - nearest_x, ey - nearest_y)
            
            if dist < min_dist:
                min_dist = dist
                best_edge = (u_id, v_id)
        
        return best_edge

    def find_nearest_node(self, ex, ey):
        best_node = None
        min_dist = 30.0 
        for node in self.graph.nodes.values():
            nx, ny = self.to_screen(node.lat, node.lon)
            dist = math.hypot(ex - nx, ey - ny)
            if dist < min_dist:
                min_dist = dist
                best_node = node.id
        return best_node

    def calculate_time(self, path):
        total_seconds = 0
        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            # Find edge
            edge_found = False
            for e in self.graph.get_neighbors(u):
                if e['to'] == v:
                    edge_found = True
                    status = e.get('status', None)
                    rtype = e.get('type', 'unknown')
                    
                    # Determine limit
                    if status == 'jammed':
                        limit = Theme.SPEED_LIMITS['jammed']
                    elif status == 'blocked':
                        # If blocked, time is infinite
                        return float('inf')
                    else:
                        limit = Theme.SPEED_LIMITS.get(rtype, 30)
                    
                    # Protection against division by zero
                    speed_ms = max(1, limit) / 3.6
                    weight = e['weight']
                    
                    # If weight is infinite (blockage), time is infinite
                    if math.isinf(weight):
                        return float('inf')
                        
                    total_seconds += weight / speed_ms
                    break
            
            if not edge_found:
                return float('inf') # Path broken
                
        return total_seconds
    
    def draw_dashboard(self, distance, minutes, seconds):
        self.canvas.create_rectangle(20, 20, 250, 110, fill="#222222", outline="#444444", width=2, tags="dashboard")
        self.canvas.create_text(35, 35, text="ROUTE STATS", fill="#888888", font=("Arial", 9, "bold"), anchor="w", tags="dashboard")
        dist_str = f"{distance/1000:.2f} km" if distance > 1000 else f"{int(distance)} m"
        self.canvas.create_text(35, 60, text=f"Distance:    {dist_str}", fill="white", font=("Segoe UI", 12), anchor="w", tags="dashboard")
        time_str = f"{minutes} min {seconds} s"
        self.canvas.create_text(35, 85, text=f"Time:        {time_str}", fill="#00ff00", font=("Segoe UI", 12, "bold"), anchor="w", tags="dashboard")

    def handle_click(self, event):
        if self.mode == "NAVIGATE":
            # Routing Logic
            node = self.find_nearest_node(event.x, event.y)
            if not node: return
            nx, ny = self.to_screen(self.graph.nodes[node].lat, self.graph.nodes[node].lon)

            if self.click_state == 0:
                self.start_node = node
                self.canvas.delete("marker"); self.canvas.delete("route"); self.canvas.delete("dashboard")
                self.canvas.create_oval(nx-6, ny-6, nx+6, ny+6, fill="#00ff00", outline="white", width=2, tags="marker")
                self.click_state = 1
                self.animate_click(event.x, event.y)
            elif self.click_state == 1:
                self.end_node = node
                self.click_state = 2
                self.recalculate_route()
                self.animate_click(event.x, event.y)
            elif self.click_state == 2:
                self.start_node = node
                self.end_node = None
                self.canvas.delete("marker"); self.canvas.delete("route"); self.canvas.delete("dashboard")
                self.canvas.create_oval(nx-6, ny-6, nx+6, ny+6, fill="#00ff00", outline="white", width=2, tags="marker")
                self.click_state = 1
                self.animate_click(event.x, event.y)
        
        elif self.mode in ["JAM", "BLOCK"]:
            # Simulation Logic
            edge = self.find_nearest_edge(event.x, event.y)
            if edge:
                u, v = edge
                if self.mode == "JAM":
                    self.simulator.apply_jam(u, v)
                    print(f"Traffic jammed at: {u}-{v}")
                elif self.mode == "BLOCK":
                    self.simulator.block_road(u, v)
                    print(f"Road blocked: {u}-{v}")
                
                # If active route exists, try to reroute
                if self.start_node and self.end_node and self.click_state == 2:
                    if hasattr(self, 'anim_running') and self.anim_running and hasattr(self, 'current_route_path'):
                         # Live Rerouting
                         self.reroute_live()
                         # Force redraw to show new status colors
                         self.draw_map()
                         # Car persists now due to optimized draw_map not deleting it.
                         self.canvas.tag_raise("car") # Ensure it's on top of new road colors
                    else:
                         self.recalculate_route()
                else:
                    self.draw_map()

    def search_street(self):
        """ Searches for a street by name and centers the map on it, highlighting the first found node. """
        query = self.entry_search.get().lower().strip()
        if not query: return
        
        # O(1) Search via Index
        nodes = self.graph.street_index.get(query)
        
        if nodes:
            # Center on the first node found
            target_node_id = nodes[0]
            if target_node_id in self.graph.nodes:
                target_node = self.graph.nodes[target_node_id]
                
                # Center View
                self.offset_x = -target_node.lon * self.scale + self.width / 2
                self.offset_y = target_node.lat * self.scale + self.height / 2
                
                self.draw_map()
                self.lbl_info.config(text=f"Found: {query.title()}", fg="#00ff00")
                
                # Highlight
                cx, cy = self.to_screen(target_node.lat, target_node.lon)
                self.canvas.create_oval(cx-15, cy-15, cx+15, cy+15, outline="yellow", width=4, tags="highlight")
            else:
                self.lbl_info.config(text="Data Error", fg="red")
        else:
            self.lbl_info.config(text=f"Not found:\n{query}", fg="red")

    def on_mouse_move(self, event):
        """ Handles mouse movement to display tooltips for POIs and roads. """
        # 1. Check POIs first (Higher priority)
        if self.show_pois.get():
            for poi in self.graph.pois:
                px, py = self.to_screen(poi.lat, poi.lon)
                if abs(event.x - px) < 10 and abs(event.y - py) < 10:
                     self.tooltip.config(text=f"{poi.name} ({poi.type})", fg="#55ff55")
                     self.tooltip.place(x=event.x + 15, y=event.y + 15)
                     return # Stop checking edges if POI found

        # 2. Check Edges
        edge = self.find_nearest_edge(event.x, event.y)
        if edge:
            u_id, v_id = edge
            # Find the edge object to get the name
            name = "Unknown Road"
            if u_id in self.graph.edges:
                for e in self.graph.edges[u_id]:
                    if e['to'] == v_id:
                        name = e.get('name', 'Unknown Road')
                        break
            
            self.tooltip.config(text=name)
            self.tooltip.place(x=event.x + 15, y=event.y + 15)
        else:
            self.tooltip.place(x=-100, y=-100) # Hide

    def draw_pois(self):
        """ Draws Points of Interest (POIs) on the canvas. """
        poi_colors = {'school': '#55ff55', 'shop': '#ff55ff', 'park': '#00dd00', 'bench': '#aaaaaa'}
        
        count = 0 
        for poi in self.graph.pois:
            px, py = self.to_screen(poi.lat, poi.lon)
            
            # Simple view culling
            if px < 0 or px > self.width or py < 0 or py > self.height: continue
            
            color = poi_colors.get(poi.type, '#ffffff')
            # Draw circle
            r = 3 
            self.canvas.create_oval(px-r, py-r, px+r, py+r, fill=color, outline="black", tags="poi")
            
            count += 1
            if count > 500: break # Limit POIs for performance

    def start_animation(self):
        """ Initializes and starts the car animation along the current route. """
        if not hasattr(self, 'current_route_path') or not self.current_route_path:
            return
            
        # Create a car object
        # LOGIC CHANGE: Now storing (Lat, Lon) tuples instead of Screen (x, y)
        self.anim_path = []
        path_nodes = self.current_route_path
        
        for i in range(len(path_nodes)-1):
            u = self.graph.nodes[path_nodes[i]]
            v = self.graph.nodes[path_nodes[i+1]]
            
            # No to_screen here! We interpolate raw coordinates.
            steps = 10 
            for s in range(steps):
                t = s / steps
                # Interpolate Latitude and Longitude
                lat = u.lat + (v.lat - u.lat) * t
                lon = u.lon + (v.lon - u.lon) * t
                self.anim_path.append((lat, lon))
                
        self.anim_index = 0
        # Car creation moved to draw_car helper or animate_step logic
        # But we ensure it exists
        self.canvas.delete("car")
        self.car_id = self.canvas.create_polygon(0,0,0,0,0,0, fill="yellow", outline="white", width=1, tags="car")
        
        self.animate_step()
        
    def animate_step(self):
        """ Handles a single frame of the car animation, interpolating geographic coordinates. """
        if self.is_paused: return 

        if self.anim_index < len(self.anim_path):
            self.anim_running = True
            
            # 1. Get Geo Coords
            lat, lon = self.anim_path[self.anim_index]
            
            # 2. Project to current screen coordinates (Dynamic!)
            x, y = self.to_screen(lat, lon)
            
            # Calculate rotation dynamically based on screen projection
            angle = 0
            if self.anim_index < len(self.anim_path) - 1:
                nlat, nlon = self.anim_path[self.anim_index + 1]
                nx, ny = self.to_screen(nlat, nlon)
                angle = math.atan2(ny - y, nx - x)
            elif self.anim_index > 0:
                 plat, plon = self.anim_path[self.anim_index - 1]
                 px, py = self.to_screen(plat, plon)
                 angle = math.atan2(y - py, x - px)
            
            # Draw Triangle
            pts = [(10, 0), (-6, -6), (-6, 6)]
            rotated_pts = []
            for px, py in pts:
                rx, ry = rotate_point(px, py, 0, 0, angle)
                rotated_pts.extend([x + rx, y + ry])
                
            self.canvas.coords(self.car_id, *rotated_pts)
            self.canvas.tag_raise(self.car_id) # Ensure car is on top
            
            # --- HUD Logic ---
            total_steps = len(self.anim_path)
            path_nodes = self.current_route_path
            
            if total_steps > 0 and len(path_nodes) > 1:
                segment_idx = int((self.anim_index / total_steps) * (len(path_nodes) - 1))
                segment_idx = min(segment_idx, len(path_nodes) - 2)
                
                u, v = path_nodes[segment_idx], path_nodes[segment_idx+1]
                
                limit = 50
                road_name = "Unknown Road"
                if u in self.graph.edges:
                    for e in self.graph.edges[u]:
                        if e['to'] == v:
                            rtype = e.get('type', 'unknown')
                            status = e.get('status', None)
                            road_name = e.get('name', 'Unknown Road')
                            if status == 'jammed': limit = Theme.SPEED_LIMITS['jammed']
                            elif status == 'blocked': limit = Theme.SPEED_LIMITS['blocked']
                            else: limit = Theme.SPEED_LIMITS.get(rtype, 50)
                            break

                import random
                current_speed = limit * (0.9 + 0.2 * random.random())
                if current_speed < 0: current_speed = 0

                self.canvas.delete("hud_speed")
                self.hud.draw_speedometer(current_speed, limit)
                
                hud_text = self._update_navigation_hud(segment_idx, path_nodes, road_name)
                self.canvas.delete("hud_instr")
                self.hud.draw_navigation(hud_text)
            
            self.anim_index += 1
            self.root.after(50, self.animate_step)

        else:
            self.anim_running = False
            # Don't delete car here if we want it to persist at destination
            # self.canvas.delete(self.car_id) 
            self.canvas.delete("hud_speed")
            self.canvas.delete("hud_instr")
 
    def reroute_live(self):
         """ Dynamically recalculates the route from the car's current position to avoid obstacles. """
         print("Recalculating live route...")
         
         if not self.current_route_path: return
         
         path_nodes = self.current_route_path
         total_steps = len(self.anim_path)
         if total_steps == 0 or self.anim_index >= total_steps: return

         # 1. Identify where we are
         current_seg_idx = self.anim_index // 10
         current_seg_idx = min(current_seg_idx, len(path_nodes) - 2)
         
         next_node_id = path_nodes[current_seg_idx + 1]
         
         # 2. A* from next node to end
         new_tail_path, new_dist = a_star(self.graph, next_node_id, self.end_node)
         
         # STOP LOGIC
         if not new_tail_path:
             print("Rerouting failed: Path blocked.")
             self.anim_running = False
             self.anim_path = self.anim_path[:self.anim_index] # Keep history so car stays put
             self.hud.draw_navigation("ROUTE BLOCKED! NO PASSAGE.")
             self.draw_map()
             return
             
         # 3. Splice paths
         final_path = path_nodes[:current_seg_idx+1] + new_tail_path
         self.current_route_path = final_path
         
         # 4. Regenerate Animation Path (GEO COORDS)
         points_to_keep_count = (current_seg_idx + 1) * 10
         if points_to_keep_count > len(self.anim_path):
             points_to_keep_count = len(self.anim_path)
             
         kept_anim_path = self.anim_path[:points_to_keep_count]
         
         new_visual_points = []
         for i in range(len(new_tail_path)-1):
            u = self.graph.nodes[new_tail_path[i]]
            v = self.graph.nodes[new_tail_path[i+1]]
            
            steps = 10 
            for s in range(steps):
                t = s / steps
                # Interpolate Geo
                lat = u.lat + (v.lat - u.lat) * t
                lon = u.lon + (v.lon - u.lon) * t
                new_visual_points.append((lat, lon))
         
         self.anim_path = kept_anim_path + new_visual_points
         
         # 5. Update
         self.current_instructions = generate_instructions(self.graph, final_path)
         self.draw_map()

    def _update_navigation_hud(self, segment_idx: int, path_nodes: list[str], current_road_name: str) -> str:
        """ Calculates the instruction text for the HUD based on current position in path. """
        hud_text = "Navigating..."
        next_turn_dist = 0
        next_street_name = "Destination"
        found_turn = False
        
        u, v = path_nodes[segment_idx], path_nodes[segment_idx+1]

        current_u, current_v = u, v
        segment_weight = 0
        if current_u in self.graph.edges:
            for e in self.graph.edges[current_u]:
                if e['to'] == current_v:
                        segment_weight = e['weight']
                        break
        
        # If current road is blocked, weight is inf
        if math.isinf(segment_weight):
             return "Route blocked ahead."

        steps = 10 
        local_step = self.anim_index % steps
        t = local_step / steps
        current_seg_dist_remaining = segment_weight * (1.0 - t)
        
        next_turn_dist += current_seg_dist_remaining
        turn_direction = "straight"
        
        for i in range(segment_idx + 1, len(path_nodes) - 1):
            u2, v2 = path_nodes[i], path_nodes[i+1]
            
            seg_name = "Unknown"
            seg_len = 0
            is_blocked = False
            
            if u2 in self.graph.edges:
                for e in self.graph.edges[u2]:
                    if e['to'] == v2:
                        seg_name = e.get('name', 'Unknown')
                        seg_len = e['weight']
                        if math.isinf(seg_len): is_blocked = True
                        break
            
            # --- SAFETY CHECK ---
            if is_blocked:
                return "Route blocked ahead."
            # --------------------

            if seg_name != current_road_name and seg_name != "Unknown Road" and seg_name != "Unknown":
                next_street_name = seg_name
                found_turn = True
                if i > 0:
                        p_prev = self.graph.nodes[path_nodes[i-1]]
                        p_curr = self.graph.nodes[u2]
                        p_next = self.graph.nodes[v2]
                        turn_direction = calculate_turn_dir(p_prev.lat, p_prev.lon, 
                                                            p_curr.lat, p_curr.lon, 
                                                            p_next.lat, p_next.lon)
                break
            else:
                next_turn_dist += seg_len
        
        # --- SAFETY CHECK ---
        if math.isinf(next_turn_dist) or math.isnan(next_turn_dist):
             return "Recalculating..."
        # --------------------

        if found_turn:
                # "ravno", "lijevo", "desno" needs to be mapped if calculate_turn_dir returns Croatian
                # BUT I already updated calculate_turn_dir in `utils.py` to return english.
                
                if turn_direction == "straight":
                    hud_text = f"In {int(next_turn_dist)}m: Continue straight onto {next_street_name}"
                else:
                    hud_text = f"In {int(next_turn_dist)}m: Turn {turn_direction} onto {next_street_name}"
        else:
                hud_text = f"Go {int(next_turn_dist)}m to destination"
        
        return hud_text

    def show(self):
        """ Starts the Tkinter event loop, displaying the map application. """
        self.root.mainloop()