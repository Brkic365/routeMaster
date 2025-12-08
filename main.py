from parser import load_osm_data
from visualizer import MapVisualizer

OSM_FILE = "mapa_trg.osm"

def main():
    print("Loading map data...")
    graph = load_osm_data(OSM_FILE)
    
    if not graph or len(graph.nodes) < 2:
        print("Failed to load graph data.")
        return

    print("Launching visualizer...")
    viz = MapVisualizer(graph)
    
    # Draw initial map state
    viz.draw_map()
    
    # Hand over control to UI
    viz.show()

if __name__ == "__main__":
    main()