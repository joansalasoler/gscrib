# -*- coding: utf-8 -*-

"""Common hooks for standard operations.

This module provides methods to create hooks for common operations.
Includes hooks for extrusion and height compensation.
"""

from .extrusion_hook import extrusion_hook
from .heightmap_hook import heightmap_hook

__all__ = [
    "extrusion_hook",
    "heightmap_hook"
]
