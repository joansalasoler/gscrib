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

from typing import NamedTuple, TypeAlias
from typing import Sequence, Union

import numpy as np
from gscrib.params import ParamsDict

OptFloat: TypeAlias = float | None
PointLike: TypeAlias = Union['Point', Sequence[float | None], np.ndarray, None]


class Point(NamedTuple):
    """A point in a 3D space."""

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

    def __eq__(self, other: 'Point') -> bool:
        """Equal to operator"""

        return bool(
            self.x == other.x and
            self.y == other.y and
            self.z == other.z
        )

    def __lt__(self, other: 'Point') -> bool:
        """Less than operator"""

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
