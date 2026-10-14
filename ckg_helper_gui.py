"""
CKG Helper - Graphical User Interface (GUI)
Menggunakan CustomTkinter untuk antarmuka desktop modern.
"""
import sys
from pathlib import Path

# Pastikan root direktori ada di sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.gui.app import main

if __name__ == "__main__":
    main()
