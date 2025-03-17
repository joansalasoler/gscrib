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

import sys
from collections import defaultdict
from typing import Any, List, Dict
from typeguard import typechecked

from .enums import DistanceMode
from .utils import Point, Transformer
from .formatters import BaseFormatter, DefaultFormatter
from .writers import BaseWriter, SocketWriter, SerialWriter, FileWriter


class CoreGBuilder(object):
    """A class for handling G-code generation and transformation."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize G-code generator with configuration.

        Args:
            **kwargs: Configuration parameters
        """

        self._formatter = DefaultFormatter()
        self._transformer = Transformer()
        self._current_axes = Point.zero()
        self._current_params = defaultdict()
        self._distance_mode = DistanceMode.ABSOLUTE
        self._writers: List[BaseWriter] = []
        self._initialize_formatter(kwargs)
        self._initialize_writers(kwargs)

    def _initialize_formatter(self, config: Dict[str, Any]) -> None:
        """Initialize the G-code formatter."""

        self._formatter.set_decimal_places(config.get("decimal_places", 5))
        self._formatter.set_comment_symbols(config.get("comment_symbols", ";"))
        self._formatter.set_line_endings(config.get("line_endings", "os"))
        self._formatter.set_axis_label("x", config.get("x_axis", "X"))
        self._formatter.set_axis_label("y", config.get("y_axis", "Y"))
        self._formatter.set_axis_label("z", config.get("z_axis", "Z"))

    def _initialize_writers(self, config: Dict[str, Any]) -> None:
        """Initialize output writers."""

        output = config.get("output", None)
        print_lines = config.get("print_lines", False)
        direct_write_mode = config.get("direct_write_mode", "off")
        host = config.get("host", "localhost")
        port = config.get("port", 8000)
        baudrate = config.get("baudrate", 250000)
        wait_for_response = config.get("wait_for_response", True)

        if print_lines is True:
            writer = FileWriter(sys.stdout.buffer)
            self._writers.append(writer)

        if output is not None:
            writer = FileWriter(output)
            self._writers.append(writer)

        if direct_write_mode == "socket":
            writer = SocketWriter(host, port, wait_for_response)
            self._writers.append(writer)

        if direct_write_mode == "serial":
            writer = SerialWriter(port, baudrate)
            self._writers.append(writer)

        if len(self._writers) == 0:
            writer = FileWriter(sys.stdout.buffer)
            self._writers.append(writer)

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
        return self.transformer.reverse_transform(self._current_axes)

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

        statement = self.formatter.format_command("G92", kwargs)
        self._current_params.update(kwargs)
        self._current_axes = Point(x, y, z)
        self.write(statement)

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

    def reflect(self, angle: float, axis: str = 'z') -> None:
        """Apply a reflection transformation.

        Args:
            angle: Angle of the reflection in radians
            axis: Axis of reflection (x, y, or z)
        """

        self.transformer.reflect(angle, axis)

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

        current_axes = self._current_axes
        is_relative = self.is_relative

        point = (
            current_axes.replace(x, y, z)
            if is_relative == False else
            current_axes + Point.create(x, y, z)
        )

        axes = self.transformer.apply_transform(point)
        axes = axes - current_axes if is_relative else axes

        nx = self._get_coordinate_or_none(x, point.x, axes.x)
        ny = self._get_coordinate_or_none(y, point.y, axes.y)
        nz = self._get_coordinate_or_none(z, point.z, axes.z)

        self._write_move(nx, ny, nz, rapid, kwargs)
        self._current_params.update(kwargs)
        self._current_axes = axes

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

        axes = self._current_axes.replace(x, y, z)
        was_relative = self.is_relative

        if was_relative: self.absolute()
        self._write_move(x, y, z, rapid, kwargs)
        if was_relative: self.relative()

        self._current_params.update(kwargs)
        self._current_axes = axes

    @typechecked
    def comment(self, message: str) -> None:
        """Write a comment to the G-code output.

        Args:
            message (str): Text of the comment

        >>> ; <message>
        """

        comment = self.formatter.format_comment(message)
        self.write(comment)

    @typechecked
    def write(self, statement: str, requires_response: bool = False) -> None:
        """Write a G-code statement to all configured writers.

        Args:
            statement: The G-code statement to write
            requires_response: Whether to wait for a response

        Raises:
            RuntimeError: If writing fails
        """

        try:
            line = self.formatter.format_line(statement)
            line_bytes = bytes(line, "utf-8")

            for writer in self._writers:
                writer.write(line_bytes, requires_response)
        except Exception as e:
            raise RuntimeError(f"Failed to write statement: {e}")

    @typechecked
    def teardown(self, wait: bool = True) -> None:
        """Clean up and disconnect all writers.

        Args:
            wait (bool): Waits for pending operations to complete
        """

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
        request: float | None, origin: float,
        transform: float) -> float | None:
        """Determine if a coordinate needs to be updated.

        Args:
            request: The requested coordinate value or `None`
            origin: The original coordinate value
            transform: The transformed coordinate value

        Returns:
            float or None: Transformed coordinate or `None`
        """

        explicit_request = request is not None
        transform_changed = transform != origin
        should_update = explicit_request or transform_changed

        return transform if should_update else None

    def __enter__(self) -> 'CoreGBuilder':
        """Enter the context manager."""

        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager and clean up resources."""

        self.teardown()
