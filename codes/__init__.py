# -*- coding: utf-8 -*-

"""
Converts enums to G-Code instructions.

This module contains a table that translates our internal enum
values into their corresponding G-Code instructions. The `GBuilder`
class uses this mapping to generate valid G-Code output.
"""

from .mappings import gcode_table
from .gcode_entry import GCodeEntry
from .gcode_table import GCodeTable

__all__ = [
    "GCodeTable",
    "GCodeEntry",
    "gcode_table",
]
