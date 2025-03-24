# -*- coding: utf-8 -*-

"""
Maps machine operations to G/M-code commands.

This module contains a table that translates our internal enum
values into their corresponding G-Code instructions. The `GCodeBuilder`
class uses this mapping to generate valid G-Code output.
"""

from .gcode_mappings import gcode_table
from .gcode_entry import GCodeEntry
from .gcode_table import GCodeTable

__all__ = [
    "GCodeTable",
    "GCodeEntry",
    "gcode_table",
]
