# RouteMaster 🚗🗺️

**RouteMaster** is a modern Python-based traffic simulation and navigation application. It visualizes OpenStreetMap (OSM) data, calculates optimal routes using the A* algorithm, and provides a rich set of interactive features including real-time traffic simulation, turn-by-turn navigation, and POI visualization.

![RouteMaster Screenshot](https://via.placeholder.com/800x450.png?text=RouteMaster+Screenshot) 
*(Note: Replace with an actual screenshot if available)*

## ✨ Key Features

### 🖥️ Interactive Visualization
- **Cyberpunk / Neon Night Theme:** A visually striking dark mode with neon accents for roads and routes.
- **Zoom & Pan:** Fully interactive map control using mouse wheel and right-click drag.
- **Instant Interaction:** Optimized with a **Spatial Grid** system for high performance even on large maps.

### 📍 Navigation & Routing
- **A* Algorithm:** Efficiently finds the shortest path between two points.
- **Smart HUD:** Heads-Up Display showing:
  - **Next Turn Instructions:** Dynamic "Turn Left/Right in X meters" updates.
  - **Speedometer:** Real-time speed and limit display.
  - **Street Name:** Current street name overlay.
- **Export Route:** Save detailed textual directions to a `.txt` file.

### 🚗 Traffic Simulation
- **Dynamic Traffic:** "Animiraj Promet" mode visualizes a car driving along the route.
- **Traffic Control:** Manually create **Traffic Jams** (Orange) or **Block Roads** (Red) to test rerouting.
- **Points of Interest (POI):** Toggle visualization for Schools, Shops, and Parks.

## 🛠️ Technology Stack
- **Language:** Python 3.x
- **GUI Framework:** Tkinter (Standard Library)
- **Data Source:** OpenStreetMap (`.osm` XML format)
- **Algorithms:** A* (Pathfinding), Haversine (Distance), Cross Product (Geometry/Turn Direction)
- **Zero External Dependencies:** Built entirely using Python's standard library.

## 🚀 How to Run

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Brkic365/routeMaster.git
    cd routeMaster
    ```

2.  **Prepare Map Data:**
    - Ensure you have a valid `mapa.osm` file in the project directory.
    - *Note: Included map files like `mapa.osm` or `mapa_sava.osm` can be used.*

3.  **Run the application:**
    ```bash
    python main.py
    ```

## 🎮 Controls

| Action | Control |
| :--- | :--- |
| **Select Start/End** | Left Click on map |
| **Zoom** | Mouse Wheel |
| **Pan** | Right Click + Drag |
| **Hover** | Mouse over streets/POIs for details |
| **Search** | Type street name in Sidebar + "Traži" |
| **Animation** | Click "Animiraj Promet" in Sidebar |

## 📂 Project Structure

- `main.py`: Entry point of the application.
- `visualizer.py`: Handles all GUI, drawing, and interactive logic (Tkinter).
- `algorithms.py`: Pathfinding (A*) and instruction generation logic.
- `parser.py`: XML parsing of OSM data.
- `models.py`: Data structures for Graph, Nodes, Edges, and POIs.
- `simulation.py`: Traffic interaction logic (jams/blocks).
- `spatial.py`: Spatial Grid optimization for fast queries.
- `utils.py`: Geometry and math helper functions.

## 📝 License

This project is open-source and available for educational purposes.

---
*Created by [Brkic365](https://github.com/Brkic365)*
