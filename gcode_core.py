# -*- coding: utf-8 -*-

# G-Code generator for Vpype.
# Copyright (C) 2025 Joan Sala <contact@joansala.com>
#
# This file contains code originally written by Jack Minardi, which is
# licensed under the MIT License. See the LICENSE-MIT file in this
# project's root directory for the full text of the original license.
#
# Modifications made by Joan Sala are licensed under the GNU GPL.
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

import sys, logging
from contextlib import contextmanager
from typing import Any, List, Sequence, Tuple, TypeAlias
from typeguard import typechecked

from .config import GConfig
from .enums import DistanceMode
from .excepts import DeviceError
from .formatters import BaseFormatter, DefaultFormatter
from .move_params import MoveParams
from .point import Point, PointLike
from .transformer import Transformer
from .writers import BaseWriter, SocketWriter, SerialWriter, FileWriter

ProcessedParams: TypeAlias = Tuple[Point, MoveParams, str | None]


class GCodeCore(object):
    """Core G-code generation functionality.

    This class provides the fundamental building blocks for G-code
    generation, including:

    - G-code formatting and output writing
    - Coordinate system transformations
    - Position tracking and distance mode management
    - Basic movement operations (linear and rapid moves)
    - Multiple output methods (file, serial, network socket)

    For general use, it is recommended to use the `GCodeBuilder` class
    instead, which extends `GCodeCore` with a more complete set of
    G-code commands and additional state management capabilities.

    The `teardown()` method must be called when done to properly close
    connections and clean up resources. Using the class as a context
    manager with 'with' automatically handles this.

    The current position of X, Y and Z axes is tracked by the `position`
    property. This property reflects the absolute position of all axes
    in the original coordinate system (without transforms).

    Transformations are limited to the X, Y, and Z axes. While you can
    include additional axes or parameters in move commands, only these
    three primary axes will transformed and tracked by the `position`
    property. All other custom parameters provided to the move methods
    can be retrieved using the `get_move_parameter()` method.

    This class constructor accepts the following configuration options:

    - output (str | TextIO | BinaryIO ):
        Path or file-like object where the generated G-Code will be
        saved. If not specified defaults to `stdout`.
    - print_lines (bool) [default: false]:
        Always print lines to `stdout`, even if an output file is
        specified.
    - direct_write (str | DirectWrite) [default: 'off']:
        Send G-code to machine ('off', 'socket' or 'serial').
    - host (str) [default: localhost]:
        Hostname/IP for network connection when using socket mode.
    - port (int) [default: 8000]:
        Port number for network/serial communication.
    - baudrate (int) [default: 250000]:
        Baud rate for serial connection.
    - decimal_places (str) [default: 5]:
        Maximum number of decimal places in numeric output.
    - comment_symbols (str) [default: ';']:
        Characters used to mark comments in G-code.
    - line_endings (str) [default: 'os']:
        Line ending characters (use 'os' for system default).
    - x_axis (str) [default: 'X']:
        Custom label for X axis in G-code output.
    - y_axis (str) [default: 'Y']:
        Custom label for Y axis in G-code output.
    - z_axis (str) [default: 'Z']:
        Custom label for Z axis in G-code output.

    Example:
        >>> with GCodeCore(output="outfile.gcode") as g:
        ...     g.set_distance_mode("absolute")
        ...     g.move(x=10, y=10)  # Linear move to (10, 10)
        ...     g.rapid(z=5)        # Rapid move up to Z=5
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize G-code generator with configuration.

        Args:
            **kwargs: Configuration parameters
        """

        config: GConfig = GConfig(**kwargs)

        self._logger = logging.getLogger(__name__)
        self._formatter = DefaultFormatter()
        self._transformer = Transformer()
        self._current_axes = Point.unknown()
        self._current_params = MoveParams()
        self._distance_mode = DistanceMode.ABSOLUTE
        self._writers: List[BaseWriter] = []
        self._initialize_formatter(config)
        self._initialize_writers(config)

    def _initialize_formatter(self, config: GConfig) -> None:
        """Initialize the G-code formatter."""

        self._formatter.set_decimal_places(config.decimal_places)
        self._formatter.set_comment_symbols(config.comment_symbols)
        self._formatter.set_line_endings(config.line_endings)
        self._formatter.set_axis_label("x", config.x_axis)
        self._formatter.set_axis_label("y", config.y_axis)
        self._formatter.set_axis_label("z", config.z_axis)

    def _initialize_writers(self, config: GConfig) -> None:
        """Initialize output writers."""

        if config.print_lines is True:
            writer = FileWriter(self._get_stdout_file())
            self._writers.append(writer)

        if config.output is not None:
            writer = FileWriter(config.output)
            self._writers.append(writer)

        if config.direct_write == "socket":
            writer = SocketWriter(config.host, config.port)
            self._writers.append(writer)

        if config.direct_write == "serial":
            writer = SerialWriter(config.port, config.baudrate)
            self._writers.append(writer)

        if len(self._writers) == 0:
            writer = FileWriter(self._get_stdout_file())
            self._writers.append(writer)

    def _get_stdout_file(self) -> Any:
        """Get binary or text stdout file."""

        if hasattr(sys.stdout, 'buffer'):
            return sys.stdout.buffer

        return sys.stdout

    @property
    def transform(self) -> Transformer:
        """Get the current coordinate transformer instance."""
        return self._transformer

    @property
    def format(self) -> BaseFormatter:
        """Get the current G-code formatter instance."""
        return self._formatter

    @property
    def position(self) -> Point:
        """Get the current absolute positions of the axes."""
        return self._current_axes

    @property
    def is_relative(self) -> bool:
        """Check if the current positioning mode is relative."""
        return self._distance_mode == DistanceMode.RELATIVE

    def get_move_parameter(self, name: str) -> Any:
        """Get the current value of a move parameter by name.

        This method retrieves the last used value for a G-code movement
        parameter. These parameters are stored during move operations and
        include both standard G-code parameters (like F for feed rate)
        and any custom parameters passed to move commands.

        Args:
            name: Name of the parameter (case-insensitive)

        Returns:
            Any: The parameter's value, or None if the parameter hasn't
            been used in any previous move command.
        """

        return self._current_params.get(name)

    @typechecked
    def set_distance_mode(self, mode: DistanceMode | str) -> None:
        """Set the positioning mode for subsequent commands.

        Args:
            mode (DistanceMode): The distance mode to use

        >>> G90|G91
        """

        self._logger.debug("Setting distance mode to: %s", mode)

        self._distance_mode = DistanceMode(mode)
        command = "G91" if mode == DistanceMode.RELATIVE else "G90"
        statement = self.format.command(command)
        self.write(statement)

    @typechecked
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

        point, params, comment = self._process_move_params(point, **kwargs)
        target_axes = self._current_axes.replace(*point)
        statement = self.format.command("G92", params, comment)

        self._update_axes(target_axes, params)
        self.write(statement)

    def push_matrix(self) -> None:
        """Push the current transformation matrix onto the stack.

        Saves the current transformation state that can be restored
        later with `pop_matrix()`.
        """

        self.transform.push_matrix()

    def pop_matrix(self) -> None:
        """Pop and restore the previous transformation matrix.

        Restores from the stack the transformation state to what it
        was when last pushed.
        """

        self.transform.pop_matrix()

    def translate(self, x: float, y: float, z: float = 0) -> None:
        """Apply a translation transformation.

        Args:
            x: Translation distance along X axis
            y: Translation distance along Y axis
            z: Translation distance along Z axis
        """

        self.transform.translate(x, y, z)

    def rotate(self, angle: float, axis: str = 'z') -> None:
        """Apply a rotation transformation.

        Args:
            angle: Rotation angle in degrees
            axis: Axis of rotation (x, y, or z)
        """

        self.transform.rotate(angle, axis)

    def scale(self, *scale: float) -> None:
        """Apply a scaling transformation.

        Args:
            *scale: Scale factors for each axis. If only one value
                is provided uniform scaling is applied to all axes.
        """

        self.transform.scale(*scale)

    def reflect(self, normal: List[float]) -> None:
        """Apply a reflection transformation.

        Args:
            normal: Normal as a 3D vector (nx, ny, nz)
        """

        self.transform.reflect(normal)

    def mirror(self, plane: str = "zx") -> None:
        """Apply a mirror transformation around a plane.

        Args:
            plane: Mirror plane ("xy", "yz", or "zx").
        """

        self.transform.mirror(plane)

    def rename_axis(self, axis: str, label: str) -> None:
        """Rename an axis label in the G-code output.

        Args:
            axis: Axis to rename (x, y, or z)
            label: New label for the axis
        """

        self.format.set_axis_label(axis, label)

    @contextmanager
    def absolute_distance(self):
        """Temporarily set absolute distance mode within a context.

        This context manager temporarily switches to absolute positioning
        mode (G90) and automatically restores the previous mode when
        exiting the context.

        Example:
            >>> with g.absolute_distance():
            ...     g.move(x=10, y=10)  # Absolute move
            ...     g.move(x=20, y=20)  # Absolute move
            ... # Previous distance mode is restored here
        """

        mode = DistanceMode.ABSOLUTE
        previous = self._distance_mode

        try:
            if mode != previous:
                self.set_distance_mode(mode)
            yield
        finally:
            if previous != mode:
                self.set_distance_mode(previous)

    @contextmanager
    def relative_distance(self):
        """Temporarily set relative distance mode within a context.

        This context manager temporarily switches to relative positioning
        mode (G91) and automatically restores the previous mode when
        exiting the context.

        Example:
            >>> with g.relative_distance():
            ...     g.move(x=10, y=10)  # Relative move
            ...     g.move(x=20, y=20)  # Relative move
            ... # Previous distance mode is restored here
        """

        mode = DistanceMode.RELATIVE
        previous = self._distance_mode

        try:
            if mode != previous:
                self.set_distance_mode(mode)
            yield
        finally:
            if previous != mode:
                self.set_distance_mode(previous)

    @typechecked
    def to_absolute(self, point: PointLike) -> Point:
        """Convert a point to absolute coordinates.

        Calculates the absolute coordinates of a target point based on
        the current position and positioning mode (relative/absolute).
        Any None coordinates in the current position are first converted
        to 0.0 to ensure all returned coordinates have numeric values.

        The input is a point-like object containing target coordinates.
        In absolute mode, these are the final coordinates. In relative
        mode, these are offsets from the current position.

        Args:
            point: Absolute target or relative offset

        Returns:
            Point: The absolute target position
        """

        origin = self._current_axes.resolve()

        return (
            origin + Point(*point).resolve()
            if self.is_relative else
            origin.replace(*point)
        )

    @typechecked
    def to_absolute_list(self, points: Sequence[PointLike]) -> List[Point]:
        """Convert a sequence of points to absolute coordinates.

        Args:
            points: Absolute targets or relative offsets

        Returns:
            Point: A tuple of absolute target positions
        """

        results = []
        current = self._current_axes.resolve()

        if self.is_relative:
            for point in points:
                current += Point(*point).resolve()
                results.append(current)
        else:
            for point in points:
                current = current.replace(*point)
                results.append(current)

        return results

    @typechecked
    def to_distance_mode(self, point: PointLike) -> Point:
        """Convert an absolute point to match current distance mode.

        Calculates the coordinates to use in a move command based on the
        current positioning mode (relative/absolute). Any None coordinates
        in the current position or the target point are first converted
        to 0.0 to ensure all returned coordinates have numeric values.

        In absolute mode, returns the absolute coordinates.
        In relative mode, returns the offset from current position.

        Args:
            point: Target point in absolute coordinates

        Returns:
            Point: Coordinates matching current positioning mode
        """

        origin = self._current_axes.resolve()

        return (
            point.resolve() - origin
            if self.is_relative else
            point.resolve()
        )

    @typechecked
    def rapid(self, point: PointLike = None, **kwargs) -> None:
        """Execute a rapid move to the specified location.

        Performs a maximum-speed, uncoordinated move where each axis
        moves independently at its maximum rate to reach the target
        position. This is typically used for non-cutting movements like
        positioning or tool changes.

        Args:
            point (optional): Target position as a point
            x (float, optional): Target X-axis position
            y (float, optional): Target Y-axis position
            z (float, optional): Target Z-axis position
            comment (str, optional): Optional comment to add
            **kwargs: Additional G-code parameters

        >>> G0 [X<x>] [Y<y>] [Z<z>] [<param><value> ...]
        """

        point, params, comment = self._process_move_params(point, **kwargs)
        move, target_axes = self._transform_move(point)
        self._update_axes(target_axes, params)
        self._write_rapid(move, params, comment)

    @typechecked
    def move(self, point: PointLike = None, **kwargs) -> None:
        """Execute a controlled linear move to the specified location.

        The target position can be specified either as a Point object or
        as individual x, y, z coordinates. Additional movement parameters
        can be provided as keyword arguments. The move will be relative
        or absolute based on the current distance mode.

        Args:
            point (optional): Target position as a point
            x (float, optional): Target X-axis position
            y (float, optional): Target Y-axis position
            z (float, optional): Target Z-axis position
            comment (str, optional): Optional comment to add
            **kwargs: Additional G-code parameters

        >>> G1 [X<x>] [Y<y>] [Z<z>] [<param><value> ...]
        """

        point, params, comment = self._process_move_params(point, **kwargs)
        move, target_axes = self._transform_move(point)
        self._update_axes(target_axes, params)
        self._write_move(move, params, comment)

    @typechecked
    def rapid_absolute(self, point: PointLike = None, **kwargs) -> None:
        """Execute a rapid positioning move to absolute coordinates.

        Performs a maximum-speed move to the specified absolute
        coordinates, bypassing any active coordinate system
        transformations. This method temporarily switches to absolute
        positioning mode if relative mode is active.

        Args:
            point (optional): Target position as a point
            x (float, optional): Target X-axis position
            y (float, optional): Target Y-axis position
            z (float, optional): Target Z-axis position
            comment (str, optional): Optional comment to add
            **kwargs: Additional G-code parameters

        >>> G0 [X<x>] [Y<y>] [Z<z>] [<param><value> ...]
        """

        move, params, comment = self._process_move_params(point, **kwargs)
        target_axes = self._current_axes.replace(*move)
        self._update_axes(target_axes, params)

        with self.absolute_distance():
            self._write_rapid(move, params, comment)

    @typechecked
    def move_absolute(self, point: PointLike = None, **kwargs) -> None:
        """Execute a controlled move to absolute coordinates.

        Performs a coordinated linear move to the specified absolute
        coordinates, bypassing any active coordinate system
        transformations. This method temporarily switches to absolute
        positioning mode if relative mode is active.

        Args:
            point (optional): Target position as a point
            x (float, optional): Target X-axis position
            y (float, optional): Target Y-axis position
            z (float, optional): Target Z-axis position
            comment (str, optional): Optional comment to add
            **kwargs: Additional G-code parameters

        >>> G1 [X<x>] [Y<y>] [Z<z>] [<param><value> ...]
        """

        move, params, comment = self._process_move_params(point, **kwargs)
        target_axes = self._current_axes.replace(*move)
        self._update_axes(target_axes, params)

        with self.absolute_distance():
            self._write_move(move, params, comment)

    @typechecked
    def comment(self, message: str, *args: Any) -> None:
        """Write a comment to the G-code output.

        Args:
            message (str): Text of the comment
            *args: Additional values to include in the comment

        >>> ; <message> <args>
        """

        text = (
            message
            if len(args) == 0 else
            f"{message} {' '.join((str(a) for a in args))}"
        )

        comment = self.format.comment(text)
        self.write(comment)

    @typechecked
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

        self._logger.debug("Write statement: %s", statement)

        try:
            line = self.format.line(statement)
            line_bytes = bytes(line, "utf-8")

            for writer in self._writers:
                self._logger.debug("Write to %s", writer)
                writer.write(line_bytes)
        except Exception as e:
            self._logger.exception("Failed to write statement: %s", e)
            raise DeviceError("Failed to write statement") from e

    @typechecked
    def teardown(self, wait: bool = True) -> None:
        """Clean up and disconnect all writers.

        Args:
            wait (bool): Waits for pending operations to complete
        """

        self._logger.info("Teardown writers")

        for writer in self._writers:
            writer.disconnect(wait)

        self._writers.clear()

    def _write_move(self,
        point: Point, params: MoveParams, comment: str | None = None) -> None:
        """Write a linear move statement with the given parameters.

        Args:
            point: Target position
            params: Additional movement parameters
            comment: Comment to include in the move
        """

        args = { **params, "X": point.x, "Y": point.y, "Z": point.z }
        statement = self.format.command("G1", args, comment)
        self.write(statement)

    def _write_rapid(self,
        point: Point, params: MoveParams, comment: str | None = None) -> None:
        """Write a rapid move statement with the given parameters.

        Args:
            point: Target position
            params: Additional movement parameters
            comment: Comment to include in the move
        """

        args = { **params, "X": point.x, "Y": point.y, "Z": point.z }
        statement = self.format.command("G0", args, comment)
        self.write(statement)

    def _process_move_params(self, point: PointLike, **kwargs) -> ProcessedParams:
        """Extract move parameters from the provided arguments.

        The methods that perform movement operations accept a target
        position as a Point object or as individual x, y, z coordinates.
        This method processes the provided arguments and returns a tuple
        containing the target point and a case-insensitive dictionary of
        movement parameters (including X, Y and Z).

        Args:
            point (optional): Target position as a point
            x (float, optional): Target X-axis position
            y (float, optional): Target Y-axis position
            z (float, optional): Target Z-axis position
            comment (str, optional): Comment to include in the move
            **kwargs: Additional G-code parameters

        Returns:
            ProcessedParams: A tuple containing:
                - (Point) The target point of the movement
                - (MoveParams) Processed movement parameters
                - (str | None) Comment to include in the move
        """

        comment = kwargs.pop("comment", None)
        params = MoveParams(kwargs)

        point = (
            Point(*point[:3])
            if point is not None else
            Point.from_params(params)
        )

        params["X"] = point.x
        params["Y"] = point.y
        params["Z"] = point.z

        return point, params, comment

    def _transform_move(self, point: Point) -> Tuple[Point, Point]:
        """Transform target coordinates and determine movement.

        This method transforms the target coordinates of a move using
        the current transformation matrix and determines the movement
        vector that should be used to reach the target.

        Args:
            point: Target position

        Returns:
            Tuple[Point, Point]: A tuple containing:
                - Transformed absolute or relative movement vector
                - Absolute target position before transformation
        """

        # Beware that axes are initialized with `None` to indicate their
        # current position is unknown. If that is the case, this will
        # convert `None` coordinates to zero.

        current_axes = self._current_axes.resolve()
        target_axes = self.to_absolute(point)

        # Transform target coordinates and determine which axes need to
        # move. An axis moves if it was explicitly requested (the point
        # contains a coordinate for it) or if the transformation matrix
        # caused its position to change. All other coordinates of the
        # move vector are set to `None`.

        origin = self.transform.apply_transform(current_axes)
        target = self.transform.apply_transform(target_axes)
        move = (target - origin) if self.is_relative else target
        move = point.combine(origin, target, move)

        return move, target_axes

    def _update_axes(self, axes: Point, params: MoveParams) -> None:
        """Update the internal state after a movement.

        Updates the current position and movement parameters to reflect
        the new machine state after executing a move command.

        Args:
            axes: The new position of all axes
            params: The movement parameters used in the command
        """

        self._logger.debug("New position: %s", axes)
        self._current_params.update(params)
        self._current_axes = axes

    def __enter__(self) -> 'GCodeCore':
        """Enter the context manager."""

        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager and clean up resources."""

        self.teardown()
