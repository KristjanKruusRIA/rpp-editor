#!/usr/bin/env python3
"""
Main entry point for RPP Editor GUI application
"""

import sys
from pathlib import Path

# Add src to path for development
if __name__ == "__main__":
    src_path = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_path))
    
    from rpp_editor.gui import main
    main()