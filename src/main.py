"""Main entry point for RouteMaster traffic simulation."""

import os
from pathlib import Path
from parser import load_osm_data
from visualizer import MapVisualizer
from config import FileConfig


def main() -> None:
    """Initialize and launch the RouteMaster application."""
    print("Loading map data...")
    
    # Handle path resolution - if running from root, adjust path
    osm_file = FileConfig.DEFAULT_OSM_FILE
    if not os.path.exists(osm_file):
        # Try relative to project root
        project_root = Path(__file__).parent.parent
        osm_file = project_root / osm_file
        if not osm_file.exists():
            osm_file = FileConfig.DEFAULT_OSM_FILE
    
    graph = load_osm_data(str(osm_file))

    if not graph or len(graph.nodes) < 2:
        print("Failed to load graph data.")
        return

    print("Launching visualizer...")
    viz = MapVisualizer(graph)

    viz.draw_map()
    viz.show()


if __name__ == "__main__":
    main()