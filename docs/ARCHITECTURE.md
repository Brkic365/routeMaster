# RouteMaster Architecture Documentation

## Overview

RouteMaster is a traffic simulation and navigation system built with Python and Tkinter. The architecture follows clean code principles with strict separation of concerns, type safety, and modular design.

## System Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   main.py    │  │ visualizer.py│  │ui_components │  │
│  │  (Entry)     │  │  (Controller)│  │   (UI)       │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
└─────────┼──────────────────┼─────────────────┼──────────┘
          │                  │                 │
┌─────────┼──────────────────┼─────────────────┼──────────┐
│         │                  │                 │          │
│  ┌──────▼──────┐  ┌────────▼────────┐  ┌────▼──────┐  │
│  │  algorithms │  │   simulation    │  │  spatial  │  │
│  │  (A* Path)  │  │  (Traffic State)│  │  (Grid)   │  │
│  └──────┬──────┘  └────────┬────────┘  └────┬───────┘  │
│         │                  │                 │          │
│  ┌──────▼──────────────────▼─────────────────▼───────┐ │
│  │              models.py (Data Layer)                │ │
│  │         Node, Edge, Graph, POI                     │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │           parser.py (Data Loading)                  │ │
│  │         OSM XML → Graph Structure                  │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Data Models (`models.py`)

Pure data classes representing the graph structure:

- **Node**: Geographic point with ID, latitude, and longitude
- **Edge**: Directed edge with weight, type, name, and optional traffic status
- **POI**: Point of interest with location and type
- **Graph**: Container for nodes, edges, POIs, and street index

All models use Python dataclasses with complete type hints and `__repr__` methods for debugging.

### 2. Pathfinding (`algorithms.py`)

Pure functions for route calculation:

- **a_star()**: A* pathfinding with traffic awareness and turn penalties
- **reconstruct_path()**: Path reconstruction from predecessor map
- **generate_instructions()**: Turn-by-turn navigation instruction generation

Key features:
- Lazy deletion optimization
- Turn penalty calculation for smoother routes
- Dynamic weight adjustment based on traffic conditions

### 3. Traffic Simulation (`simulation.py`)

Manages traffic state and car physics:

- **TrafficSimulator**: Main simulation class
  - `apply_jam()`: Create traffic congestion
  - `block_road()`: Block road completely
  - `reset_all()`: Reset all traffic modifications
  - `interpolate_route_path()`: Generate trajectory points
  - `calculate_car_position()`: Get car position at index
  - `calculate_car_rotation()`: Calculate car rotation angle
  - `calculate_current_speed()`: Get current speed based on road conditions
  - `calculate_route_time()`: Calculate total travel time
  - `calculate_route_distance()`: Calculate total distance

### 4. Spatial Indexing (`spatial.py`)

Efficient spatial queries using hash grid:

- **SpatialGrid**: Spatial hash grid implementation
  - O(1) average time complexity for edge queries
  - Bounding box queries for viewport culling
  - Grid-based cell organization

### 5. Visualization (`visualizer.py`)

Main controller coordinating all components:

- **MapVisualizer**: Main application controller
  - **ViewManager**: Nested class for coordinate transformations
    - `geo_to_screen()`: Convert lat/lon to screen coordinates
    - `screen_to_geo()`: Convert screen to lat/lon
    - `get_visible_bounds()`: Calculate viewport bounds
    - `fit_to_bounds()`: Auto-zoom to fit area

Key responsibilities:
- Event handling (clicks, zoom, pan)
- Route visualization
- Animation loop management
- Live rerouting during navigation
- Map rendering with viewport culling

### 6. UI Components (`ui_components.py`)

Separated UI rendering logic:

- **HudRenderer**: HUD element rendering
  - `draw_legend()`: Map legend
  - `draw_speedometer()`: Speed display
  - `draw_navigation()`: Turn-by-turn instructions

- **SidebarManager**: Sidebar widget creation
  - `create_styled_button()`: Button creation with hover effects
  - Helper methods for UI elements

### 7. Configuration (`config.py`)

Centralized constants:

- **Theme**: Visual styling (colors, road styles, speed limits)
- **ViewConfig**: Viewport settings (dimensions, zoom, padding)
- **AnimationConfig**: Animation parameters (steps, delays)
- **UIConfig**: UI text and fonts
- **FileConfig**: File paths
- **PhysicsConfig**: Physics constants

### 8. Utilities (`utils.py`)

Helper functions:

- **haversine_distance()**: Calculate distance between coordinates
- **calculate_turn_dir()**: Determine turn direction from three points
- **rotate_point()**: Rotate point around center

### 9. Parser (`parser.py`)

OSM file parsing:

- **load_osm_data()**: Parse OSM XML and build graph
- **keep_only_largest_component()**: Filter to largest connected component

## Data Flow

### Route Calculation Flow

```
User clicks start/end
    ↓
MapVisualizer.handle_click()
    ↓
MapVisualizer.recalculate_route()
    ↓
algorithms.a_star(graph, start, end)
    ↓
Returns path and distance
    ↓
simulation.interpolate_route_path(path)
    ↓
Generate trajectory points
    ↓
Start animation automatically
```

### Live Rerouting Flow

```
User blocks road during navigation
    ↓
simulation.block_road(u, v)
    ↓
visualizer._reroute_live()
    ↓
Calculate current car position
    ↓
algorithms.a_star(graph, current_node, end)
    ↓
Splice new path with existing
    ↓
Regenerate trajectory
    ↓
Continue animation
```

### Rendering Flow

```
Window resize or map update
    ↓
visualizer.draw_map()
    ↓
ViewManager.get_visible_bounds()
    ↓
spatial.query_bbox(min_lat, max_lat, min_lon, max_lon)
    ↓
Filter visible edges
    ↓
ViewManager.geo_to_screen() for each edge
    ↓
Render with appropriate styles
    ↓
ui_components.HudRenderer.draw_*()
    ↓
Update HUD elements
```

## Design Patterns

### Separation of Concerns

- **Models**: Pure data, no business logic
- **Algorithms**: Pure functions, no side effects
- **Simulation**: State management, no UI
- **Visualization**: UI coordination, delegates to other modules

### ViewManager Pattern

Nested class within MapVisualizer encapsulates all coordinate transformation logic, isolating viewport math from rendering.

### Configuration Pattern

All constants centralized in config.py, eliminating magic numbers and hardcoded values throughout the codebase.

## Performance Considerations

### Spatial Hashing

- Grid-based spatial indexing for O(1) average edge queries
- Reduces search space from O(n) to O(1) for nearby edges
- Critical for interactive performance

### Viewport Culling

- Only renders edges within visible bounds
- Reduces rendering overhead for large maps
- Dynamic bounds calculation with padding

### Lazy Deletion

- A* implementation uses lazy deletion in priority queue
- Avoids expensive queue updates
- Improves pathfinding performance

## Type Safety

All functions include complete type hints:
- Function parameters typed
- Return types specified
- Generic types used (List, Dict, Tuple, Optional)
- Python 3.9+ type syntax throughout

## Error Handling

- Graph validation in parser
- Edge case handling (empty graphs, missing nodes)
- Safe division checks
- Infinity checks for blocked routes
- Graceful degradation for missing data

## Testing Considerations

The modular design facilitates testing:
- Pure functions in algorithms.py are easily testable
- Models can be instantiated independently
- Simulation logic separated from UI
- Configuration can be mocked for testing

## Future Enhancements

Potential improvements:
- Unit test suite
- Performance profiling
- Additional map formats
- Multi-threaded rendering
- Route optimization algorithms
- Real-time traffic data integration

