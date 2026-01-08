# RouteMaster

A high-performance Python-based traffic simulation and navigation system designed for real-time pathfinding on OpenStreetMap (OSM) data. RouteMaster features a custom spatial hashing engine for efficient queries, dynamic A\* rerouting, and an interactive visualization dashboard.

## Features

### Core Functionality

- **Advanced Pathfinding**: Implementation of the A\* algorithm with lazy deletion optimization and dynamic weight adjustments for traffic conditions
- **Spatial Hashing**: Custom `SpatialGrid` class enabling O(1) average time complexity for spatial lookups, replacing slow iterative searches
- **Live Traffic Simulation**: Interactive traffic jam creation and road blocking with immediate path recalculation
- **Dynamic Rerouting**: Automatic route recalculation when obstacles are encountered during navigation
- **Geographic Projection**: Accurate mapping of latitude/longitude to screen coordinates with zoom and pan capabilities
- **Interactive HUD**: Real-time speedometer, turn-by-turn navigation, and route statistics dashboard

### User Interface

- **Flexible Viewport**: Responsive canvas that adapts to window resizing
- **Interactive Map Controls**: Zoom, pan, and click-based navigation
- **Multiple Interaction Modes**: Navigate, create traffic jams, or block roads
- **Point of Interest Visualization**: Display schools, shops, and other POIs on the map
- **Street Search**: Quick search and navigation to specific streets

## Requirements

- Python 3.9 or higher
- Tkinter (included with Python standard library)
- OpenStreetMap XML data files (.osm format)

## Installation

1. Clone or download the repository:

   ```bash
   git clone <repository-url>
   cd routeMaster2
   ```

2. Ensure you have OSM map data files in the `data/` directory. The default file is `data/mapa_trg.osm`. You can download OSM data from [OpenStreetMap](https://www.openstreetmap.org/) or use the provided sample files.

3. Run the application:
   ```bash
   python main.py
   ```

## Usage

### Basic Navigation

1. **Set Start Point**: Click the "Navigate" button (blue), then click on the map to set your starting location (green marker)
2. **Set End Point**: Click on the map again to set your destination (red marker)
3. **Automatic Start**: The route is calculated and animation begins automatically

### Interactive Controls

#### Navigation Mode

- **Left Click**: Set start and end points for routing
- **Right Click + Drag**: Pan the map view
- **Mouse Wheel**: Zoom in/out

#### Traffic Jam Mode

- Click "Create Traffic Jam" (orange button)
- Click on any road to create congestion (slows traffic by 5x)
- Route automatically recalculates if affected

#### Block Road Mode

- Click "Block Road" (red button)
- Click on any road to completely block it
- Route automatically recalculates or displays "ROUTE BLOCKED" if no alternative exists

#### During Navigation

- **Pause/Resume**: Click "Pause" to pause animation, "Resume" to continue
- **Complete Restart**: Click "Complete Restart" to reset all traffic conditions, clear route, and return to initial state

### Additional Features

- **Street Search**: Enter a street name in the search box and click "Search" to navigate to it
- **POI Display**: Check "Show POI (School/Shop)" to display points of interest on the map
- **Export Route**: Click "Export Route" to save turn-by-turn directions to a text file

## Project Structure

```
routeMaster2/
├── src/                    # Source code
│   ├── __init__.py
│   ├── main.py            # Application entry point
│   ├── visualizer.py      # Main GUI controller and visualization
│   ├── models.py          # Data models (Node, Edge, Graph, POI)
│   ├── algorithms.py      # A* pathfinding and instruction generation
│   ├── simulation.py      # Traffic simulation and car physics
│   ├── parser.py          # OSM file parser
│   ├── spatial.py         # Spatial hash grid implementation
│   ├── utils.py           # Utility functions (geometry, distance)
│   ├── config.py          # Configuration constants
│   └── ui_components.py   # UI components (HUD, sidebar)
├── data/                  # Data files
│   ├── mapa_trg.osm      # Default map data
│   └── *.osm             # Additional OSM files
├── docs/                  # Documentation
│   └── ARCHITECTURE.md   # Technical architecture documentation
└── README.md             # This file
```

## Architecture

RouteMaster follows a modular architecture with clear separation of concerns:

- **Models**: Pure data classes representing the graph structure
- **Algorithms**: Pure functions for pathfinding and route generation
- **Simulation**: Traffic state management and car physics calculations
- **Visualization**: UI rendering and user interaction handling
- **Spatial**: Efficient spatial indexing for performance optimization

For detailed technical documentation, see `docs/ARCHITECTURE.md`.

## Configuration

All application constants are centralized in `src/config.py`:

- **Theme**: Visual styling (colors, road styles, speed limits)
- **ViewConfig**: Viewport and rendering settings
- **AnimationConfig**: Animation and interpolation parameters
- **UIConfig**: User interface text and styling
- **FileConfig**: File paths and export settings
- **PhysicsConfig**: Physics and simulation constants

## Performance Optimizations

- **Spatial Hashing**: O(1) average time complexity for edge queries
- **Viewport Culling**: Only renders visible map elements
- **Lazy Deletion**: Optimized A\* implementation with priority queue management
- **Efficient Rendering**: Layered drawing with tag-based element management

## Technical Details

### Pathfinding Algorithm

The A\* implementation includes:

- Heuristic function using Haversine distance
- Turn penalty calculation for smoother routes
- Dynamic weight adjustment based on traffic conditions
- Lazy deletion optimization for better performance

### Coordinate System

- Geographic coordinates (latitude/longitude) are projected to screen coordinates
- Aspect ratio correction for accurate distance representation
- Zoom and pan transformations applied to viewport

### Traffic Simulation

- Edge weights modified dynamically based on traffic conditions
- Speed limits vary by road type and traffic status
- Car position calculated through interpolation along route segments
- Real-time speed calculation with variance for realism

## Contributing

This project follows clean code principles:

- Type hints required for all functions
- Google-style docstrings for all classes and public methods
- Modular design with clear separation of concerns
- Constants centralized in configuration files
- No hardcoded values in business logic

## License

This project was developed for educational purposes and professional portfolio demonstration.

## Authors

- Antonio Brkic
- Francesco Marko Livaic

Developed for Advanced Python Algorithms Class / Professional Portfolio.
