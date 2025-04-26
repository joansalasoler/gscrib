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

from typing import NamedTuple

import numpy as np

from gscrib.params import ParamsDict
from gscrib.types import OptFloat


class Point(NamedTuple):
    """A point in a 3D space.

    This class represents a point in 3D space, where each coordinate
    (x, y, z) can be either a ``float`` value or ``None``. None values
    indicate unknown or unspecified coordinates.

    Most methods in :class:`gscrib.GCodeCore` and :class:`gscrib.GCodeBuilder`
    that accept ``Point`` objects are designed to work with point-like
    values, which can be a ``Point`` object or a sequence containing the
    (x, y, z) coordinates as numeric values.

    The class supports basic arithmetic operations, that raise ``TypeError``
    if any coordinates of the points are unknown. The method ``resolve``
    can be used to create a new ``Point`` with any unknown coordinates
    set to zero.

    Examples:
        >>> #Create points using different constructors:
        >>> p1 = Point(1.0, 2.0, 3.0)      # All coordinates specified
        >>> p2 = Point(x=1.0, z=3.0)       # Y coordinate is None
        >>> p3 = Point.zero()              # Point at origin (0, 0, 0)
        >>> p4 = Point.unknown()           # All coordinates are None
        >>>
        >>> # Using PointLike values
        >>> g.move([1.0, 2.0, 3.0])        # Using a list
        >>> g.move(point=(1.0, 2.0, 3.0))  # Using a tuple
        >>> g.move(Point(1.0, 2.0, 3.0))   # Using a Point object
        >>> g.move(x=1.0, y=2.0, z=3.0)    # Individual coordinates
        >>>
        >>> # Arithmetic operations
        >>> p1 = Point(1.0, 2.0, 3.0)
        >>> p2 = Point(2.0, 3.0, 4.0)
        >>> p3 = p1 + p2  # Point(3.0, 5.0, 7.0)
        >>> p4 = p2 - p1  # Point(1.0, 1.0, 1.0)
        >>> p5 = p1 * 2   # Point(2.0, 4.0, 6.0)
        >>> p6 = p1 / 2   # Point(0.5, 1.0, 1.5)
    """

    x: OptFloat = None
    y: OptFloat = None
    z: OptFloat = None

    @classmethod
    def unknown(cls) -> 'Point':
        """Create a point with unknown coordinates"""
        return cls(None, None, None)

    @classmethod
    def zero(cls) -> 'Point':
        """Create a point at origin (0, 0, 0)"""
        return cls(0.0, 0.0, 0.0)

    @classmethod
    def from_vector(cls, vector: np.ndarray) -> 'Point':
        """Create a Point from a 4D vector"""
        return cls(*vector[:3]).resolve()

    def to_vector(self) -> np.ndarray:
        """Convert point to a 4D vector"""
        return np.array([self.x or 0, self.y or 0, self.z or 0, 1.0])

    @classmethod
    def from_params(cls, params: ParamsDict) -> 'Point':
        """Create a point from a dictionary of move parameters."""

        x = params.get('X', None)
        y = params.get('Y', None)
        z = params.get('Z', None)

        return cls(x, y, z)

    def resolve(self) -> 'Point':
        """Create a new point replacing None values with zeros."""

        return Point(
            0 if self.x is None else self.x,
            0 if self.y is None else self.y,
            0 if self.z is None else self.z
        )

    def replace(self,
        x: OptFloat = None, y: OptFloat = None, z: OptFloat = None) -> 'Point':
        """Create a new point replacing only the specified coordinates.

        Args:
            x: New X position or `None` to keep the current
            y: New Y position or `None` to keep the current
            z: New Z position or `None` to keep the current

        Returns:
            A new point with the specified coordinates.
        """

        return Point(
            self.x if x is None else x,
            self.y if y is None else y,
            self.z if z is None else z
        )

    def mask(self,
        x: OptFloat = None, y: OptFloat = None, z: OptFloat = None) -> 'Point':
        """Create a new point with coordinates set to None if specified.

        This method creates a new point where coordinates are set to
        ``None`` if their corresponding parameter is not ``None``. This
        is useful for marking coordinates as unknown when they are
        involved in an operation.

        Args:
            x: Set X to `None` if not `None`
            y: Set Y to `None` if not `None`
            z: Set Z to `None` if not `None`

        Returns:
            A new point with the specified coordinates.
        """

        return Point(
            self.x if x is None else None,
            self.y if y is None else None,
            self.z if z is None else None
        )

    def combine(self, o: 'Point', t: 'Point', m: 'Point') -> 'Point':
        """Update coordinates based on position changes.

        Updates coordinates by comparing the current, reference, and
        target points. Individual coordinates are updated to the values
        from point 'm' following these rules:

        - If the current coordinate is not `None`.
        - If current is `None` but reference and target differ.

        Args:
            o: The reference position
            t: The target point to update towards
            m: Values to use when updating

        Returns:
            A new point with the coordinates combined
        """

        x = m.x if self.x is not None or o.x != t.x else None
        y = m.y if self.y is not None or o.y != t.y else None
        z = m.z if self.z is not None or o.z != t.z else None

        return Point(x, y, z)

    def within_bounds(self, min_point: 'Point', max_point: 'Point') -> bool:
        """Check if point lies within bounds defined by two points.

        Coordinates that are ``None`` in either self, min_point, or
        max_point points are ignored in the comparison.

        Args:
            min_point: The minimum boundary point
            max_point: The maximum boundary point

        Returns:
            True if all known coordinates are within bounds
        """

        def in_range(value, min_bound, max_bound):
            return (
                (None in (value, min_bound, max_bound)) or
                (min_bound <= value <= max_bound)
            )

        return (
            in_range(self.x, min_point.x, max_point.x) and
            in_range(self.y, min_point.y, max_point.y) and
            in_range(self.z, min_point.z, max_point.z)
        )

    def __add__(self, other: 'Point') -> 'Point':
        """Add two points.

        Args:
            other: Point to add to this point

        Raises:
            TypeError: If any of the point coordinates are None.

        Returns:
            A new point with the coordinates added
        """

        return Point(
            self.x + other.x,
            self.y + other.y,
            self.z + other.z
        )

    def __sub__(self, other: 'Point') -> 'Point':
        """Subtract two points.

        Args:
            other: Point to subtract from this point

        Raises:
            TypeError: If any of the point coordinates are None.

        Returns:
            A new point with the coordinates substracted
        """

        return Point(
            self.x - other.x,
            self.y - other.y,
            self.z - other.z
        )

    def __mul__(self, scalar: float) -> 'Point':
        """Multiply the point's coordinates by a scalar.

        Args:
            scalar: The scalar value to multiply by.

        Raises:
            TypeError: If any of the point coordinates are None.

        Returns:
            A new point with the coordinates multiplied by the scalar.
        """

        return Point(
            self.x * scalar,
            self.y * scalar,
            self.z * scalar
        )

    def __neg__(self) -> 'Point':
        """Negate the point's coordinates.

        Returns:
            A new point with negated coordinates.
        """

        return Point(
            None if self.x is None else -(self.x or 0),
            None if self.y is None else -(self.y or 0),
            None if self.z is None else -(self.z or 0)
        )

    def __truediv__(self, scalar: float) -> 'Point':
        """Divide the point's coordinates by a scalar.

        Args:
            scalar: The scalar value to divide by.

        Returns:
            A new point with the coordinates divided by the scalar.

        Raises:
            TypeError: If any of the point coordinates are None.
            ZeroDivisionError: If the scalar is zero.
        """

        return Point(
            self.x / scalar,
            self.y / scalar,
            self.z / scalar
        )

    def __lt__(self, other: 'Point') -> bool:
        """Less than operator

        Args:
            other: Point to compare with this point.

        Raises:
            TypeError: If any of the point coordinates are None.
        """

        return bool(
            self.x <= other.x and
            self.y <= other.y and
            self.z <= other.z and
            (
                self.x < other.x or
                self.y < other.y or
                self.z < other.z
            )
        )

    def __eq__(self, other: 'Point') -> bool:
        """Equal to operator"""

        return bool(
            self.x == other.x and
            self.y == other.y and
            self.z == other.z
        )

    def __ge__(self, other: 'Point') -> bool:
        """Greater than or equal operator."""

        return not (self < other)

    def __gt__(self, other: 'Point') -> bool:
        """Greater than operator."""

        return not (self < other or self == other)

    def __le__(self, other: 'Point') -> bool:
        """Less than or equal operator."""

        return self < other or self == other

    def __ne__(self, other: 'Point') -> bool:
        """Not equal operator."""

        return not (self == other)
