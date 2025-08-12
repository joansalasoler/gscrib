# -*- coding: utf-8 -*-

"""Utilities for path generation and transformations.

This module provides tools for working with geometric paths and coordinate
transformations. It includes functionality for tracing paths and applying
transformations to coordinate systems."
"""

from .point import Point
from .bounds import Bound, BoundManager
from .tracer import PathTracer
from .transformer import CoordinateTransformer
from .transform import Transform
from .patterns import grid

__all__ = [
    "Point",
    "PathTracer",
    "CoordinateTransformer",
    "Transform",
    "Bound",
    "BoundManager",
    "grid",
]
