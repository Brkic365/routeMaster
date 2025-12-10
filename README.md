# RouteMaster - Traffic Simulation & Navigation Engine

**RouteMaster** is a high-performance Python-based traffic simulation and navigation system designed for real-time pathfinding on OpenStreetMap (OSM) data. It features a custom **Spatial Hashing** engine for O(1) queries, dynamic A* rerouting, and an interactive visualizations dashboard.

![RouteMaster Navigation Mode](https://ibb.co/CKz2vJ32) *Representative Image*

## 🚀 Key Features

*   **Advanced Pathfinding**: Implementation of the **A* Algorithm** with "Lazy Deletion" and dynamic weight adjustments for traffic jams.
*   **Spatial Hashing**: Custom `SpatialGrid` class enabling efficient O(1) spatial lookups for roads and interactions, replacing slow iterative searches.
*   **Live Traffic Simulation**:
    *   **Traffic Jams**: Interactively create congestion zones that slow down routing agents.
    *   **Road Blocks**: Dynamically close roads, triggering immediate path recalculation (Live Rerouting).
*   **Geographic Projection**: Accurate mapping of Latitude/Longitude to screen coordinates with Zoom/Pan capabilities.
*   **Interactive HUD**:
    *   Real-time Speedometer & Turn-by-Turn Navigation.
    *   Dynamic Dashboard for route statistics (Time/Distance).
    *   Map Legend & POI Visualization (Schools, Shops, etc.).

## 🛠️ Tech Stack

*   **Language**: Python 3.9+
*   **GUI Framework**: Tkinter (Canvas-based rendering)
*   **Data Format**: OpenStreetMap XML (.osm)
*   **Algorithms**: A*, Spatial Hashing, Queue/PriorityQueue.

## 📦 Installation & Usage

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/Brkic365/RouteMaster.git
    cd RouteMaster
    ```

2.  **Ensure Map Data**:
    Place your `.osm` file (e.g., `mapa_trg.osm`) in the root directory. Update `config.py` or `main.py` if the filename differs.

3.  **Run the Application**:
    ```bash
    python main.py
    ```

## 🎮 Controls

| Mode | Action | Description |
| :--- | :--- | :--- |
| **Navigate** | Left Click | Set **Start** (Green) and **End** (Red) points for routing. |
| **Traffic Jam** | Left Click on Road | Creates a traffic jam (Orange), increasing travel cost x5. |
| **Block Road** | Left Click on Road | Blocks the road (Red), forcing a reroute. |
| **Map View** | Right Click + Drag | Pan the map view. |
| **Zoom** | Scroll Wheel | Zoom in/out. |

## 📂 Project Structure

*   `main.py`: Entry point.
*   `visualizer.py`: Core GUI logic, rendering engine, and animation loop.
*   `algorithms.py`: A* implementation and instruction generation.
*   `spatial.py`: Spatial Hashing implementation for optimization.
*   `models.py`: Data structures (Node, Edge, Graph, POI).
*   `config.py`: Configuration text, colors, and speed limits.
*   `hud_renderer.py`: Heads-Up Display (HUD) drawing logic.
*   `utils.py`: Helper functions (Geo-distance, geometry).

---
*Created by [Antonio Brkic](https://github.com/Brkic365)[Francesco Marko Livaic](https://github.com/markolivaic)*
*Developed for Advanced Python Algorithms Class / Professional Portfolio.*
