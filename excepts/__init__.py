# -*- coding: utf-8 -*-

"""
G-code generation specific error handling.

This module defines a collection of exceptions to handle errors related
to G-code processing and generation.
"""

from .gcode_errors import GCodeError
from .gcode_errors import ToolStateError
from .gcode_errors import CoolantStateError
from .device_errors import DeviceError
from .device_errors import DeviceTimeoutError
from .device_errors import DeviceConnectionError
from .device_errors import DeviceWriteError

__all__ = [
    "GCodeError",
    "ToolStateError",
    "CoolantStateError",
    "DeviceError",
    "DeviceTimeoutError",
    "DeviceConnectionError",
    "DeviceWriteError",
]
