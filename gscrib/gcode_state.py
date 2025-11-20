# -*- coding: utf-8 -*-
# pylint: disable=no-member

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

from typing import Any
from typeguard import typechecked

from gscrib.geometry.bounds import Bound, BoundManager
from gscrib.geometry.point import Point
from gscrib.params import ParamsDict
from gscrib.excepts import CoolantStateError, ToolStateError
from gscrib.enums import *


class GState:
    """Manages and tracks the state of the G-code machine.

    This class maintains the current state of various G-code machine
    parameters. It provides methods to retrieve and safely modify these
    states while enforcing validation rules.
    """

    __slots__ = (
        "_user_bounds",
        "_current_axes",
        "_current_params",
        "_current_tool_number",
        "_current_tool_power",
        "_current_spin_mode",
        "_current_power_mode",
        "_current_distance_mode",
        "_current_extrusion_mode",
        "_current_coolant_mode",
        "_current_feed_mode",
        "_current_feed_rate",
        "_current_tool_swap_mode",
        "_current_halt_mode",
        "_current_length_units",
        "_current_time_units",
        "_current_temperature_units",
        "_current_plane",
        "_current_direction",
        "_current_resolution",
        "_is_coolant_active",
        "_is_tool_active",
        "_target_hotend_temperature",
        "_target_bed_temperature",
        "_target_chamber_temperature",
    )

    def __init__(self) -> None:
        self._user_bounds = BoundManager()
        self._current_axes = Point.zero()
        self._current_params = ParamsDict()
        self._current_tool_number: int = 0
        self._current_tool_power: float = 0
        self._current_feed_rate: float = 0
        self._current_tool_swap_mode = ToolSwapMode.OFF
        self._target_hotend_temperature: float = float("-inf")
        self._target_bed_temperature: float = float("-inf")
        self._target_chamber_temperature: float = float("-inf")
        self._is_coolant_active: bool = False
        self._is_tool_active: bool = False
        self._set_spin_mode(SpinMode.OFF)
        self._set_power_mode(PowerMode.OFF)
        self._set_distance_mode(DistanceMode.ABSOLUTE)
        self._set_extrusion_mode(ExtrusionMode.ABSOLUTE)
        self._set_coolant_mode(CoolantMode.OFF)
        self._set_feed_mode(FeedMode.UNITS_PER_MINUTE)
        self._set_halt_mode(HaltMode.OFF)
        self._set_length_units(LengthUnits.MILLIMETERS)
        self._set_time_units(TimeUnits.SECONDS)
        self._set_temperature_units(TemperatureUnits.CELSIUS)
        self._set_plane(Plane.XY)
        self._set_direction(Direction.CLOCKWISE)
        self._set_resolution(0.1) # mm

    @property
    def position(self) -> Point:
        """Current absolute position of the axes."""
        return self._current_axes

    @property
    def is_coolant_active(self) -> bool:
        """Check if coolant is currently active."""
        return self._is_coolant_active

    @property
    def is_tool_active(self) -> bool:
        """Check if tool is currently active."""
        return self._is_tool_active

    @property
    def tool_number(self) -> int:
        """Get the current tool number."""
        return self._current_tool_number

    @property
    def tool_power(self) -> float:
        """Get the current tool power."""
        return self._current_tool_power

    @property
    def feed_rate(self) -> float:
        """Get the current feed rate."""
        return self._current_feed_rate

    @property
    def spin_mode(self) -> SpinMode:
        """Get the current spin mode."""
        return self._current_spin_mode

    @property
    def power_mode(self) -> PowerMode:
        """Get the current power mode."""
        return self._current_power_mode

    @property
    def coolant_mode(self) -> CoolantMode:
        """Get the current coolant mode."""
        return self._current_coolant_mode

    @property
    def distance_mode(self) -> DistanceMode:
        """Get the current distance mode."""
        return self._current_distance_mode

    @property
    def extrusion_mode(self) -> ExtrusionMode:
        """Get the current extrusion mode."""
        return self._current_extrusion_mode

    @property
    def feed_mode(self) -> FeedMode:
        """Get the current feed mode."""
        return self._current_feed_mode

    @property
    def tool_swap_mode(self) -> ToolSwapMode:
        """Get the current tool swap mode."""
        return self._current_tool_swap_mode

    @property
    def halt_mode(self) -> HaltMode:
        """Get the current halt mode."""
        return self._current_halt_mode

    @property
    def length_units(self) -> LengthUnits:
        """Get the current length units sytem."""
        return self._current_length_units

    @property
    def time_units(self) -> TimeUnits:
        """Get the current time units sytem."""
        return self._current_time_units

    @property
    def temperature_units(self) -> TemperatureUnits:
        """Get the current temperature units sytem."""
        return self._current_temperature_units

    @property
    def plane(self) -> Plane:
        """Get the current working plane."""
        return self._current_plane

    @property
    def direction(self) -> Direction:
        """Get the current direction for interpolated moves."""
        return self._current_direction

    @property
    def resolution(self) -> float:
        """Get the current resolution for interpolated moves."""
        return self._current_resolution

    @property
    def target_hotend_temperature(self) -> float:
        """Get the current target hotend temperature."""
        return self._target_hotend_temperature

    @property
    def target_bed_temperature(self) -> float:
        """Get the current target bed temperature."""
        return self._target_bed_temperature

    @property
    def target_chamber_temperature(self) -> float:
        """Get the current target chamber temperature."""
        return self._target_chamber_temperature

    def get_parameter(self, name: str) -> Any:
        """Current value of a move parameter by name"""
        return self._current_params.get(name)

    def get_bounds(self, name: str) -> Any:
        """Current user defined bounds for a property"""
        return self._user_bounds.get_bounds(name)

    # pylint: disable=redefined-builtin
    def _set_bounds(self, name: str, min: Bound, max: Bound) -> None:
        """Set the bounds for a property."""

        self._user_bounds.set_bounds(name, min, max)

    @typechecked
    def _set_axes(self, axes: Point) -> None:
        """Set the current axes position."""

        self._user_bounds.validate("axes", axes)
        self._current_axes = axes

    @typechecked
    def _set_params(self, params: ParamsDict) -> None:
        """Set the current parameters dictionary."""

        self._current_params = params

    @typechecked
    def _set_length_units(self, length_units: LengthUnits) -> None:
        """Set the length measurement unit system.

        Args:
            length_units (LengthUnits): The unit system to use.
        """

        self._current_length_units = length_units

    @typechecked
    def _set_time_units(self, time_units: TimeUnits) -> None:
        """Set the time measurement unit system.

        Args:
            time_units (TimeUnits): The unit system to use.
        """

        self._current_time_units = time_units

    @typechecked
    def _set_temperature_units(self, temp_units: TemperatureUnits) -> None:
        """Set the temperature measurement unit system.

        Args:
            temp_units (TemperatureUnits): The unit system to use.
        """

        self._current_temperature_units = temp_units

    @typechecked
    def _set_plane(self, plane: Plane) -> None:
        """Set the working plane for circular movements.

        Args:
            plane (Plane): The plane to use.
        """

        self._current_plane = plane

    @typechecked
    def _set_direction(self, direction: Direction) -> None:
        """Set the rotation direction for interpolated moves.

        Args:
            direction (Direction): Rotation direction to use.
        """

        self._current_direction = direction


    @typechecked
    def _set_resolution(self, resolution: float) -> None:
        """Set the resolution for interpolated moves.

        Args:
            resolution (float): The resolution to use.

        Raises:
            ValueError: If resolution is non-positive.
        """

        if resolution <= 0:
            raise ValueError("Resolution must be positive")

        self._current_resolution = resolution

    @typechecked
    def _set_feed_rate(self, speed: float) -> None:
        """Set the feed rate for subsequent commands.

        Args:
            speed (float): The speed to set (must be >= 0).

        Raises:
            ValueError: If speed is negative or not a number.
        """

        self._validate_feed_rate(speed)
        self._current_feed_rate = speed

    @typechecked
    def _set_tool_power(self, power: float) -> None:
        """Set the current tool power level.

        Args:
            power (float): The power level to set (must be >= 0).

        Raises:
            ValueError: If power is negative or not a number.
        """

        self._validate_tool_power(power)
        self._current_tool_power = power

    @typechecked
    def _set_distance_mode(self, mode: DistanceMode) -> None:
        """Set the coordinate input mode for position commands.

        Args:
            mode (DistanceMode): The distance mode to use
        """

        self._current_distance_mode = mode

    @typechecked
    def _set_extrusion_mode(self, mode: ExtrusionMode) -> None:
        """Set the coordinate input mode for extrusion.

        Args:
            mode (ExtrusionMode): The extrusion mode to use
        """

        self._current_extrusion_mode = mode

    @typechecked
    def _set_feed_mode(self, mode: FeedMode) -> None:
        """Set the feed rate interpretation mode.

        Args:
            mode (FeedMode): The feed mode to use.
        """

        self._current_feed_mode = mode

    @typechecked
    def _set_coolant_mode(self, mode: CoolantMode) -> None:
        """Set the current coolant mode.

        Args:
            mode (CoolantMode): The coolant mode to set.

        Raises:
            CoolantStateError: If attempting to change mode while
                coolant is active.
        """

        if mode != CoolantMode.OFF:
            self._ensure_coolant_is_inactive("Coolant already active.")

        self._is_coolant_active = mode != CoolantMode.OFF
        self._current_coolant_mode = mode

    @typechecked
    def _set_spin_mode(self, mode: SpinMode, speed: float = 0) -> None:
        """Set the current tool spin mode and speed.

        Args:
            mode (SpinMode): The spin mode to set.
            speed (float): The spindle speed (must be >= 0).

        Raises:
            ValueError: If speed is negative or not a number.
            ToolStateError: If attempting to change mode while
                the spindle is active.
        """

        if mode != SpinMode.OFF:
            self._ensure_tool_is_inactive("Spindle already active.")

        self._set_tool_power(speed)
        self._is_tool_active = (mode != SpinMode.OFF)
        self._current_spin_mode = mode

    @typechecked
    def _set_power_mode(self, mode: PowerMode, power: float = 0) -> None:
        """Set the current tool power mode and level.

        Args:
            mode (PowerMode): The power mode to set.
            power (float): The power level (must be >= 0).

        Raises:
            ValueError: If power is negative or not a number.
            ToolStateError: If attempting to change mode while tool
                power is active.
        """

        if mode != PowerMode.OFF:
            self._ensure_tool_is_inactive("Power already active.")

        self._set_tool_power(power)
        self._is_tool_active = (mode != PowerMode.OFF)
        self._current_power_mode = mode

    @typechecked
    def _set_tool_number(self, mode: ToolSwapMode, tool_number: int) -> None:
        """Set the current tool number and swap mode.

        Args:
            mode (ToolSwapMode): The tool swap mode to set.
            tool_number (int): The tool number to select.

        Raises:
            ValueError: If tool_number is less than 1.
            ToolStateError: If attempting to set the tool while the
                tool is active.
            CoolantStateError: If attempting to set the tool while
                coolant is active.
        """

        self._validate_tool_number(tool_number)
        self._ensure_tool_is_inactive("Tool change with tool on.")
        self._ensure_coolant_is_inactive("Tool change with coolant on.")
        self._current_tool_number = tool_number
        self._current_tool_swap_mode = mode

    @typechecked
    def _set_halt_mode(self, mode: HaltMode) -> None:
        """Set the current halt mode.

        Args:
            mode (HaltMode): The halt mode to set.

        Raises:
            ToolStateError: If attempting to halt while a tool is active.
            CoolantStateError: If attempting to halt while coolant is active.
        """

        if mode != HaltMode.OFF:
            self._ensure_tool_is_inactive("Halt with tool on.")
            self._ensure_coolant_is_inactive("Halt with coolant on.")

        self._current_halt_mode = mode

    @typechecked
    def _set_target_hotend_temperature(self, temperature: float) -> None:
        """Set the target hotend temperature.

        Args:
            temperature (float): The target temperature to set.
        """

        self._user_bounds.validate("hotend-temperature", temperature)
        self._target_hotend_temperature = temperature

    @typechecked
    def _set_target_bed_temperature(self, temperature: float) -> None:
        """Set the target bed temperature.

        Args:
            temperature (float): The target temperature to set.
        """

        self._user_bounds.validate("bed-temperature", temperature)
        self._target_bed_temperature = temperature

    @typechecked
    def _set_target_chamber_temperature(self, temperature: float) -> None:
        """Set the target chamber temperature.

        Args:
            temperature (float): The target temperature to set.
        """

        self._user_bounds.validate("chamber-temperature", temperature)
        self._target_chamber_temperature = temperature

    def _ensure_tool_is_inactive(self, message: str) -> None:
        """Raise an exception if tool is active."""

        if self._is_tool_active:
            raise ToolStateError(message)

    def _ensure_coolant_is_inactive(self, message: str) -> None:
        """Raise an exception if coolant is active."""

        if self._is_coolant_active:
            raise CoolantStateError(message)

    def _validate_tool_number(self, number: int) -> None:
        """Validate tool number is within acceptable range."""

        self._user_bounds.validate("tool-number", number)

        if not isinstance(number, int) or number < 1:
            message = f"Invalid tool number '{number}'."
            raise ValueError(message)

    def _validate_feed_rate(self, speed: float) -> None:
        """Validate feed rate is within acceptable range."""

        self._user_bounds.validate("feed-rate", speed)

        if not isinstance(speed, int | float) or speed < 0.0:
            message = f"Invalid feed rate '{speed}'."
            raise ValueError(message)

    def _validate_tool_power(self, power: float) -> None:
        """Validate tool power level is within acceptable range."""

        self._user_bounds.validate("tool-power", power)

        if not isinstance(power, int | float) or power < 0.0:
            message = f"Invalid tool power '{power}'."
            raise ValueError(message)
