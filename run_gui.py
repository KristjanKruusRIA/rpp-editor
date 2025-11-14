#!/usr/bin/env python3
"""
Convenience script to run the RPP Editor GUI.

This script can be used to quickly start the GUI application
without needing to import from the package structure.
"""

import sys
from pathlib import Path

# Add src to path so we can import the package
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from rpp_editor.gui import main

if __name__ == "__main__":
    main()