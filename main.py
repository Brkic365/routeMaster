from parser import load_osm_data
from visualizer import MapVisualizer

OSM_FILE = "mapa_trg.osm"

def main():
    print("Učitavam podatke...")
    graph = load_osm_data(OSM_FILE)
    
    if not graph or len(graph.nodes) < 2:
        print("Neuspješno učitavanje grafa.")
        return

    print("Pokrećem vizualizaciju...")
    viz = MapVisualizer(graph)
    
    # Prvo nacrtamo mapu
    viz.draw_map()
    
    # Onda prepustimo kontrolu korisniku
    viz.show()

if __name__ == "__main__":
    main()