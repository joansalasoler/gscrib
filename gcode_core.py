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
from collections import defaultdict
from typing import Any, List, Dict
from typeguard import typechecked

from vpype_mecode.builder.excepts import DeviceError

from .config import GConfig
from .enums import DistanceMode
from .formatters import BaseFormatter, DefaultFormatter
from .point import Point
from .transformer import Transformer
from .writers import BaseWriter, SocketWriter, SerialWriter, FileWriter


class CoreGBuilder(object):
    """Core G-code generation functionality.

    This class provides the fundamental building blocks for G-code
    generation, including:

    - G-code formatting and output writing
    - Coordinate system transformations
    - Position tracking and distance mode management
    - Basic movement operations (linear and rapid moves)
    - Multiple output methods (file, serial, network socket)

    For general use, it is recommended to use the `GBuilder` class
    instead, which extends `CoreGBuilder` with a more complete set of
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
    can be retrieved using the `get_parameter()` method.

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
        >>> with CoreGBuilder(output="outfile.gcode") as g:
        ...     g.absolute()        # Set absolute positioning mode
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
        self._current_params = defaultdict()
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
    def transformer(self) -> Transformer:
        """Get the current coordinate transformer instance."""
        return self._transformer

    @property
    def formatter(self) -> BaseFormatter:
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

    def get_parameter(self, name: str) -> Any:
        """Get the current value of a parameter by name."""
        return self._current_params.get(name)

    @typechecked
    def set_distance_mode(self, mode: DistanceMode) -> None:
        """Set the positioning mode for subsequent commands.

        Args:
            mode (DistanceMode): The distance mode to use

        >>> G90|G91
        """

        self._logger.debug("Setting distance mode to: %s", mode)

        self._distance_mode = mode
        command = "G91" if mode == DistanceMode.RELATIVE else "G90"
        statement = self._formatter.format_command(command)
        self.write(statement)

    @typechecked
    def set_axis_position(self,
        x: float | None = None, y: float | None = None,
        z: float | None = None, **kwargs : Any) -> None:
        """Set the current position without moving the head.

        This command changes the machine's coordinate system by setting
        the current position to the specified values without any physical
        movement. It's commonly used to set a new reference point or to
        reset axis positions.

        Args:
            x (float, optional): New X-axis position value
            y (float, optional): New Y-axis position value
            z (float, optional): New Z-axis position value
            **kwargs: Additional axis positions

        >>> G92 [X<x>] [Y<y>] [Z<z>] [<axis><value> ...]
        """

        self._logger.debug("Set axis: (%s, %s, %s)", x, y, z)
        self._logger.debug("Set axis params: %s", kwargs)
        self._logger.debug("Current position: %s", self._current_axes)

        target_axes = self._current_axes.replace(x, y, z)
        params = { "x": x, "y": y, "z": z, **kwargs }
        statement = self.formatter.format_command("G92", params)

        self._current_params.update(kwargs)
        self._current_axes = target_axes
        self.write(statement)

        self._logger.debug("New position: %s", target_axes)

    def push_matrix(self) -> None:
        """Push the current transformation matrix onto the stack.

        Saves the current transformation state that can be restored
        later with `pop_matrix()`.
        """

        self.transformer.push_matrix()

    def pop_matrix(self) -> None:
        """Pop and restore the previous transformation matrix.

        Restores from the stack the transformation state to what it
        was when last pushed.
        """

        self.transformer.pop_matrix()

    def translate(self, x: float, y: float, z: float = 0) -> None:
        """Apply a translation transformation.

        Args:
            x: Translation distance along X axis
            y: Translation distance along Y axis
            z: Translation distance along Z axis
        """

        self.transformer.translate(x, y, z)

    def rotate(self, angle: float, axis: str = 'z') -> None:
        """Apply a rotation transformation.

        Args:
            angle: Rotation angle in radians
            axis: Axis of rotation (x, y, or z)
        """

        self.transformer.rotate(angle, axis)

    def scale(self, *scale: float) -> None:
        """Apply a scaling transformation.

        Args:
            *scale: Scale factors for each axis. If only one value
                is provided uniform scaling is applied to all axes.
        """

        self.transformer.scale(*scale)

    def reflect(self, normal: List[float]) -> None:
        """Apply a reflection transformation.

        Args:
            normal: Normal as a 3D vector (nx, ny, nz)
        """

        self.transformer.reflect(normal)

    def mirror(self, plane: str = "zx") -> None:
        """Apply a mirror transformation around a plane.

        Args:
            plane: Mirror plane ("xy", "yz", or "zx").
        """

        self.transformer.mirror(plane)

    def rename_axis(self, axis: str, label: str) -> None:
        """Rename an axis label in the G-code output.

        Args:
            axis: Axis to rename (x, y, or z)
            label: New label for the axis
        """

        self.formatter.set_axis_label(axis, label)

    def absolute(self) -> None:
        """Set the distance mode to absolute.

        >>> G90
        """

        self.set_distance_mode(DistanceMode.ABSOLUTE)

    def relative(self) -> None:
        """Set the distance mode to relative.

        >>> G91
        """

        self.set_distance_mode(DistanceMode.RELATIVE)

    @typechecked
    def rapid(self,
        x: float | None = None, y: float | None = None,
        z: float | None = None, **kwargs: Any) -> None:
        """Execute a rapid move to the specified location.

        Performs a maximum-speed, uncoordinated move where each axis
        moves independently at its maximum rate to reach the target
        position. This is typically used for non-cutting movements like
        positioning or tool changes.

        Args:
            x (float, optional): Target X-axis position
            y (float, optional): Target Y-axis position
            z (float, optional): Target Z-axis position
            **kwargs: Additional parameters

        >>> G0 [X<x>] [Y<y>] [Z<z>] [<param><value> ...]
        """

        self.move(x, y, z, rapid=True, **kwargs)

    @typechecked
    def move(self,
        x: float | None = None, y: float | None = None,
        z: float | None = None, rapid: bool = False, **kwargs: Any) -> None:
        """Execute a controlled linear move to the specified location.

        Performs a coordinated linear movement at the current feed rate.
        All axes will arrive at their target positions simultaneously,
        following a straight line path. The move will be relative or
        absolute based on current distance mode.

        Args:
            x (float, optional): Target X-axis position
            y (float, optional): Target Y-axis position
            z (float, optional): Target Z-axis position
            rapid (bool): Use rapid movement instead of linear
            **kwargs: Additional parameters

        >>> G1 [X<x>] [Y<y>] [Z<z>] [<param><value> ...]
        """

        self._logger.debug("Move: (%s, %s, %s)", x, y, z)
        self._logger.debug("Move params: rapid=%s, %s", rapid, kwargs)
        self._logger.debug("Current position: %s", self._current_axes)

        # Beware that axes are initialized with float("-inf") to
        # indicate their current position is unknown. If that is the
        # case, this will convert -inf coordinates to zero.

        current_axes = self._current_axes.resolve()

        # Compute target position in the original coordinate system.

        target_axes = (
            current_axes.replace(x, y, z)
            if not self.is_relative else
            current_axes + Point.create(x, y, z)
        )

        # Transform target coordinates and determine which axes need to
        # move. An axis moves if it was explicitly requested or if the
        # transformation matrix caused its position to change.

        new_axes = self.transformer.apply_transform(target_axes)
        old_axes = self.transformer.apply_transform(current_axes)
        nx = self._get_coordinate_or_none(x, old_axes.x, new_axes.x)
        ny = self._get_coordinate_or_none(y, old_axes.y, new_axes.y)
        nz = self._get_coordinate_or_none(z, old_axes.z, new_axes.z)

        # Write the move statement and update the internal state

        self._write_move(nx, ny, nz, rapid, kwargs)
        self._current_params.update(kwargs)
        self._current_axes = target_axes

        self._logger.debug("New position: %s", target_axes)

    @typechecked
    def rapid_absolute(self,
        x: float | None = None, y: float | None = None,
        z: float | None = None, **kwargs: Any) -> None:
        """Execute a rapid positioning move to absolute coordinates.

        Performs a maximum-speed move to the specified absolute
        coordinates, bypassing any active coordinate system
        transformations. This method temporarily switches to absolute
        positioning mode if relative mode is active.

        Args:
            x (float, optional): Target X-axis position
            y (float, optional): Target Y-axis position
            z (float, optional): Target Z-axis position
            **kwargs: Additional parameters

        >>> G0 [X<x>] [Y<y>] [Z<z>] [<param><value> ...]
        """

        self.move_absolute(x, y, z, rapid = True, **kwargs)

    @typechecked
    def move_absolute(self,
        x: float | None = None, y: float | None = None,
        z: float | None = None, rapid: bool = False, **kwargs: Any) -> None:
        """Execute a controlled move to absolute coordinates.

        Performs a coordinated linear move to the specified absolute
        coordinates, bypassing any active coordinate system
        transformations. This method temporarily switches to absolute
        positioning mode if relative mode is active.

        Args:
            x (float, optional): Target X-axis position
            y (float, optional): Target Y-axis position
            z (float, optional): Target Z-axis position
            **kwargs: Additional parameters

        >>> G1 [X<x>] [Y<y>] [Z<z>] [<param><value> ...]
        """

        self._logger.debug("Move absolute: (%s, %s, %s)", x, y, z)
        self._logger.debug("Move params: rapid=%s, %s", rapid, kwargs)
        self._logger.debug("Current position: %s", self._current_axes)

        target_axes = self._current_axes.replace(x, y, z)
        was_relative = self.is_relative

        if was_relative: self.absolute()
        self._write_move(x, y, z, rapid, kwargs)
        if was_relative: self.relative()

        self._current_params.update(kwargs)
        self._current_axes = target_axes

        self._logger.debug("New position: %s", target_axes)

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

        comment = self.formatter.format_comment(text)
        self.write(comment)

    @typechecked
    def write(self, statement: str) -> None:
        """Write a G-code statement to all configured writers.

        Direct use of this method is discouraged as it bypasses all state
        management. Using this method may lead to inconsistencies between
        the internal state tracking and the actual machine state. Instead,
        prefer using the dedicated methods like `move()` or `rapid()`,
        which properly maintain state.

        Args:
            statement: The G-code statement to write

        Raises:
            DeviceError: If writing fails

        Example:
            >>> g = CoreGBuilder()
            >>> g.write("G1 X10 Y20") # Bypasses state tracking
            >>> g.move(x=10, y=20) # Uses proper state management
        """

        self._logger.debug("Write statement: %s", statement)

        try:
            line = self.formatter.format_line(statement)
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
        x: float | None, y: float | None, z: float | None,
        rapid: bool, params: Dict[str, Any]) -> None:
        """Write a move statement with the given parameters.

        Args:
            x: X position or `None` if it should not be changed
            y: Y position or `None` if it should not be changed
            z: Z position or `None` if it should not be changed
            rapid: Rapid movement (G0) instead of linear (G1)
            params: Additional movement parameters
        """

        command = "G0" if rapid else "G1"
        params = { "x": x, "y": y, "z": z, **params }
        statement = self.formatter.format_command(command, params)
        self.write(statement)

    @staticmethod
    def _get_coordinate_or_none(
        request: float | None,
        origin: float, target: float) -> float | None:
        """Determine if a coordinate needs to be updated.

        Args:
            request: The requested coordinate value or `None`
            origin: The original coordinate value
            target: The target coordinate value

        Returns:
            float or None: Transformed coordinate or `None`
        """

        explicit_request = request is not None
        should_update = explicit_request or target != origin

        return target if should_update else None

    def __enter__(self) -> 'CoreGBuilder':
        """Enter the context manager."""

        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager and clean up resources."""

        self.teardown()
