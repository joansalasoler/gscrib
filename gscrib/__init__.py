# -*- coding: utf-8 -*-

"""Core G-code generation and output management.

This module provides high-level builders for generating G-code commands
for CNC machines, 3D printers, laser cutters, and similar devices
"""

from . import enums
from . import excepts
from . import formatters
from . import writers
from . import geometry

from .config import GConfig
from .gcode_builder import GCodeBuilder
from .gcode_core import GCodeCore
from .gcode_state import GState
from .params import ParamsDict
from .geometry import Point, PointLike

__version__ = "0.1.0"

__all__ = [
    "GCodeCore",
    "GCodeBuilder",
    "GConfig",
    "GState",
    "ParamsDict",
    "Point",
    "PointLike",
    "formatters",
    "writers",
    "enums",
    "excepts",
    "geometry",
]
