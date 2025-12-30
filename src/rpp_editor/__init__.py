"""
RPP Editor - REAPER Project File Editor

A Python package for parsing, comparing, and editing REAPER project files (.rpp).
"""

from .gui import RPPEditorGUI
from .parser import RPPParser, TrackInfo, compare_tracks

__version__ = "1.1.3"
__author__ = "RPP Editor Contributors"
__all__ = ["RPPParser", "TrackInfo", "compare_tracks", "RPPEditorGUI"]
