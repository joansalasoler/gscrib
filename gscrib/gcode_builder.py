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

import math
from typing import Callable
from contextlib import contextmanager
from typeguard import typechecked

from .codes import gcode_table
from .gcode_core import GCodeCore
from .gcode_state import GState
from .params import ParamsDict
from .geometry import Point, PointLike, PathTracer
from .enums import *


class GCodeBuilder(GCodeCore):
    """G-code generator with complete machine control capabilities.

    This class provides comprehensive control over CNC machines and
    similar devices. It extends GCodeCore to provide a complete machine
    control solution with state tracking, path interpolation, temperature
    management, parameter processing, and other advanced features.

    See GCodeCore for basic G-code generation and configuration options.

    Key features:

    - Machine state tracking and validation
    - Coordinate system transformations
    - Unit and coordinate system management
    - Tool control (spindle, laser, etc.)
    - Temperature and cooling management
    - Basic movement commands
    - Path interpolation (arcs, splines, helixes, etc.)
    - Emergency stop procedures
    - Multiple output capabilities
    - Move hooks for custom parameter processing

    The machine state is tracked by the `state` manager, which maintains
    and validates the state of various machine subsystems to prevent
    invalid operations and ensure proper command sequencing.

    The `trace` property provides access to advanced path interpolation
    capabilities, allowing generation of complex toolpaths like circular
    arcs, helixes or splines.

    Move hooks can be registered to process and modify movement commands
    before they are written. Each hook receives the origin and target
    points, along with current machine state, allowing for:

    - Parameter validation and modification
    - Feed rate limiting or scaling
    - Automatic parameter calculations
    - State-based parameter adjustments
    - Safety checks and constraints

    Example:
        >>> with GCodeMachine(output="outfile.gcode") as g:
        >>>     g.rapid_absolute(x=0.0, y=0.0, z=5.0)
        >>>     g.tool_on(CLOCKWISE, 1000)
        >>>     g.move(z=0.0, F=500)
        >>>     g.move(x=10.0, y=10.0, F=1500)
        >>>
        >>> # Example using a custom hook to extrude filament
        >>> def extrude_hook(origin, target, params, state):
        >>>     dt = target - origin
        >>>     length = math.hypot(dt.x, dt.y, dt.z)
        >>>     params.update(E=0.1 * length)
        >>>     return params
        >>>
        >>> with g.move_hook(extrude_hook):
        >>>     g.move(x=10, y=0)   # Will add E=1.0
        >>>     g.move(x=20, y=10)  # Will add E=1.414
        >>>     g.move(x=10, y=10)  # Will add E=1.0
    """

    __slots__ = (
        "_state",
        "_tracer",
        "_hooks",
    )

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._state: GState = GState()
        self._tracer: PathTracer = PathTracer(self)
        self._hooks = []

    @property
    def state(self) -> GState:
        """Current machine state."""

        return self._state

    @property
    def trace(self) -> PathTracer:
        """Interpolated path generation"""

        return self._tracer

    @typechecked
    def add_hook(self, hook: Callable) -> None:
        """Add a permanent move parameter hook.

        Hooks are called before each move to process and modify movement
        parameters. Each hook receives these arguments:

        - origin (Point): Absolute coordinates of the origin point
        - target (Point): Absolute coordinates of the destination point
        - params (MoveParams): Object containing movement parameters
        - state (GState): Current machine state

        Args:
            hook: Callable that processes movement parameters

        Example:
            >>> def limit_feed(origin, target, params, state):
            >>>     params.update(F=min(params.get('F'), 1000)
            >>>     return params
            >>>
            >>> g.add_hook(limit_feed)
        """

        if hook not in self._hooks:
            self._hooks.append(hook)

    @typechecked
    def remove_hook(self, hook: Callable) -> None:
        """Remove a previously added move parameter hook.

        Args:
            hook: Callable to remove

        Example:
            >>> g.remove_hook(limit_feed)
        """

        if hook in self._hooks:
            self._hooks.remove(hook)

    @typechecked
    def set_length_units(self, length_units: LengthUnits | str) -> None:
        """Set the unit system for subsequent commands.

        Args:
            length_units (LengthUnits): The unit system to use

        Raises:
            ValueError: If length units is not valid

        >>> G20|G21
        """

        length_units = LengthUnits(length_units)

        if length_units != self.state.length_units:
            in_px = length_units.to_pixels(self.state.resolution)
            self.set_resolution(length_units.scale(in_px))
            self.state._set_length_units(length_units)

        statement = self._get_statement(length_units)
        self.write(statement)

    @typechecked
    def set_time_units(self, time_units: TimeUnits | str) -> None:
        """Set the time units for subsequent commands.

        Args:
            time_units (TimeUnits): Time units (seconds/milliseconds)

        Raises:
            ValueError: If time units is not valid
        """

        time_units = TimeUnits(time_units)
        self.state._set_time_units(time_units)

    @typechecked
    def set_temperature_units(self, temp_units: TemperatureUnits | str) -> None:
        """Set the temperature units for subsequent commands.

        Args:
            temp_units (TemperatureUnits): Temperature units

        Raises:
            ValueError: If temperature units is not valid
        """

        temp_units = TemperatureUnits(temp_units)
        self.state._set_temperature_units(temp_units)

    @typechecked
    def set_plane(self, plane: Plane | str) -> None:
        """Select the working plane for machine operations.

        Args:
            plane (Plane): The plane to use for subsequent operations

        Raises:
            ValueError: If plane is not valid

        >>> G17|G18|G19
        """

        plane = Plane(plane)
        self.state._set_plane(plane)
        statement = self._get_statement(plane)
        self.write(statement)

    @typechecked
    def set_direction(self, direction: Direction | str) -> None:
        """Set the rotation direction for interpolated moves.

        Args:
            direction: Clockwise or counter-clockwise rotation

        Raises:
            ValueError: If rotation direction is not valid
        """

        direction = Direction(direction)
        self.state._set_direction(direction)

    @typechecked
    def set_resolution(self, resolution: float) -> None:
        """Set the resolution for interpolated moves.

        Controls the accuracy of path approximation by specifying the
        minimum length of linear segments used to trace the path.

        Args:
            resolution (float): Length in current work units

        ValueError:
            If the resolution is non-positive.
        """

        self.state._set_resolution(resolution)

    @typechecked
    def set_distance_mode(self, mode: DistanceMode | str) -> None:
        """Set the positioning mode for subsequent commands.

        Args:
            mode (DistanceMode): The distance mode to use

        Raises:
            ValueError: If distance mode is not valid

        >>> G90|G91
        """

        mode = DistanceMode(mode)
        self._distance_mode = mode
        self.state._set_distance_mode(mode)
        statement = self._get_statement(mode)
        self.write(statement)

    @typechecked
    def set_extrusion_mode(self, mode: ExtrusionMode | str) -> None:
        """Set the extrusion mode for subsequent commands.

        Args:
            mode (ExtrusionMode): The extrusion mode to use

        Raises:
            ValueError: If extrusion mode is not valid

        >>> M82|M83
        """

        mode = ExtrusionMode(mode)
        self.state._set_extrusion_mode(mode)
        statement = self._get_statement(mode)
        self.write(statement)

    @typechecked
    def set_feed_mode(self, mode: FeedMode | str) -> None:
        """Set the feed rate mode for subsequent commands.

        Args:
            mode (FeedMode): The feed rate mode to use

        Raises:
            ValueError: If feed mode is not valid

        >>> G93|G94|G95
        """

        mode = FeedMode(mode)
        self.state._set_feed_mode(mode)
        statement = self._get_statement(mode)
        self.write(statement)

    @typechecked
    def set_tool_power(self, power: float) -> None:
        """Set the power level for the current tool.

        The power parameter represents tool-specific values that vary
        by machine type, such as:

        - Spindle rotation speed in RPM
        - Laser power output (typically 0-100%)
        - Other similar power settings

        Args:
            power (float): Power level for the tool (must be >= 0.0)

        Raises:
            ValueError: If power is less than 0.0

        >>> S<power>
        """

        self.state._set_tool_power(power)
        statement = self.format.parameters({ "S": power })
        self.write(statement)

    @typechecked
    def set_fan_speed(self, speed: float, fan_number: int = 0) -> None:
        """Set the speed of the main fan.

        Args:
            speed (int): Fan speed (must be >= 0 and <= 255)
            fan_number (float): Fan number (must be >= 0)

        Raises:
            ValueError: If speed is not in the valid range

        >>> M106 P<fan_number> S<speed>
        """

        if fan_number < 0:
            raise ValueError(f"Invalid fan number '{fan_number}'.")

        if speed < 0 or speed > 255:
            raise ValueError(f"Invalid fan speed '{speed}'.")

        params = { "P": fan_number, "S": speed }
        mode = FanMode.COOLING if speed > 0 else FanMode.OFF
        statement = self._get_statement(mode, params)
        self.write(statement)

    @typechecked
    def set_bed_temperature(self, temperature: int) -> None:
        """Set the temperature of the bed and return immediately.

        Different machine controllers interpret the S parameter in M140
        differently. Use the method `set_temperature_units()` to set the
        correct temperature units for your specific controller.

        Args:
            temperature (float): Target temperature

        >>> M140 S<temperature>
        """

        units = self.state.temperature_units
        bed_units = BedTemperature.from_units(units)
        statement = self._get_statement(bed_units, { "S": temperature })
        self.write(statement)

    @typechecked
    def set_hotend_temperature(self, temperature: int) -> None:
        """Set the temperature of the hotend and return immediately.

        Different machine controllers interpret the S parameter in M104
        differently. Use the method `set_temperature_units()` to set the
        correct temperature units for your specific controller.

        Args:
            temperature (float): Target temperature

        >>> M104 S<temperature>
        """

        units = self.state.temperature_units
        hotend_units = HotendTemperature.from_units(units)
        statement = self._get_statement(hotend_units, { "S": temperature })
        self.write(statement)

    @typechecked
    def set_chamber_temperature(self, temperature: int) -> None:
        """Set the temperature of the chamber and return immediately.

        Different machine controllers interpret the S parameter in M141
        differently. Use the method `set_temperature_units()` to set the
        correct temperature units for your specific controller.

        Args:
            temperature (float): Target temperature

        >>> M141 S<temperature>
        """

        units = self.state.temperature_units
        chamber_units = ChamberTemperature.from_units(units)
        statement = self._get_statement(chamber_units, { "S": temperature })
        self.write(statement)

    def set_axis(self, point: PointLike = None, **kwargs) -> None:
        """Set the current position without moving the head.

        This command changes the machine's coordinate system by setting
        the current position to the specified values without any physical
        movement. It's commonly used to set a new reference point or to
        reset axis positions.

        Args:
            point (optional): New axis position as a point
            x (float, optional): New X-axis position value
            y (float, optional): New Y-axis position value
            z (float, optional): New Z-axis position value
            comment (str, optional): Optional comment to add
            **kwargs: Additional axis positions

        >>> G92 [X<x>] [Y<y>] [Z<z>] [<axis><value> ...]
        """

        mode = PositioningMode.OFFSET
        point, params, comment = self._process_move_params(point, **kwargs)
        target_axes = self._current_axes.replace(*point)
        statement = self._get_statement(mode, params, comment)

        self._update_axes(target_axes, params)
        self.write(statement)

    @typechecked
    def sleep(self, duration: float) -> None:
        """Pause program execution for the specified duration.

        Generates a dwell command that pauses program execution.
        Different machine controllers interpret the P parameter in G4
        differently. Use the method `set_time_units()` to set the
        correct time units for your specific controller.

        Args:
            duration (float): Sleep duration in time units

        Raises:
            ValueError: If duration is less than 1 ms

        >>> G4 P<seconds|milliseconds>
        """

        units = self.state.time_units

        if units == TimeUnits.SECONDS and duration < 0.001:
            raise ValueError(f"Invalid sleep time '{duration}'.")

        if units == TimeUnits.MILLISECONDS and duration < 1:
            raise ValueError(f"Invalid sleep time '{duration}'.")

        statement = self._get_statement(units, { "P": duration })
        self.write(statement)

    @typechecked
    def tool_on(self, mode: SpinMode | str, speed: float) -> None:
        """Activate the tool with specified direction and speed.

        The speed parameter represents tool-specific values that vary
        by machine type, such as:

        - Spindle rotation speed in RPM

        Args:
            mode (SpinMode): Direction of tool rotation (CW/CCW)
            speed (float): Speed for the tool (must be >= 0.0)

        Raises:
            ValueError: If speed is less than 0.0
            ValueError: If mode is OFF or was already active
            ToolStateError: If attempting invalid mode transition

        >>> S<speed> M3|M4
        """

        if mode == SpinMode.OFF:
            raise ValueError("Not a valid spin mode.")

        mode = SpinMode(mode)
        self.state._set_spin_mode(mode, speed)
        params = self.format.parameters({ "S": speed })
        mode_statement = self._get_statement(mode)
        statement = f"{params} {mode_statement}"
        self.write(statement)

    def tool_off(self) -> None:
        """Deactivate the current tool.

        >>> M5
        """

        self.state._set_spin_mode(SpinMode.OFF)
        statement = self._get_statement(SpinMode.OFF)
        self.write(statement)

    @typechecked
    def power_on(self, mode: PowerMode | str, power: float) -> None:
        """Activate the tool with specified mode and power.

        The power parameter represents tool-specific values that vary
        by machine type, such as:

        - Laser power output (typically 0-100%)
        - Other similar power settings

        Args:
            mode (PowerMode): Power mode of the tool
            power (float): Power level for the tool (must be >= 0.0)

        Raises:
            ValueError: If power is less than 0.0
            ValueError: If mode is OFF or was already active
            ToolStateError: If attempting invalid mode transition

        >>> S<power> M3|M4
        """

        if mode == PowerMode.OFF:
            raise ValueError(f"Not a valid power mode: {mode}.")

        mode = PowerMode(mode)
        self.state._set_power_mode(mode, power)
        params = self.format.parameters({ "S": power })
        mode_statement = self._get_statement(mode)
        statement = f"{params} {mode_statement}"
        self.write(statement)

    def power_off(self) -> None:
        """Power off the current tool.

        >>> M5
        """

        self.state._set_power_mode(PowerMode.OFF)
        statement = self._get_statement(PowerMode.OFF)
        self.write(statement)

    @typechecked
    def tool_change(self, mode: ToolSwapMode | str, tool_number: int) -> None:
        """Execute a tool change operation.

        Performs a tool change sequence, ensuring proper safety
        conditions are met before proceeding.

        Args:
            mode (ToolChangeMode): Tool change mode to execute
            tool_number (int): Tool number to select (must be positive)

        Raises:
            ValueError: If tool number is invalid or mode is OFF
            ToolStateError: If tool is currently active
            CoolantStateError: If coolant is currently active

        >>> T<tool_number> M6
        """

        if mode == ToolSwapMode.OFF:
            raise ValueError(f"Not a valid tool swap mode: {mode}.")

        mode = ToolSwapMode(mode)
        self.state._set_tool_number(mode, tool_number)
        change_statement = self._get_statement(mode)
        tool_digits = 2 ** math.ceil(math.log2(len(str(tool_number))))
        statement = f"T{tool_number:0{tool_digits}} {change_statement}"
        self.write(statement)

    @typechecked
    def coolant_on(self, mode: CoolantMode | str) -> None:
        """Activate coolant system with the specified mode.

        Args:
            mode (CoolantMode): Coolant operation mode to activate

        Raises:
            ValueError: If mode is OFF or was already active

        >>> M7|M8
        """

        if mode == CoolantMode.OFF:
            raise ValueError(f"Not a valid coolant mode: {mode}.")

        mode = CoolantMode(mode)
        self.state._set_coolant_mode(mode)
        statement = self._get_statement(mode)
        self.write(statement)

    def coolant_off(self) -> None:
        """Deactivate coolant system.

        >>> M9
        """

        self.state._set_coolant_mode(CoolantMode.OFF)
        statement = self._get_statement(CoolantMode.OFF)
        self.write(statement)

    @typechecked
    def halt(self, mode: HaltMode, **kwargs) -> None:
        """Pause or stop program execution.

        Args:
            mode (HaltMode): Type of halt to perform
            **kwargs: Arbitrary command parameters

        Raises:
            ToolStateError: If attempting to halt with tool active
            CoolantStateError: If attempting to halt with coolant active

        >>> M0|M1|M2|M30|M60|M109|M190|M191 [<param><value> ...]
        """

        if mode == HaltMode.OFF:
            raise ValueError(f"Not a valid halt mode: {mode}.")

        mode = HaltMode(mode)
        self.state._set_halt_mode(mode)
        statement = self._get_statement(mode, kwargs)
        self.write(statement)

    @typechecked
    def pause(self, optional: bool = False) -> None:
        """Pause program execution.

        Invokes `halt(HaltMode.OPTIONAL_PAUSE)` if optional is
        True, otherwise `halt(HaltMode.PAUSE)`.

        Args:
            optional (bool): If True, pause is optional
        """

        self.halt(
            HaltMode.OPTIONAL_PAUSE
            if optional is True else
            HaltMode.PAUSE
        )

    @typechecked
    def stop(self, reset: bool = False) -> None:
        """Stop program execution.

        Invokes `halt(HaltMode.END_WITH_RESET)` if reset is
        True, otherwise `halt(HaltMode.END_WITHOUT_RESET)`.

        Args:
            reset (bool): If True, reset the machine
        """

        self.halt(
            HaltMode.END_WITH_RESET
            if reset is True else
            HaltMode.END_WITHOUT_RESET
        )

    @typechecked
    def emergency_halt(self, message: str) -> None:
        """Execute an emergency shutdown sequence and pause execution.

        Performs a complete safety shutdown sequence in this order:

        1. Deactivates all active tools (spindle, laser, etc.)
        2. Turns off all coolant systems
        3. Adds a comment with the emergency message
        4. Halts program execution with a mandatory pause

        This method ensures safe machine state in emergency situations.
        The program cannot resume until manually cleared.

        Args:
            message (str): Description of the emergency condition

        >>> M05
        >>> M09
        >>> ; Emergency halt: <message>
        >>> M00
        """

        self.tool_off()
        self.coolant_off()
        self.comment(f"Emergency halt: {message}")
        self.halt(HaltMode.PAUSE)

    def write(self, statement: str) -> None:
        """Write a raw G-code statement to all configured writers.

        Direct use of this method is discouraged as it bypasses all state
        management. Using this method may lead to inconsistencies between
        the internal state tracking and the actual machine state. Instead,
        use the dedicated methods like move(), tool_on(), etc., which
        properly maintain state and ensure safe operation.

        Args:
            statement: The raw G-code statement to write

        Raises:
            DeviceError: If writing to any output fails

        Example:
            >>> g = GCodeCore()
            >>> g.write("G1 X10 Y20") # Bypasses state tracking
            >>> g.move(x=10, y=20) # Proper state management
        """

        self.state._set_halt_mode(HaltMode.OFF)
        super().write(statement)

    @contextmanager
    def move_hook(self, hook: Callable):
        """Temporarily enable a move parameter hook.

        Args:
            hook: Callable that processes movement parameters

        Example:
            >>> with g.move_hook(extrude_hook):  # Adds a hook
            >>>     g.move(x=10, y=0)  # Will add E=1.0
            >>> # Hook is removed automatically here
        """

        self.add_hook(hook)

        try:
            yield
        finally:
            self.remove_hook(hook)

    def _write_move(self,
        point: Point, params: ParamsDict, comment: str | None = None) -> ParamsDict:
        """Write a linear move statement with the given parameters.

        Applies all registered move hooks before writing the movement
        command. Each hook can modify the parameters based on the
        movement and current machine state.

        Args:
            point: Target position for the move
            params: Movement parameters (feed rate, etc.)
            comment: Optional comment to include
        """

        if len(self._hooks) > 0:
            origin = self.position.resolve()
            target = self.to_absolute(point)

            for hook in self._hooks:
                params = hook(origin, target, params, self.state)

        return super()._write_move(point, params, comment)

    def _update_axes(self, axes: Point, params: ParamsDict) -> None:
        """Update the internal state after a movement.

        Updates the current position and movement parameters to reflect
        the new machine state after executing a move command.

        Args:
            axes: The new position of all axes
            params: The movement parameters used in the command
        """

        super()._update_axes(axes, params)
        self.state._set_params(self._current_params)
        self.state._set_axes(self._current_axes)

    def _get_statement(self,
        value: BaseEnum, params: dict = {}, comment: str | None = None)-> str:
        """Generate a G-code statement from the codes table."""

        entry = gcode_table.get_entry(value)
        command = self.format.command(entry.instruction, params)
        comment = self.format.comment(comment or entry.description)

        return f"{command} {comment}"
