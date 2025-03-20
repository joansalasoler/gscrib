# -*- coding: utf-8 -*-

# G-Code generator for Vpype.
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

from math import inf
from typing import NamedTuple
import numpy as np


class Point(NamedTuple):
    """A point in a 3D space."""

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    @classmethod
    def unknown(cls) -> 'Point':
        """Create a point with unknown coordinates"""
        return cls(-inf, -inf, -inf)

    @classmethod
    def zero(cls) -> 'Point':
        """Create a point at origin (0, 0, 0)"""
        return cls(0.0, 0.0, 0.0)

    @classmethod
    def from_vector(cls, vector: np.ndarray) -> 'Point':
        """Create a Point from a 4D vector"""
        return cls(*vector[:3])

    def to_vector(self) -> np.ndarray:
        """Convert point to a 4D vector"""
        return np.array([self.x, self.y, self.z, 1.0])

    @classmethod
    def create(cls,
        x: float | None = None,
        y: float | None = None,
        z: float | None = None) -> 'Point':
        """Create a point converting `None` values to zero.

        Args:
            x: X coordinate, defaults to 0 if `None`
            y: Y coordinate, defaults to 0 if `None`
            z: Z coordinate, defaults to 0 if `None`
        """

        return cls(x or 0, y or 0, z or 0)

    def replace(self,
        x: float | None = None,
        y: float | None = None,
        z: float | None = None) -> 'Point':
        """Create a new point replacing only the specified coordinates.

        Args:
            x: New X position or `None` to keep the current
            y: New Y position or `None` to keep the current
            z: New Z position or `None` to keep the current

        Returns:
            A new point with the specified coordinates.
        """

        return Point(
            x if x is not None else self.x or 0,
            y if y is not None else self.y or 0,
            z if z is not None else self.z or 0
        )

    def resolve(self) -> 'Point':
        """Create a new point replacing -inf values with zeros."""

        return Point(
            0 if self.x == -inf else self.x,
            0 if self.y == -inf else self.y,
            0 if self.z == -inf else self.z
        )

    def __add__(self, other: 'Point') -> 'Point':
        """Add two points.

        Args:
            other: Point to add to this point

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

        Returns:
            A new point with the coordinates substracted
        """

        return Point(
            self.x - other.x,
            self.y - other.y,
            self.z - other.z
        )
