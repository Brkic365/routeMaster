import tkinter as tk
import math
from utils import calculate_turn_dir
from algorithms import a_star, generate_instructions
from simulation import TrafficSimulator
from spatial import SpatialGrid
from hud_renderer import HudRenderer
from utils import calculate_turn_dir

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
    'jammed':       {'width': 5, 'color': '#ff4400'}, 
    'blocked':      {'width': 5, 'color': '#ff0000'}
}

SPEED_LIMITS = {
    'motorway': 130, 'trunk': 110, 'primary': 80,
    'secondary': 60, 'tertiary': 50, 'residential': 30, 
    'motorway_link': 60, 'primary_link': 50, 'unknown': 30,
    'jammed': 10,  # Gužva = sporo
    'blocked': 0   # Blokada
}

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

        self.hud = HudRenderer(self.canvas, self.width, self.height)

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

        # Tooltip
        self.tooltip = tk.Label(self.canvas, text="", bg="#333333", fg="#00ffff", 
                                font=("Arial", 10), padx=5, pady=2, relief=tk.SOLID, borderwidth=1)
        self.tooltip.place(x=-100, y=-100)

    def fit_to_bounds(self, min_lat, max_lat, min_lon, max_lon):
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
        self.btn_nav = self.create_styled_button(self.sidebar, "📍 Navigacija", "#00ccff", lambda: self.set_mode("NAVIGATE"))
        self.btn_jam = self.create_styled_button(self.sidebar, "⚠️ Stvori Gužvu", "#ff8800", lambda: self.set_mode("JAM"))
        self.btn_block = self.create_styled_button(self.sidebar, "⛔ Zatvori Cestu", "#ff3333", lambda: self.set_mode("BLOCK"))

        # Spacer
        tk.Label(self.sidebar, bg="#2a2a2a").pack(pady=10)

        # Reset
        self.btn_reset = self.create_styled_button(self.sidebar, "🔄 Resetiraj Promet", "#555555", self.reset_traffic)
        
        # Info Panel
        self.lbl_info = tk.Label(self.sidebar, text="Mod: NAVIGACIJA\nKlikni na mapu za start.", 
                                 bg="#2a2a2a", fg="#aaaaaa", justify=tk.LEFT, wraplength=200, font=("Segoe UI", 9))
        self.lbl_info.pack(side=tk.BOTTOM, pady=30, padx=15, anchor="w")

        # Search
        tk.Label(self.sidebar, text="PRETRAGA ULICE", bg="#2a2a2a", fg="white", font=("Segoe UI", 10, "bold"), pady=10).pack()
        self.entry_search = tk.Entry(
            self.sidebar, 
            bg="#3a3a3a", fg="white", 
            insertbackground="white", 
            relief="flat", font=("Segoe UI", 11)
        )
        self.entry_search.pack(fill=tk.X, padx=15, ipady=5) # ipady for inner padding
        
        self.create_styled_button(self.sidebar, "🔍 Traži", "#444444", self.search_street)

        # Spacer
        tk.Label(self.sidebar, bg="#2a2a2a").pack(pady=10)

        # Instructions Placeholder
        tk.Label(self.sidebar, text="(Upute na mapi)", bg="#2a2a2a", fg="#777", font=("Segoe UI", 9, "italic")).pack(pady=5)
        
        # Export
        self.create_styled_button(self.sidebar, "💾 Export Rute", "#444444", self.export_route)

        # Spacer
        tk.Label(self.sidebar, bg="#2a2a2a").pack(pady=10)
        
        # Extras
        tk.Label(self.sidebar, text="DODATNO", bg="#2a2a2a", fg="white", font=("Segoe UI", 10, "bold")).pack()
        self.show_pois = tk.BooleanVar(value=False)
        
        # Checkbox Styling
        chk = tk.Checkbutton(self.sidebar, text="Prikaži POI (Škole/D)", variable=self.show_pois, 
                       bg="#2a2a2a", fg="#dddddd", selectcolor="#2a2a2a", activebackground="#2a2a2a", activeforeground="white",
                       font=("Segoe UI", 9), command=self.draw_map)
        chk.pack(anchor="w", padx=15, pady=5)
                       
        self.create_styled_button(self.sidebar, "🚗 Animiraj Promet", "#e39e54", self.start_animation)

    def set_mode(self, mode):
        self.mode = mode
        colors = {"NAVIGATE": "#00ccff", "JAM": "#ff8800", "BLOCK": "#ff0000"}
        descriptions = {
            "NAVIGATE": "Lijevi klik: Postavi Start/Cilj",
            "JAM": "Lijevi klik na cestu:\nUspori promet (x5)",
            "BLOCK": "Lijevi klik na cestu:\nPotpuno zatvori prolaz"
        }
        self.lbl_info.config(text=f"MOD: {mode}\n\n{descriptions[mode]}", fg=colors[mode])

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

    def do_pan(self, event):
        dx = event.x - self.last_mouse_x
        dy = event.y - self.last_mouse_y
        self.offset_x += dx
        self.offset_y += dy
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y
        self.draw_map()

    def do_zoom(self, event):
        factor = 1.1
        if event.num == 5 or event.delta < 0:
            self.zoom /= factor
        else:
            self.zoom *= factor
        self.draw_map()

    def draw_map(self):
        self.canvas.delete("all")
        all_edges = []
        seen = set()
        
        for u_id, edges in self.graph.edges.items():
            if u_id not in self.graph.nodes: continue
            u = self.graph.nodes[u_id]
            ux, uy = self.to_screen(u.lat, u.lon)
            
            for edge in edges:
                v_id = edge['to']
                if v_id not in self.graph.nodes: continue
                
                pair = tuple(sorted((u_id, v_id)))
                if pair in seen: continue
                seen.add(pair)
                
                v = self.graph.nodes[v_id]
                vx, vy = self.to_screen(v.lat, v.lon)
                
                # Determine style based on status
                status = edge.get('status', None)
                rtype = edge.get('type', 'unknown')
                
                if status == 'blocked':
                    style = ROAD_STYLES['blocked']
                elif status == 'jammed':
                    style = ROAD_STYLES['jammed']
                else:
                    style = ROAD_STYLES.get(rtype, ROAD_STYLES['unknown'])
                
                # Check One-Way
                is_oneway = True
                if v_id in self.graph.edges:
                    for e_back in self.graph.edges[v_id]:
                        if e_back['to'] == u_id:
                            is_oneway = False
                            break
                
                all_edges.append((style['width'], style['color'], ux, uy, vx, vy, is_oneway))

        all_edges.sort(key=lambda x: x[0])
        for w, c, ux, uy, vx, vy, is_oneway in all_edges:
            self.canvas.create_line(ux, uy, vx, vy, fill=c, width=w, capstyle=tk.ROUND)

        # POIs
        if self.show_pois.get():
            self.draw_pois()



        if not hasattr(self, 'anim_running') or not self.anim_running:
            self.hud.draw_speedometer(0, 50) 
            
        if hasattr(self, 'current_instruction_text'):
            self.hud.draw_navigation(self.current_instruction_text)

        # Draw active route
        if self.start_node and self.end_node and self.click_state == 2:
            # Crtanje markera
            sx, sy = self.to_screen(self.graph.nodes[self.start_node].lat, self.graph.nodes[self.start_node].lon)
            ex, ey = self.to_screen(self.graph.nodes[self.end_node].lat, self.graph.nodes[self.end_node].lon)
            self.canvas.create_oval(sx-6, sy-6, sx+6, sy+6, fill="#00ff00", outline="white", width=2, tags="marker")
            self.canvas.create_oval(ex-6, ey-6, ex+6, ey+6, fill="#ff0000", outline="white", width=2, tags="marker")
            
            if hasattr(self, 'current_route_path') and self.current_route_path:
                self.draw_route_line(self.current_route_path)
                time_sec = self.calculate_time(self.current_route_path)
                dist = getattr(self, 'current_route_dist', 0)
                self.draw_dashboard(dist, int(time_sec // 60), int(time_sec % 60))
            else:
                 self.canvas.create_text(100, 50, text="RUTA BLOKIRANA!", fill="red", font=("Arial", 16, "bold"), tags="dashboard")

        # Render HUD elements LAST so they are on top
        self.hud.draw_legend()
        
        # Ensure HUD is on top of everything
        self.canvas.tag_raise("legend")
        self.canvas.tag_raise("hud_speed")
        self.canvas.tag_raise("hud_instr")

    def recalculate_route(self):
        """ Ponovno računa rutu s trenutnim stanjem prometa. """
        path, dist = a_star(self.graph, self.start_node, self.end_node)
        
        self.current_route_path = path
        self.current_route_dist = dist
        
        if path:
            # Auto-Fit to Route (which will call draw_map)
            lats = [self.graph.nodes[n].lat for n in path]
            lons = [self.graph.nodes[n].lon for n in path]
            if lats and lons:
                self.fit_to_bounds(min(lats), max(lats), min(lons), max(lons))
            else:
                self.draw_map()
                
            # Generiraj instrukcije
            instructions = generate_instructions(self.graph, path)
            self.current_instructions = instructions 
        else:
            self.draw_map()

    def export_route(self):
        if not hasattr(self, 'current_instructions') or not self.current_instructions:
            print("Nema rute za export.")
            return
            
        filename = "route_directions.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("ROUTE MASTER NAVIGACIJA\n")
            f.write("=======================\n\n")
            for line in self.current_instructions:
                f.write(line + "\n")
        print(f"Ruta spremljena u {filename}")
        self.lbl_info.config(text=f"Spremljeno u:\n{filename}", fg="#00ff00")

    def draw_route_line(self, path):
        coords = []
        for nid in path:
            n = self.graph.nodes[nid]
            coords.extend(self.to_screen(n.lat, n.lon))
        self.canvas.create_line(coords, fill="#00ff00", width=8, stipple="gray50", tags="route") 
        self.canvas.create_line(coords, fill="#00ff00", width=4, tags="route")

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
        min_dist = 20.0 # Piksela tolerancije
        
        for u_id, v_id in candidates:
            if u_id not in self.graph.nodes or v_id not in self.graph.nodes: continue
            
            # Dohvati podatke o rubu
            # Moramo naći pravi edge objekt u listi
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

            # --- Isti kod za udaljenost ---
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
            for e in self.graph.get_neighbors(u):
                if e['to'] == v:
                    # Ako je gužva/blokirano, koristi taj status, inače tip ceste
                    status = e.get('status', None)
                    if status == 'jammed':
                        speed_kmh = SPEED_LIMITS['jammed']
                    elif status == 'blocked':
                        speed_kmh = SPEED_LIMITS['blocked']
                    else:
                        speed_kmh = SPEED_LIMITS.get(e.get('type'), 30)
                    
                    if speed_kmh <= 0: speed_kmh = 1 # Zaštita od dijeljenja s 0
                    
                    total_seconds += e['weight'] / (speed_kmh / 3.6)
                    break
        return total_seconds
    
    def draw_dashboard(self, distance, minutes, seconds):
        self.canvas.create_rectangle(20, 20, 250, 110, fill="#222222", outline="#444444", width=2, tags="dashboard")
        self.canvas.create_text(35, 35, text="STATISTIKA RUTE", fill="#888888", font=("Arial", 9, "bold"), anchor="w", tags="dashboard")
        dist_str = f"{distance/1000:.2f} km" if distance > 1000 else f"{int(distance)} m"
        self.canvas.create_text(35, 60, text=f"Udaljenost:  {dist_str}", fill="white", font=("Segoe UI", 12), anchor="w", tags="dashboard")
        time_str = f"{minutes} min {seconds} s"
        self.canvas.create_text(35, 85, text=f"Vrijeme:      {time_str}", fill="#00ff00", font=("Segoe UI", 12, "bold"), anchor="w", tags="dashboard")

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
            elif self.click_state == 1:
                self.end_node = node
                self.click_state = 2
                self.recalculate_route()
            elif self.click_state == 2:
                self.start_node = node
                self.end_node = None
                self.canvas.delete("marker"); self.canvas.delete("route"); self.canvas.delete("dashboard")
                self.canvas.create_oval(nx-6, ny-6, nx+6, ny+6, fill="#00ff00", outline="white", width=2, tags="marker")
                self.click_state = 1
        
        elif self.mode in ["JAM", "BLOCK"]:
            # Nova logika za simulaciju
            edge = self.find_nearest_edge(event.x, event.y)
            if edge:
                u, v = edge
                if self.mode == "JAM":
                    self.simulator.apply_jam(u, v)
                    print(f"Gužva stvorena na: {u}-{v}")
                elif self.mode == "BLOCK":
                    self.simulator.block_road(u, v)
                    print(f"Cesta zatvorena: {u}-{v}")
                
                # Ako imamo aktivnu rutu, preračunaj je (da izbjegne gužvu)
                if self.start_node and self.end_node and self.click_state == 2:
                    self.recalculate_route()
                else:
                    self.draw_map()

    def search_street(self):
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
                self.lbl_info.config(text=f"Pronađeno: {query.title()}", fg="#00ff00")
                
                # Highlight
                cx, cy = self.to_screen(target_node.lat, target_node.lon)
                self.canvas.create_oval(cx-15, cy-15, cx+15, cy+15, outline="yellow", width=4, tags="highlight")
            else:
                self.lbl_info.config(text="Greška u podacima", fg="red")
        else:
            self.lbl_info.config(text=f"Nije pronađeno:\n{query}", fg="red")

    def on_mouse_move(self, event):
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
        poi_colors = {'school': '#55ff55', 'shop': '#ff55ff', 'park': '#00dd00', 'bench': '#aaaaaa'}
        
        count = 0 
        for poi in self.graph.pois:
            px, py = self.to_screen(poi.lat, poi.lon)
            
            # Simple view culling
            if px < 0 or px > self.width or py < 0 or py > self.height: continue
            
            color = poi_colors.get(poi.type, '#ffffff')
            # Draw circle
            r = 3 
            self.canvas.create_oval(px-r, py-r, px+r, py+r, fill=color, outline="black")
            
            count += 1
            if count > 500: break # Limit POIs for performance

    def start_animation(self):
        if not hasattr(self, 'current_route_path') or not self.current_route_path:
            return
            
        # Create a car object
        # Logic: Interpolate between points on the path
        self.anim_path = []
        path_nodes = self.current_route_path
        
        for i in range(len(path_nodes)-1):
            u = self.graph.nodes[path_nodes[i]]
            v = self.graph.nodes[path_nodes[i+1]]
            ux, uy = self.to_screen(u.lat, u.lon)
            vx, vy = self.to_screen(v.lat, v.lon)
            
            steps = 10 # Frames per segment
            for s in range(steps):
                t = s / steps
                x = ux + (vx - ux) * t
                y = uy + (vy - uy) * t
                self.anim_path.append((x, y))
                
        self.anim_index = 0
        self.car_id = self.canvas.create_oval(0,0,10,10, fill="yellow", outline="white")
        self.animate_step()
        
    def animate_step(self):
        if self.anim_index < len(self.anim_path):
            self.anim_running = True
            x, y = self.anim_path[self.anim_index]
            self.canvas.coords(self.car_id, x-5, y-5, x+5, y+5)
            
            # --- Dynamic HUD Updates ---
            hud_text = "Navigacija..." 
            # 1. Calculate progress to find current edge/speed limit
            total_steps = len(self.anim_path)
            # Find which segment we are on
            path_nodes = self.current_route_path
            segment_idx = int((self.anim_index / total_steps) * (len(path_nodes) - 1))
            segment_idx = min(segment_idx, len(path_nodes) - 2)
            
            u, v = path_nodes[segment_idx], path_nodes[segment_idx+1]
            
            # Get Road Info
            limit = 50
            road_name = "Nepoznata ulica"
            if u in self.graph.edges:
                for e in self.graph.edges[u]:
                    if e['to'] == v:
                        rtype = e.get('type', 'unknown')
                        status = e.get('status', None)
                        road_name = e.get('name', 'Nepoznata ulica')
                        
                        from visualizer import SPEED_LIMITS # Import locally if needed or rely on global
                        if status == 'jammed': limit = SPEED_LIMITS['jammed']
                        elif status == 'blocked': limit = SPEED_LIMITS['blocked']
                        else: limit = SPEED_LIMITS.get(rtype, 50)
                        break

            # Simulate Speed (Random fluctuation around limit)
            import random
            current_speed = limit * (0.9 + 0.2 * random.random()) # +/- 10%
            if current_speed < 0: current_speed = 0
            
            # Draw HUDs via Helper
            self.canvas.delete("hud_speed")
            self.hud.draw_speedometer(current_speed, limit)
            
            # ...
            
            self.canvas.delete("hud_instr")
            self.hud.draw_navigation(hud_text)
            
            self.anim_index += 1
            # Calculate distance to next change of street name
            next_turn_dist = 0
            next_street_name = "Cilj"
            found_turn = False
            
            current_seg_dist_remaining = 0
            
            # Distance on current segment
            # We are at 't' (0..1) on segment u->v
            # weight is length
            # remaining = length * (1-t)
            
            # We need to find the weight of u->v again
            current_u, current_v = u, v
            segment_weight = 0
            if current_u in self.graph.edges:
                for e in self.graph.edges[current_u]:
                    if e['to'] == current_v:
                         segment_weight = e['weight']
                         break
            
            # Interpolation factor t re-calculation for distance
            steps = 10 
            # anim_index is global index. 
            # steps per segment = 10
            # local_step = anim_index % 10
            local_step = self.anim_index % steps
            t = local_step / steps
            current_seg_dist_remaining = segment_weight * (1.0 - t)
            
            next_turn_dist += current_seg_dist_remaining
            
            # Look ahead segments
            found_turn = False
            turn_direction = "ravno"
            
            for i in range(segment_idx + 1, len(path_nodes) - 1):
                u2, v2 = path_nodes[i], path_nodes[i+1]
                
                # Check name
                seg_name = "Unknown"
                seg_len = 0
                if u2 in self.graph.edges:
                    for e in self.graph.edges[u2]:
                        if e['to'] == v2:
                            seg_name = e.get('name', 'Unknown')
                            seg_len = e['weight']
                            break
                
                if seg_name != road_name and seg_name != "Unknown Road" and seg_name != "Unknown":
                    # Changed street!
                    next_street_name = seg_name
                    found_turn = True
                    
                    # Calculate Turn Direction
                    # Points: P1 (prev node), P2 (current node u2, which is the intersection), P3 (next node v2)
                    # We need the node BEFORE u2 in the path. path_nodes[i] is u2. path_nodes[i-1] is previous.
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
            
            if found_turn:
                 if turn_direction == "ravno":
                     hud_text = f"Za {int(next_turn_dist)}m: Nastavite ravno u {next_street_name}"
                 else:
                     hud_text = f"Za {int(next_turn_dist)}m: Skrenite {turn_direction} u {next_street_name}"
            else:
                 hud_text = f"Vozite {int(next_turn_dist)}m do cilja"
            
            self.canvas.delete("hud_instr")

            self.hud.draw_navigation(hud_text)
            
            self.anim_index += 1
            self.root.after(50, self.animate_step) # Slower delay for visibility
        else:
            self.anim_running = False
            self.canvas.delete(self.car_id)
            self.canvas.delete("hud_speed") # Clean up
            self.canvas.delete("hud_instr")

    def show(self):
        self.root.mainloop()