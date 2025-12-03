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

from abc import ABC, abstractmethod
from numbers import Real
from typing import Sequence, Union

from numpy.typing import ArrayLike
from numpy import ndarray


class BaseHeightMap(ABC):
    """Base class for height map implementations."""

    @abstractmethod
    def get_depth_at(self, x: Real, y: Real) -> float:
        """Get the interpolated elevation value at specific coordinates.

        Args:
            x (Real): X-coordinate in the height map.
            y (Real): Y-coordinate in the height map.

        Returns:
            float: Interpolated elevation scaled by the scale factor.
        """

    @abstractmethod
    def sample_path(self, line: Union[Sequence[float], ArrayLike]) -> ndarray:
        """Sample height values along a straight line path.

        Generates a series of points along the line with their corresponding
        heights, filtering out points where height differences are below
        the specified tolerance.

        Args:
            line: Sequence containing start and end points of the line
                to sample in the format (x1, y1, x2, y2).
            tolerance (float, optional): Minimum height difference between
                consecutive points to be included in the output.

        Returns:
            ndarray: Array of points (x, y, z) along the line where
                height changes exceed the tolerance.

        Raises:
            ValueError: If line does not contain exactly 4 elements or
                cannot be converted to float values.
        """
