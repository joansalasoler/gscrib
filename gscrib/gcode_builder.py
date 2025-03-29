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
from .move_params import MoveParams
from .point import Point, PointLike
from .trace_path import TracePath
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
    - Path interpolation (arcs, splines, helixes)
    - Emergency stop procedures
    - Multiple output capabilities
    - Move handlers for custom parameter processing

    The machine state is tracked by the `state` manager, which maintains
    and validates the state of various machine subsystems to prevent
    invalid operations and ensure proper command sequencing.

    The `trace` property provides access to advanced path interpolation
    capabilities, allowing generation of complex toolpaths like circular
    arcs, helixes or splines.

    Move handlers can be registered to process and modify movement
    commands before they are written. Each handler receives the origin
    and target points, along with current machine state, allowing for:

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
        >>> # Example using a custom handler to extrude filament
        >>> def extrude_handler(origin, target, params, state):
        >>>     dt = target - origin
        >>>     length = math.hypot(dt.x, dt.y, dt.z)
        >>>     params.update(E=0.1 * length)
        >>>     return params
        >>>
        >>> with g.handler(extrude_handler):
        >>>     g.move(x=10, y=0)   # Will add E=1.0
        >>>     g.move(x=20, y=10)  # Will add E=1.414
        >>>     g.move(x=10, y=10)  # Will add E=1.0
    """

    __slots__ = (
        "_state",
        "_tracer",
        "_handlers",
    )

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._state: GState = GState()
        self._tracer: TracePath = TracePath(self)
        self._handlers = []

    @property
    def state(self) -> GState:
        """Current machine state."""

        return self._state

    @property
    def trace(self) -> TracePath:
        """Interpolated path generation"""

        return self._tracer

    @typechecked
    def add_handler(self, handler: Callable) -> None:
        """Add a permanent move parameter handler.

        Handlers are called before each move to process and modify
        movement parameters. Each handler receives these arguments:

        - origin (Point): Absolute coordinates of the origin point
        - target (Point): Absolute coordinates of the destination point
        - params (MoveParams): Object containing movement parameters
        - state (GState): Current machine state

        Args:
            handler: Callable that processes movement parameters

        Example:
            >>> def limit_feed(origin, target, params, state):
            >>>     params.update(F=min(params.get('F'), 1000)
            >>>     return params
            >>>
            >>> g.add_handler(limit_feed)
        """

        if handler not in self._handlers:
            self._handlers.append(handler)

    @typechecked
    def remove_handler(self, handler: Callable) -> None:
        """Remove a previously added move parameter handler.

        Args:
            handler: Handler callable to remove

        Example:
            >>> g.remove_handler(limit_feed)
        """

        if handler in self._handlers:
            self._handlers.remove(handler)

    @typechecked
    def select_units(self, length_units: LengthUnits | str) -> None:
        """Set the unit system for subsequent commands.

        Args:
            length_units (LengthUnits): The unit system to use

        >>> G20|G21
        """

        length_units = LengthUnits(length_units)
        self._state._set_length_units(length_units)
        self._tracer._set_length_units(length_units)
        statement = self._get_statement(length_units)
        self.write(statement)

    @typechecked
    def select_plane(self, plane: Plane | str) -> None:
        """Select the working plane for machine operations.

        Args:
            plane (Plane): The plane to use for subsequent operations

        >>> G17|G18|G19
        """

        plane = Plane(plane)
        self._state._set_plane(plane)
        statement = self._get_statement(plane)
        self.write(statement)

    @typechecked
    def set_distance_mode(self, mode: DistanceMode | str) -> None:
        """Set the positioning mode for subsequent commands.

        Args:
            mode (DistanceMode): The distance mode to use

        >>> G90|G91
        """

        mode = DistanceMode(mode)
        self._distance_mode = mode
        self._state._set_distance_mode(mode)
        statement = self._get_statement(mode)
        self.write(statement)

    @typechecked
    def set_extrusion_mode(self, mode: ExtrusionMode | str) -> None:
        """Set the extrusion mode for subsequent commands.

        Args:
            mode (ExtrusionMode): The extrusion mode to use

        >>> M82|M83
        """

        mode = ExtrusionMode(mode)
        self._state._set_extrusion_mode(mode)
        statement = self._get_statement(mode)
        self.write(statement)

    @typechecked
    def set_feed_mode(self, mode: FeedMode | str) -> None:
        """Set the feed rate mode for subsequent commands.

        Args:
            mode (FeedMode): The feed rate mode to use

        >>> G93|G94|G95
        """

        mode = FeedMode(mode)
        self._state._set_feed_mode(mode)
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

        self._state._set_tool_power(power)
        statement = self.format.parameters({ "S": power })
        self.write(statement)

    @typechecked
    def set_fan_speed(self, speed: int, fan_number: int = 0) -> None:
        """Set the speed of the main fan.

        Args:
            speed (int): Fan speed (must be >= 0 and <= 255)
            fan_number (int): Fan number (must be >= 0)

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
    def set_bed_temperature(self,
        units: TemperatureUnits | str, temp: int) -> None:
        """Set the temperature of the bed and return immediately.

        Args:
            units (TemperatureUnits): Temperature units
            temp (float): Target temperature

        >>> M140 S<temp>
        """

        units = TemperatureUnits(units)
        bed_units = BedTemperature.from_units(units)
        statement = self._get_statement(bed_units, { "S": temp })
        self.write(statement)

    @typechecked
    def set_hotend_temperature(self,
        units: TemperatureUnits | str, temp: int) -> None:
        """Set the temperature of the hotend and return immediately.

        Args:
            units (TemperatureUnits): Temperature units
            temp (float): Target temperature

        >>> M104 S<temp>
        """

        units = TemperatureUnits(units)
        hotend_units = HotendTemperature.from_units(units)
        statement = self._get_statement(hotend_units, { "S": temp })
        self.write(statement)

    def set_axis_position(self, point: PointLike = None, **kwargs) -> None:
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
    def sleep(self, units: TimeUnits | str, seconds: float) -> None:
        """Pause program execution for the specified duration.

        Generates a dwell command that pauses program execution. While
        the input is always in seconds, different machine controllers
        interpret the P parameter in G4 differently; some expect seconds,
        others milliseconds. The `units` parameter allows generating the
        correct format for your specific controller:

        - TimeUnits.SECONDS: Output as seconds
        - TimeUnits.MILLISECONDS: Output as milliseconds

        Args:
            units (TimeUnits): Time unit (seconds/milliseconds)
            seconds (float): Sleep duration (minimum 1ms)

        Raises:
            ValueError: If seconds is less than 0.001

        >>> G4 P<seconds|milliseconds>
        """

        if seconds < 0.001:
            raise ValueError(f"Invalid sleep time '{seconds}'.")

        units = TimeUnits(units)
        params = { "P": units.scale(seconds) }
        statement = self._get_statement(units, params)
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
        self._state._set_spin_mode(mode, speed)
        params = self.format.parameters({ "S": speed })
        mode_statement = self._get_statement(mode)
        statement = f"{params} {mode_statement}"
        self.write(statement)

    def tool_off(self) -> None:
        """Deactivate the current tool.

        >>> M5
        """

        self._state._set_spin_mode(SpinMode.OFF)
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
            raise ValueError("Not a valid power mode.")

        mode = PowerMode(mode)
        self._state._set_power_mode(mode, power)
        params = self.format.parameters({ "S": power })
        mode_statement = self._get_statement(mode)
        statement = f"{params} {mode_statement}"
        self.write(statement)

    def power_off(self) -> None:
        """Power off the current tool.

        >>> M5
        """

        self._state._set_power_mode(PowerMode.OFF)
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

        mode = ToolSwapMode(mode)
        self._state._set_tool_number(mode, tool_number)
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
            raise ValueError("Not a valid coolant mode.")

        mode = CoolantMode(mode)
        self._state._set_coolant_mode(mode)
        statement = self._get_statement(mode)
        self.write(statement)

    def coolant_off(self) -> None:
        """Deactivate coolant system.

        >>> M9
        """

        self._state._set_coolant_mode(CoolantMode.OFF)
        statement = self._get_statement(CoolantMode.OFF)
        self.write(statement)

    @typechecked
    def halt_program(self, mode: HaltMode, **kwargs) -> None:
        """Pause or stop program execution.

        Args:
            mode (HaltMode): Type of halt to perform
            **kwargs: Arbitrary command parameters

        Raises:
            ToolStateError: If attempting to halt with tool active
            CoolantStateError: If attempting to halt with coolant active

        >>> M0|M1|M2|M30|M60|M109|M190 [<param><value> ...]
        """

        if mode == HaltMode.OFF:
            raise ValueError("Not a valid halt mode.")

        mode = HaltMode(mode)
        self._state._set_halt_mode(mode)
        statement = self._get_statement(mode, kwargs)
        self.write(statement)

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
        self.halt_program(HaltMode.PAUSE)

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

        self._state._set_halt_mode(HaltMode.OFF)
        super().write(statement)

    @contextmanager
    def handler(self, handler: Callable):
        """Temporarily enable a move parameter handler.

        Args:
            handler: Callable that processes movement parameters

        Example:
            >>> with g.handler(extrude_handler):  # Adds a handler
            >>>     g.move(x=10, y=0)  # Will add E=1.0
            >>> # Handler is removed automatically here
        """

        try:
            self._handlers.append(handler)
            yield
        finally:
            self._handlers.remove(handler)

    def _write_move(self,
        point: Point, params: MoveParams, comment: str | None = None) -> MoveParams:
        """Write a linear move statement with the given parameters.

        Applies all registered move handlers before writing the movement
        command. Each handler can modify the parameters based on the
        movement and current machine state.

        Args:
            point: Target position for the move
            params: Movement parameters (feed rate, etc.)
            comment: Optional comment to include
        """

        if len(self._handlers) > 0:
            origin = self.position.resolve()
            target = self.to_absolute(point)

            for handler in self._handlers:
                params = handler(origin, target, params, self._state)

        return super()._write_move(point, params, comment)

    def _get_statement(self,
        value: BaseEnum, params: dict = {}, comment: str | None = None)-> str:
        """Generate a G-code statement from the codes table."""

        entry = gcode_table.get_entry(value)
        command = self.format.command(entry.instruction, params)
        comment = self.format.comment(comment or entry.description)

        return f"{command} {comment}"
