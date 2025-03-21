# -*- coding: utf-8 -*-

"""
G-code writer module.

This module provides utilities for writing G-code to different outputs,
including files, network sockets, and serial connections.
"""

from .printcore import printcore

__all__ = [
    "printcore",
]
