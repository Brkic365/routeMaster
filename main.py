"""Main entry point for RouteMaster traffic simulation.

This script serves as the entry point for the application.
It imports and runs the main function from the src package.
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from main import main

if __name__ == "__main__":
    main()

