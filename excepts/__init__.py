# -*- coding: utf-8 -*-

"""
Exceptions and errors.

This module defines a collection of exceptions to handle errors related
to G-code processing and generation.
"""

from .gcode_errors import GCodeError
from .gcode_errors import ToolStateError
from .gcode_errors import CoolantStateError
from .device_errors import DeviceError
from .device_errors import DeviceTimeoutError
from .device_errors import DeviceConnectionError

__all__ = [
    "GCodeError",
    "ToolStateError",
    "CoolantStateError",
    "DeviceError",
    "DeviceTimeoutError",
    "DeviceConnectionError",
]
