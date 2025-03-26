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

from typing import Callable

import numpy as np
from typeguard import typechecked

from .enums import Direction
from .point import Point, PointLike
from .gcode_core import GCodeCore


class TracePath:
    """Generating G-code with interpolated motion paths.

    This class provides methods to generate G-code commands for complex
    motion paths by approximating them with small linear segments. The
    path approximation resolution can be configured to balance between
    motion smoothness and G-code file size. Smaller resolution values
    result in smoother paths but generate more G-code commands.

    Unlike standard G-code where arc movements are affected by the
    selected plane (G17/G18/G19), this class always traces paths on the
    XY plane by default. To transform paths to other planes or orientations,
    use the transformation methods provided by the builder (translate,
    rotate, scale, etc).

    For complex transformations, the GCodeCore.transformer property can
    be used as a context manager to ensure proper matrix stack handling.
    Transformations can be combined and will affect all subsequent path
    operations until the context is exited.

    Example:
        >>> g.move(x=10, y=0)               # Move to start position
        >>> g.trace.select_resolution(0.1)  # Set 0.1mm resolution
        >>> g.trace.select_direction("cw")  # Set clockwise direction
        >>>
        >>> # Draw a quarter circle in XY plane
        >>> g.trace.arc(target=(0, 10), center=(-10, 0))
        >>>
        >>> # Draw an arc rotated 45° around the X axis
        >>> with g.transformer:  # Use transformer as context manager
        ...     g.move(x=0, y=0)
        ...     g.rotate(math.pi / 4, 'x')  # Rotate 45° around X axis
        ...     g.trace.circle(center=(0, 10))
        ... # Applied transforms ar restored here
    """

    __slots__ = (
        '_g',
        '_direction',
        '_resolution'
    )

    def __init__(self, builder: GCodeCore):
        self._g: GCodeCore = builder
        self.select_direction(Direction.CLOCKWISE)
        self.select_resolution(0.01) # 0.01 mm

    @typechecked
    def select_resolution(self, resolution: float) -> None:
        """Set the resolution for interpolation.

        Controls the accuracy of path approximation by specifying the
        maximum length of linear segments used to trace the path. Smaller
        values result in smoother paths but generate more G-code commands.

        Args:
            resolution: Maximum length in current work units
        """

        self._resolution = resolution

    @typechecked
    def select_direction(self, direction: Direction | str) -> None:
        """Set the rotation direction for subsequent movements.

        Args:
            direction: Clockwise or counter-clockwise rotation
        """

        self._direction = Direction(direction)

    @typechecked
    def arc(self, target: PointLike, center: PointLike) -> None:
        """Trace an arc from the current position to a target point.

        This method generates a series of linear segments that
        approximate a circular arc. The arc is traced around a center
        point, maintaining a constant radius throughout the motion.

        The direction of the arc is determined by the last call to
        select_direction(). If Z is provided for the target point, the
        arc will perform helical interpolation.

        Args:
            target: Absolute or relative destination point (x, y, [z])
            center: Center point (x, y) relative to the current position

        Raises:
            ValueError: If start and end points are not equidistant

        Example:
            >>> # Draw a quarter circle (90 degrees) clockwise
            >>> g.move(x=0, y=10)
            >>> g.trace.select_direction("cw")  # clockwise
            >>> g.trace.arc(target=(10, 0), center=(0, -10))
        """

        # Convert all coordinates to absolute positions. Coordinates
        # will be converted back to relative if needed during tracing.

        o = self._g.position.resolve()
        t = self._g.to_absolute(target)
        c = o + Point(*center).resolve()

        # Validate that both points lie on the same circle

        do = o - c; dt = t - c
        radius = np.hypot(do.x, do.y)

        if abs(radius - np.hypot(dt.x, dt.y)) > 1e-10:
            raise ValueError(
                "Cannot trace arc: start and end points must be at "
                "an equal distance from the center point"
            )

        # Compute the angular displacement between start and end points.
        # Total angle is negative for clockwise arcs, positive otherwise

        end_angle = np.arctan2(dt.y, dt.x)
        start_angle = np.arctan2(do.y, do.x)
        total_angle = self._direction.enforce(end_angle - start_angle)

        # Vertical displacement for helical motion if Z is provided

        height = t.z - o.z if len(target) > 2 else 0
        total_length = np.hypot(radius * total_angle, height)

        def arc_function(theta: float) -> Point:
            angle = start_angle + total_angle * theta
            x = c.x + radius * np.cos(angle)
            y = c.y + radius * np.sin(angle)
            z = o.z + theta * height
            return Point(x, y, z)

        self._trace(total_length, arc_function)

    @typechecked
    def circle(self, center: PointLike) -> None:
        """Trace a complete circle around a center point.

        Creates a full 360-degree circular path around the specified
        center point, starting and ending at the current position. The
        direction of rotation is determined by the last call to
        select_direction().

        Args:
            center: Center point (x, y) relative to the current position

        Example:
            >>> # Draw a circle with 10mm radius
            >>> g.move(x=10, y=0)
            >>> g.trace.select_direction("ccw")  # counter-clockwise
            >>> g.trace.circle(center=(-10, 0))
        """

        self.arc(self._g.position, center)

    def _trace(self, length: float, function: Callable[[float], Point]) -> None:
        """Approximate a parametric curve with linear segments.

        Divides the curve into small linear segments based on the current
        resolution setting. The curve is defined by a parametric function
        that takes a parameter theta from 0 to 1 and returns a Point.
        The length parameter is used to determine the number of segments
        needed to maintain the desired resolution.

        Args:
            length: Total curve length in current work units
            function: Parametric function f(theta)
        """

        steps = max(2, int(length / self._resolution))

        for theta in (i / steps for i in range(1, steps + 1)):
            point = self._g.to_distance_mode(function(theta))
            self._g.move(point)
