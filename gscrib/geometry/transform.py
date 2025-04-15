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

import numpy as np
from scipy import linalg
from typeguard import typechecked

from gscrib.types import PointLike
from .point import Point


class Transform:
    """Encapsulates a transformation state."""

    __slots__ = (
        '_matrix',
        '_inverse',
        '_pivot',
        '_from_pivot',
        '_to_pivot'
    )

    def __init__(self, matrix: np.ndarray, pivot: Point) -> None:
        self._set_pivot(pivot)
        self._set_matrix(matrix)

    @typechecked
    def _set_pivot(self, point: Point) -> None:
        """Set the pivot point for new chained transformations."""

        self._pivot = point.resolve()
        self._from_pivot = self._tranlation_matrix(-point)
        self._to_pivot = self._tranlation_matrix(point)

    @typechecked
    def _set_matrix(self, matrix: np.ndarray) -> None:
        """Set the transformation matrix."""

        if matrix.shape != (4, 4):
            raise ValueError("Transform matrix must be 4x4")

        self._matrix = matrix.copy()
        self._inverse = linalg.inv(matrix)

    @typechecked
    def _chain_matrix(self, matrix: np.ndarray) -> None:
        """Chain a new transformation with the current matrix."""

        if matrix.shape != (4, 4):
            raise ValueError("Transform matrix must be 4x4")

        translated_matrix = self._to_pivot @ matrix @ self._from_pivot
        self._set_matrix(translated_matrix @ self._matrix)

    def _tranlation_matrix(self, point: Point) -> np.array:
        """Create a translation matrix for the given point."""

        x, y, z = point
        translation_matrix = np.eye(4)
        translation_matrix[:-1, -1] = [x, y, z]
        return translation_matrix

    @typechecked
    def apply(self, point: PointLike) -> Point:
        """Transform the coordinates of a point.

        Args:
            point (Point): A Point or point-like object.

        Returns:
            A Point with the transformed (x, y, z) coordinates.
        """

        point = Point(*point)
        vector = self._matrix @ point.to_vector()
        return Point.from_vector(vector)

    @typechecked
    def reverse(self, point: PointLike) -> Point:
        """Invert he transformed coordinates of a point.

        Args:
            point (Point): A Point or point-like object.

        Returns:
            A Point with the inverted (x, y, z) coordinates.
        """

        point = Point(*point)
        vector = self._inverse @ point.to_vector()
        return Point.from_vector(vector)
