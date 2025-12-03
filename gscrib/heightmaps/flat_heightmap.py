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

from numbers import Real
from typing import Sequence, Union

import numpy

from typeguard import typechecked
from numpy.typing import ArrayLike
from numpy import ndarray
from .base_heightmap import BaseHeightMap


class FlatHeightMap(BaseHeightMap):
    """No-op height map implementation."""

    @typechecked
    def get_depth_at(self, x: Real, y: Real) -> float:
        """Get the interpolated elevation value at specific coordinates.

        Args:
            x (Real): X-coordinate in the height map.
            y (Real): Y-coordinate in the height map.

        Returns:
            float: Always returns zero.
        """

        return 0.0

    @typechecked
    def sample_path(self, line: Union[Sequence[float], ArrayLike]) -> ndarray:
        """Return start and end points of the line with zero height.

        Args:
            line: Line coordinates as (x1, y1, x2, y2).

        Returns:
            ndarray: Array of two points (x, y, z) with z = 0.

        Raises:
            ValueError: If line does not contain exactly 4 elements.
        """

        line_array = numpy.asarray(line, dtype=float)

        if line_array.shape != (4,):
            raise ValueError("Line must contain exactly 4 elements")

        return numpy.array([
            [line_array[0], line_array[1], 0.0],
            [line_array[2], line_array[3], 0.0]
        ])
