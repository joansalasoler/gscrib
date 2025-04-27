# -*- coding: utf-8 -*-

# Gscrib. Supercharge G-code with Python.
# Copyright (C) 2025 Joan Sala <contact@joansala.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Built-in enums to G-Code mappings.
"""

from gscrib.enums.types import *
from gscrib.enums.units import *
from .gcode_table import GCodeEntry, GCodeTable


gcode_table = GCodeTable((

    # ------------------------------------------------------------------
    # Positioning
    # ------------------------------------------------------------------

    GCodeEntry(PositioningMode.RAPID,
        "G00", "Rapid positioning"
    ),

    GCodeEntry(PositioningMode.LINEAR,
        "G01", "Linear interpolation"
    ),

    GCodeEntry(PositioningMode.OFFSET,
        "G92", "Set axis position"
    ),

    GCodeEntry(PositioningMode.HOME,
        "G28", "Auto-home axes"
    ),

    # ------------------------------------------------------------------
    # Probing
    # ------------------------------------------------------------------

    GCodeEntry(ProbingMode.TOWARDS,
        "G38.2", "Probe towards"
    ),

    GCodeEntry(ProbingMode.TOWARDS_NO_ERROR,
        "G38.3", "Probe towards, no error"
    ),

    GCodeEntry(ProbingMode.AWAY,
        "G38.4", "Probe away"
    ),

    GCodeEntry(ProbingMode.AWAY_NO_ERROR,
        "G38.5", "Probe away, no error"
    ),

    # ------------------------------------------------------------------
    # Length Units
    # ------------------------------------------------------------------

    GCodeEntry(LengthUnits.INCHES,
        "G20", "Set length units, inches"
    ),

    GCodeEntry(LengthUnits.MILLIMETERS,
        "G21", "Set length units, millimeters"
    ),

    # ------------------------------------------------------------------
    # Distance Modes
    # ------------------------------------------------------------------

    GCodeEntry(DistanceMode.ABSOLUTE,
        "G90", "Set distance mode, absolute"
    ),

    GCodeEntry(DistanceMode.RELATIVE,
        "G91", "Set distance mode, relative"
    ),

    # ------------------------------------------------------------------
    # Extrusion Modes
    # ------------------------------------------------------------------

    GCodeEntry(ExtrusionMode.ABSOLUTE,
        "M82", "Set extrusion mode, absolute"
    ),

    GCodeEntry(ExtrusionMode.RELATIVE,
        "M83", "Set extrusion mode, relative"
    ),

    # ------------------------------------------------------------------
    # Feed Rate Modes
    # ------------------------------------------------------------------

    GCodeEntry(FeedMode.INVERSE_TIME,
        "G93", "Set feed rate mode, inverse time"
    ),

    GCodeEntry(FeedMode.UNITS_PER_MINUTE,
        "G94", "Set feed rate mode, units per minute"
    ),

    GCodeEntry(FeedMode.UNITS_PER_REVOLUTION,
        "G95", "Set feed rate mode, units per revolution"
    ),

    # ------------------------------------------------------------------
    # Tool Control
    # ------------------------------------------------------------------

    GCodeEntry(SpinMode.CLOCKWISE,
        "M03", "Start tool, clockwise"
    ),

    GCodeEntry(SpinMode.COUNTER,
        "M04", "Start tool, counterclockwise"
    ),

    GCodeEntry(SpinMode.OFF,
        "M05", "Stop tool"
    ),

    GCodeEntry(PowerMode.CONSTANT,
        "M03", "Start tool, constant power"
    ),

    GCodeEntry(PowerMode.DYNAMIC,
        "M04", "Start tool, dynamic power"
    ),

    GCodeEntry(PowerMode.OFF,
        "M05", "Stop tool"
    ),

    # ------------------------------------------------------------------
    # Tool Swap Modes
    # ------------------------------------------------------------------

    GCodeEntry(ToolSwapMode.AUTOMATIC,
        "M06", "Tool change, automatic"
    ),

    GCodeEntry(ToolSwapMode.MANUAL,
        "M06", "Tool change, manual"
    ),

    # ------------------------------------------------------------------
    # Coolant Control Modes
    # ------------------------------------------------------------------

    GCodeEntry(CoolantMode.MIST,
        "M07", "Turn on coolant, mist"
    ),

    GCodeEntry(CoolantMode.FLOOD,
        "M08", "Turn on coolant, flood"
    ),

    GCodeEntry(CoolantMode.OFF,
        "M09", "Turn off coolant"
    ),

    # ------------------------------------------------------------------
    # Fan Control Modes
    # ------------------------------------------------------------------

    GCodeEntry(FanMode.COOLING,
        "M106", "Set fan speed"
    ),

    GCodeEntry(FanMode.OFF,
        "M106", "Turn off fan"
    ),

    # ------------------------------------------------------------------
    # Temperature Control
    # ------------------------------------------------------------------

    GCodeEntry(BedTemperature.CELSIUS,
        "M140", "Set bed temperature, celsius"
    ),

    GCodeEntry(BedTemperature.KELVIN,
        "M140", "Set bed temperature, kelvin"
    ),

    GCodeEntry(HotendTemperature.CELSIUS,
        "M104", "Set hotend temperature, celsius"
    ),

    GCodeEntry(HotendTemperature.KELVIN,
        "M104", "Set hotend temperature, kelvin"
    ),

    GCodeEntry(ChamberTemperature.CELSIUS,
        "M141", "Set chamber temperature, celsius"
    ),

    GCodeEntry(ChamberTemperature.KELVIN,
        "M141", "Set chamber temperature, kelvin"
    ),

    # ------------------------------------------------------------------
    # Plane Selection
    # ------------------------------------------------------------------

    GCodeEntry(Plane.XY,
        "G17", "Select plane, XY"
    ),

    GCodeEntry(Plane.YZ,
        "G19", "Select plane, YZ"
    ),

    GCodeEntry(Plane.ZX,
        "G18", "Select plane, ZX"
    ),

    # ------------------------------------------------------------------
    # Sleep/Dwell Modes
    # ------------------------------------------------------------------

    GCodeEntry(TimeUnits.SECONDS,
        "G04", "Sleep for a while, seconds"
    ),

    GCodeEntry(TimeUnits.MILLISECONDS,
        "G04", "Sleep for a while, milliseconds"
    ),

    # ------------------------------------------------------------------
    # Halt Modes
    # ------------------------------------------------------------------

    GCodeEntry(HaltMode.PAUSE,
        "M00", "Pause program, forced"
    ),

    GCodeEntry(HaltMode.OPTIONAL_PAUSE,
        "M01", "Pause program, optional"
    ),

    GCodeEntry(HaltMode.END_WITHOUT_RESET,
        "M02", "End of program, no reset"
    ),

    GCodeEntry(HaltMode.END_WITH_RESET,
        "M30", "End of program, stop and reset"
    ),

    GCodeEntry(HaltMode.PALLET_EXCHANGE,
        "M60", "Exchange pallet and end program"
    ),

    GCodeEntry(HaltMode.WAIT_FOR_BED,
        "M190", "Wait for bed to reach temperature"
    ),

    GCodeEntry(HaltMode.WAIT_FOR_HOTEND,
        "M109", "Wait for hotend to reach temperature"
    ),

    GCodeEntry(HaltMode.WAIT_FOR_CHAMBER,
        "M191", "Wait for chamber to reach temperature"
    ),

    GCodeEntry(HaltMode.WAIT_FOR_MOTION,
        "M400", "Wait for all moves to finish"
    ),

))
