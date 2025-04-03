# -*- coding: utf-8 -*-

"""
G-code specific modes and parameter types.

This module contains enumeration classes that define different machine
states, options, and configurations for G-code generation. Each enum
value is linked to a specific G-Code instruction and a description, which
are stored in the `codes.codes_table`. The `GCodeBuilder` class
uses this table to create the appropriate G-code statements.
"""

from .base_enum import BaseEnum
from .modes import DirectWrite
from .types import Axis
from .types import BedTemperature
from .types import CoolantMode
from .types import Direction
from .types import DistanceMode
from .types import ExtrusionMode
from .types import FanMode
from .types import FeedMode
from .types import HaltMode
from .types import HotendTemperature
from .types import Plane
from .types import PositioningMode
from .types import PowerMode
from .types import SpinMode
from .types import ToolSwapMode
from .units import LengthUnits
from .units import TemperatureUnits
from .units import TimeUnits

__all__ = [
    "BaseEnum",
    "Axis",
    "DirectWrite",
    "BedTemperature",
    "CoolantMode",
    "Direction",
    "DistanceMode",
    "ExtrusionMode",
    "FanMode",
    "FeedMode",
    "HaltMode",
    "HotendTemperature",
    "Plane",
    "PositioningMode",
    "PowerMode",
    "SpinMode",
    "ToolSwapMode",
    "LengthUnits",
    "TemperatureUnits",
    "TimeUnits",
]
