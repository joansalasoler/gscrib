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

import logging
from dataclasses import asdict
from contextlib import contextmanager
from typing import Any, List, Sequence, Tuple
from typeguard import typechecked

from .config import GConfig
from .enums import Axis, DistanceMode, Direction
from .excepts import DeviceError, GCodeError, GscribError
from .formatters import BaseFormatter, DefaultFormatter
from .params import ParamsDict
from .geometry import Point, CoordinateTransformer
from .types import PointLike, ProcessedParams
from .writers import BaseWriter, ConsoleWriter, FileWriter
from .writers import SocketWriter, SerialWriter


# pylint: disable=protected-access
class GCodeCore(object):
    """Core class for generating G-code output.

    This class provides the fundamental components for generating and
    outputting G-code, including formatting, coordinate transformations,
    and support for various output destinations.

    It offers the core functionality necessary for G-code generation and
    is designed to be extended when building custom G-code builders. For
    most purposes, it is recommended to use :class:`GCodeBuilder` instead,
    as it extends this base class with a more comprehensive set of G-code
    commands and enhanced state management features.

    Key responsibilities of this class include:

    - Formatting and writing G-code instructions.
    - Basic movement commands (linear and rapid moves).
    - Position tracking and distance mode management.
    - Coordinate system transformations (rotation, scaling, etc).
    - Support for multiple output methods (file, serial, network, etc).

    Basic movement methods include ``move()`` and ``rapid()`` for linear
    and rapid moves, respectively. These methods automatically apply any
    active transformations before outputting the corresponding G-code.
    To bypass transformations when moving to absolute coordinates the
    ``move_absolute()`` and ``rapid_absolute()`` methods may be used.

    Movement coordinates can be provided as individual X, Y, Z parameters
    to this methods or as a :class:`geometry.Point` object. Additionally,
    all movement methods accept extra G-code parameters as keyword
    arguments and support an optional ``comment`` for annotation.

    The ``transform`` property gives access to the coordinate transformer,
    enabling operations such as translation, rotation, and scaling of the
    coordinate system. Note that transformations only apply to the X, Y,
    and Z axes. While custom axes or parameters may be included in the
    movement commands, transformations and tracking will be limited to
    the X, Y, and Z axes. Any other custom parameters can be retrieved
    via the ``get_parameter()`` method.

    The ``position`` property tracks the current positions of the X, Y,
    and Z axes, reflecting their absolute positions in the original
    coordinate system (without any transformations).

    The ``teardown()`` method should be called when done to properly
    close connections and clean up resources. However, using the class
    as a context manager automatically handles this.

    This class constructor accepts the following configuration options,
    which can be provided as keyword arguments or as a dictionary:

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

    def __init__(self, *args, **kwargs: Any) -> None:
        """Initialize G-code generator with configuration.

        Args:
            **kwargs: Configuration parameters
        """

        if args and isinstance(args[0], GConfig):
            kwargs = {**asdict(args[0]), **kwargs}

        if args and isinstance(args[0], dict):
            kwargs = {**args[0], **kwargs}

        config: GConfig = GConfig(**kwargs)

        self._logger = logging.getLogger(__name__)
        self._formatter = DefaultFormatter()
        self._transformer = CoordinateTransformer()
        self._current_axes = Point.unknown()
        self._current_params = ParamsDict()
        self._distance_mode = DistanceMode.ABSOLUTE
        self._direction = Direction.CLOCKWISE
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
            writer = ConsoleWriter()
            self.add_writer(writer)

        if config.output is not None:
            writer = FileWriter(config.output)
            self.add_writer(writer)

        if config.direct_write == "socket":
            writer = SocketWriter(config.host, int(config.port))
            self.add_writer(writer)

        if config.direct_write == "serial":
            writer = SerialWriter(str(config.port), config.baudrate)
            self.add_writer(writer)

    @property
    def transform(self) -> CoordinateTransformer:
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
    def distance_mode(self) -> DistanceMode:
        """Get the current positioning mode."""
        return self._distance_mode

    def get_parameter(self, name: str) -> Any:
        """Get the current value of a move parameter by name.

        This method retrieves the last used value for a G-code movement
        parameter. These parameters are stored during move operations and
        include both standard G-code parameters (like ``F`` for feed rate)
        and any custom parameters passed to move commands.

        Args:
            name (str): Name of the parameter (case-insensitive)

        Returns:
            Any: The parameter's value, or None if the parameter hasn't
            been used in any previous move command.
        """

        return self._current_params.get(name)

    @typechecked
    def set_formatter(self, formatter: BaseFormatter) -> None:
        """Set a new G-code formatter.

        This method allows you to change the G-code formatter used by
        the generator. The formatter is responsible for converting commands
        and parameters into the appropriate string format for output.

        Args:
            formatter (BaseFormatter): The formatter to use
        """

        self._formatter = formatter

    @typechecked
    def get_writer(self, index: int = 0) -> BaseWriter:
        """Get a writer by index.

        Args:
            index (int): Index of the writer to retrieve

        Returns:
            BaseWriter: The writer at the specified index

        Raises:
            IndexError: If the index is out of range
        """

        return self._writers[index]

    @typechecked
    def add_writer(self, writer: BaseWriter) -> None:
        """Add a new writer to the list of writers.

        Args:
            writer (BaseWriter): The writer to add
        """

        if not writer in self._writers:
            self._writers.append(writer)

    @typechecked
    def remove_writer(self, writer: BaseWriter) -> None:
        """Remove a writer from the list of writers.

        Args:
            writer (BaseWriter): The writer to remove
        """

        if writer in self._writers:
            self._writers.remove(writer)

    @typechecked
    def set_distance_mode(self, mode: DistanceMode | str) -> None:
        """Set the positioning mode for subsequent commands.

        Args:
            mode (DistanceMode | str): The distance mode (absolute/relative)


        Raises:
            ValueError: If distance mode is not valid

        >>> G90|G91
        """

        self._logger.debug("Setting distance mode to: %s", mode)

        self._distance_mode = DistanceMode(mode)
        command = "G91" if mode == DistanceMode.RELATIVE else "G90"
        statement = self.format.command(command)
        self.write(statement)

    @typechecked
    def set_axis(self, point: PointLike = None, **kwargs) -> None:
        """Set the current position without moving the head.

        This command changes the machine's coordinate system by setting
        the current position to the specified values without any physical
        movement. It's commonly used to set a new reference point or to
        reset axis positions.

        Args:
            point (Point, optional): New axis position as a point
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

    def rename_axis(self, axis: Axis | str, label: str) -> None:
        """Rename an axis label in the G-code output.

        Args:
            axis: Axis to rename (x, y, or z)
            label: New label for the axis
        """

        self.format.set_axis_label(axis, label)

    @contextmanager
    def absolute_mode(self):
        """Temporarily set absolute distance mode within a context.

        This context manager temporarily switches to absolute positioning
        mode (``G90``) and automatically restores the previous mode when
        exiting the context.

        Example:
            >>> with g.absolute_mode():
            ...     g.move(x=10, y=10)  # Absolute move
            ...     g.move(x=20, y=20)  # Absolute move
            ... # Previous distance mode is restored here
        """

        mode = DistanceMode.ABSOLUTE
        previous = self._distance_mode

        if mode != self._distance_mode:
            self.set_distance_mode(mode)

        try:
            yield
        finally:
            if previous != self._distance_mode:
                self.set_distance_mode(previous)

    @contextmanager
    def relative_mode(self):
        """Temporarily set relative distance mode within a context.

        This context manager temporarily switches to relative positioning
        mode (``G91``) and automatically restores the previous mode when
        exiting the context.

        Example:
            >>> with g.relative_mode():
            ...     g.move(x=10, y=10)  # Relative move
            ...     g.move(x=20, y=20)  # Relative move
            ... # Previous distance mode is restored here
        """

        mode = DistanceMode.RELATIVE
        previous = self._distance_mode

        if mode != self._distance_mode:
            self.set_distance_mode(mode)

        try:
            yield
        finally:
            if previous != self._distance_mode:
                self.set_distance_mode(previous)

    @contextmanager
    def current_transform(self):
        """Temporarily save the transformation state within a context.

        This context manager allows you to temporarily modify the current
        coordinate system. Any changes made to the coordinate system
        within the context will be reverted when exiting the context.

        Returns:
            CoordinateTransformer: The current transformer instance.

        Example:
            >>> with g.current_transform():
            ...     g.transform.translate(10, 0, 0)
            ...     g.move(x=10, y=10)  # Transformed move
            ... # Transformation state is restored here
        """

        state = self.transform._copy_state()

        try:
            yield self.transform
        finally:
            self.transform._revert_state(state)

    @contextmanager
    def named_transform(self, name: str):
        """Temporarily restore a transformation state within a context.

        This context manager allows you to temporarily modify the current
        coordinate system. Any changes made to the coordinate system
        within the context will be reverted when exiting the context.

        Args:
            name: Name of the saved transformation state

        Raises:
            KeyError: If the named state does not exist

        Returns:
            CoordinateTransformer: The current transformer instance.

        Example:
            >>> with g.named_transform("my_transform"):
            ...     g.move(x=10, y=10)  # Transformed move
            ... # Transformation state is restored here
        """

        state = self.transform._copy_state()
        self.transform.restore_state(name)

        try:
            yield self.transform
        finally:
            self.transform._revert_state(state)

    @typechecked
    def to_absolute(self, point: PointLike) -> Point:
        """Convert a point to absolute coordinates.

        Calculates the absolute coordinates of a target point based on
        the current position and positioning mode (relative/absolute).
        Any ``None`` coordinates in the current position are first converted
        to 0.0 to ensure all returned coordinates have numeric values.

        The input is a point object containing target coordinates.
        In absolute mode, these are the final coordinates. In relative
        mode, these are offsets from the current position.

        Args:
            point (Point): Absolute target or relative offset

        Returns:
            Point: The absolute target position
        """

        origin = self._current_axes.resolve()

        return (
            origin + Point(*point).resolve()
            if self.distance_mode.is_relative else
            origin.replace(*point)
        )

    @typechecked
    def to_absolute_list(self, points: Sequence[PointLike]) -> List[Point]:
        """Convert a sequence of points to absolute coordinates.

        Args:
            points (Sequence[Point]): Absolute targets or relative offsets

        Returns:
            Point: A tuple of absolute target positions
        """

        results = []
        current = self._current_axes.resolve()

        if self.distance_mode.is_relative:
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
        current positioning mode (relative/absolute). Any ``None`` coordinates
        in the current position or the target point are first converted
        to 0.0 to ensure all returned coordinates have numeric values.

        In absolute mode, returns the absolute coordinates.
        In relative mode, returns the offset from current position.

        Args:
            point (Point): Target point in absolute coordinates

        Returns:
            Point: Coordinates matching current positioning mode
        """

        origin = self._current_axes.resolve()

        return (
            point.resolve() - origin
            if self.distance_mode.is_relative else
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
            point (Point, optional): Target position as a point
            x (float, optional): Target X-axis position
            y (float, optional): Target Y-axis position
            z (float, optional): Target Z-axis position
            comment (str, optional): Optional comment to add
            **kwargs: Additional G-code parameters

        >>> G0 [X<x>] [Y<y>] [Z<z>] [<param><value> ...]
        """

        point, params, comment = self._process_move_params(point, **kwargs)
        move, target_axes = self._transform_move(point)
        statement, params = self._prepare_rapid(move, params, comment)
        self._update_axes(target_axes, params)
        self.write(statement)

    @typechecked
    def move(self, point: PointLike = None, **kwargs) -> None:
        """Execute a controlled linear move to the specified location.

        The target position can be specified either as a :class:`geometry.Point`
        object or as individual x, y, z coordinates. Additional movement
        parameters can be provided as keyword arguments. The move will be
        relative or absolute based on the current distance mode.

        Args:
            point (Point, optional): Target position as a point
            x (float, optional): Target X-axis position
            y (float, optional): Target Y-axis position
            z (float, optional): Target Z-axis position
            comment (str, optional): Optional comment to add
            **kwargs: Additional G-code parameters

        >>> G1 [X<x>] [Y<y>] [Z<z>] [<param><value> ...]
        """

        point, params, comment = self._process_move_params(point, **kwargs)
        move, target_axes = self._transform_move(point)
        statement, params = self._prepare_move(move, params, comment)
        self._update_axes(target_axes, params)
        self.write(statement)

    @typechecked
    def rapid_absolute(self, point: PointLike = None, **kwargs) -> None:
        """Execute a rapid positioning move to absolute coordinates.

        Performs a maximum-speed move to the specified absolute
        coordinates, bypassing any active coordinate system
        transformations. This method temporarily switches to absolute
        positioning mode if relative mode is active.

        Args:
            point (Point, optional): Target position as a point
            x (float, optional): Target X-axis position
            y (float, optional): Target Y-axis position
            z (float, optional): Target Z-axis position
            comment (str, optional): Optional comment to add
            **kwargs: Additional G-code parameters

        >>> G0 [X<x>] [Y<y>] [Z<z>] [<param><value> ...]
        """

        move, params, comment = self._process_move_params(point, **kwargs)
        target_axes = self._current_axes.replace(*move)

        with self.absolute_mode():
            statement, params = self._prepare_rapid(move, params, comment)
            self._update_axes(target_axes, params)
            self.write(statement)

    @typechecked
    def move_absolute(self, point: PointLike = None, **kwargs) -> None:
        """Execute a controlled move to absolute coordinates.

        Performs a coordinated linear move to the specified absolute
        coordinates, bypassing any active coordinate system
        transformations. This method temporarily switches to absolute
        positioning mode if relative mode is active.

        Args:
            point (Point, optional): Target position as a point
            x (float, optional): Target X-axis position
            y (float, optional): Target Y-axis position
            z (float, optional): Target Z-axis position
            comment (str, optional): Optional comment to add
            **kwargs: Additional G-code parameters

        >>> G1 [X<x>] [Y<y>] [Z<z>] [<param><value> ...]
        """

        move, params, comment = self._process_move_params(point, **kwargs)
        target_axes = self._current_axes.replace(*move)

        with self.absolute_mode():
            statement, params = self._prepare_move(move, params, comment)
            self._update_axes(target_axes, params)
            self.write(statement)

    @typechecked
    def annotate(self, key: str, value: str) -> None:
        """Write an annotation comment to the G-code output.

        Annotations are a special type of structured comments that can be
        used by post-processors or other tools to store metadata or
        configuration information. Useful for storing tool settings,
        material properties, or processing parameters alongside the G-code.

        Args:
            key (str): Variable name (a valid identifier)
            value (str): Variable value (any string)

        Raises:
            ValueError: If key is not a valid identifier

        Example:
            >>> g.annotate("tool_diameter", "3.175 mm")
            ; @set tool_diameter = 3.175 mm

        >>> ; @set <key> = <value>
        """

        if not key.isidentifier():
            raise ValueError("Not a valid annotation key.")

        annotation = f"@set {key} = {value}"
        comment = self.format.comment(annotation)
        self.write(comment)

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
        use the dedicated methods like ``move()``, ``tool_on()``, etc.,
        which properly maintain state and ensure safe operation.

        Args:
            statement: The raw G-code statement to write

        Raises:
            GCodeError: If the internal state is inconsistent
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
        except GCodeError:
            raise
        except DeviceError:
            raise
        except Exception as e:
            self._logger.exception("Failed to write statement: %s", e)
            raise GscribError("Internal error") from e

    @typechecked
    def teardown(self, wait: bool = True) -> None:
        """Clean up and disconnect all writers.

        This method should be called to ensure all writers are properly
        closed and any pending operations are completed. It is typically
        called when the builder instance is no longer needed.

        Args:
            wait (bool): Waits for pending operations to complete
        """

        self._logger.info("Teardown writers")

        for writer in self._writers:
            writer.disconnect(wait)

        self._writers.clear()

    def flush(self) -> None:
        """Forces any buffered data to be written immediately.

        Usually, file writes are buffered to improve performance, reducing
        the number of disk operations by grouping multiple writes together.

        In most cases, manual flushing is not required, as data is flushed
        automatically when the buffer is full or the file is closed. Use
        flush when immediate output is needed, such as for logging or when
        other processes read the file.
        """

        self._logger.info("Flush writers")

        for writer in self._writers:
            writer.flush()

    def _prepare_move(self,
        point: Point, params: ParamsDict,
        comment: str | None = None) -> Tuple[str, ParamsDict]:
        """Process a linear move statement with the given parameters.

        Args:
            point: Target position
            params: Additional movement parameters
            comment: Comment to include in the move

        Returns:
            Tuple[str, ParamsDict]: A tuple containing:
                - (str) The formatted G-code statement
                - (ParamsDict) The updated movement parameters
        """

        args = { **params, "X": point.x, "Y": point.y, "Z": point.z }
        statement = self.format.command("G1", args, comment)
        return statement, params

    def _prepare_rapid(self,
        point: Point, params: ParamsDict,
        comment: str | None = None) -> Tuple[str, ParamsDict]:
        """Process a rapid move statement with the given parameters.

        Args:
            point: Target position
            params: Additional movement parameters
            comment: Comment to include in the move

        Returns:
            Tuple[str, ParamsDict]: A tuple containing:
                - (str) The formatted G-code statement
                - (ParamsDict) The updated movement parameters
        """

        args = { **params, "X": point.x, "Y": point.y, "Z": point.z }
        statement = self.format.command("G0", args, comment)
        return statement, params

    def _process_move_params(self, point: PointLike, **kwargs) -> ProcessedParams:
        """Extract move parameters from the provided arguments.

        The methods that perform movement operations accept a target
        position as a Point object or as individual x, y, z coordinates.
        This method processes the provided arguments and returns a tuple
        containing the target point and a case-insensitive dictionary of
        movement parameters (including X, Y and Z).

        Args:
            point (Point, optional): Target position as a point
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
        params = ParamsDict(kwargs)

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

        is_relative = self.distance_mode.is_relative
        origin = self.transform.apply_transform(current_axes)
        target = self.transform.apply_transform(target_axes)
        move = (target - origin) if is_relative else target
        move = point.combine(origin, target, move)

        return move, target_axes

    def _update_axes(self, axes: Point, params: ParamsDict) -> None:
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
