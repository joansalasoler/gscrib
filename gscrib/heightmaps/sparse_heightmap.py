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
import cv2 as cv

from numpy import ndarray
from numpy.typing import ArrayLike
from scipy.interpolate import LinearNDInterpolator
from typeguard import typechecked

from gscrib.excepts import FileLoadError
from .raster_heightmap import BaseHeightMap


class SparseHeightMap(BaseHeightMap):
    """Interpolates height map data from sparse point data.

    This class reads scattered (x, y, z) probe data from a CSV file into
    a height map and provides methods for height interpolation at
    specific coordinates and along paths.

    Example:
        >>> height_map = SparseHeightMap.from_path('heights.csv')
        >>> height = height_map.get_depth_at(100, 100)
    """

    __slots__ = (
        "_scale_z",
        "_tolerance",
        "_resolution",
        "_interpolator"
    )

    def __init__(self, sparse_data: ndarray) -> None:
        self._scale_z = 1.0
        self._tolerance = 0.378
        self._interpolator = self._create_interpolator(sparse_data)

    @classmethod
    def from_path(cls, path: str) -> "SparseHeightMap":
        """Create a HeightMap instance from a CSV file.

        Args:
            path (str): Path to the CSV file with X, Y, Z columns

        Returns:
            SparseHeightMap: New HeightMap instance

        Raises:
            FileLoadError: If the CSV file cannot be read
        """

        try:
            delimiter = "\t" if path.lower().endswith(".tsv") else ","
            sparse_data = numpy.loadtxt(path, delimiter=delimiter)

            if len(sparse_data) < 4:
                raise ValueError("At least 4 points are required")

            if sparse_data.shape[1] != 3:
                raise ValueError("CSV file must have exactly 3 columns")

            return cls(sparse_data)
        except Exception as e:
            raise FileLoadError(
                f"Could not load heightmap from '{path}': {str(e)}"
            )

    @typechecked
    def set_scale(self, scale_z: float) -> None:
        """Set the vertical scaling factor for height values.

        Args:
            scale_z (float): Scaling factor to apply to normalized
                height values.

        Raises:
            ValueError: If scale_z is zero or negative
        """

        if scale_z <= 0:
            raise ValueError("Scale factor must be positive")

        self._scale_z = scale_z

    @typechecked
    def set_tolerance(self, tolerance: float) -> None:
        """Set height difference threshold for path sampling.

        This is the minimum height difference between consecutive points
        that will be considered significant during path sampling. Points
        with height differences below this value will be filtered out
        when using ``sample_path()``.

        Args:
            tolerance (float): The minimum height difference

        Raises:
            ValueError: If tolerance is negative
        """

        if tolerance < 0:
            raise ValueError("Tolerance must be non-negative")

        self._tolerance = tolerance

    @typechecked
    def get_depth_at(self, x: Real, y: Real) -> float:
        """Get the interpolated elevation value at specific coordinates.

        Args:
            x (float): X-coordinate in the height map.
            y (float): Y-coordinate in the height map.

        Returns:
            float: Interpolated elevation scaled by the scale factor.
        """

        return self._scale_z * self._interpolator(x, y)

    @typechecked
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

        line_array = numpy.asarray(line, dtype=float)

        if line_array.shape != (4,):
            raise ValueError("Line must contain exactly 4 elements")

        points = self._interpolate_line(line_array)
        filtered = self._filter_points(points, self._tolerance)

        return filtered

    def save_image(self, path: str) -> None:
        """Save the sparse height map as a raster image.

        Args:
            path (str): Path where the image will be saved

        Raises:
            IOError: If the image cannot be written
        """

        points = self._interpolator.points
        width = int(numpy.ceil(points[:, 0].max()))
        height = int(numpy.ceil(points[:, 1].max()))
        raster = self._to_image(width, height)

        if not cv.imwrite(path, raster):
            raise IOError(f"Failed to save image to {path}")

    def _to_image(self, width: int, height: int) -> ndarray:
        """Convert the sparse height map to a raster image.

        Args:
            width (int): Width of the output image in pixels
            height (int): Height of the output image in pixels

        Returns:
            ndarray: 8-bit single channel image where pixel values
                     represent heights scaled to 0-255 range
        """

        # Get bounds from interpolator points
        points = self._interpolator.points
        x_min = points[:, 0].min()
        y_min = points[:, 1].min()

        # Create a grid of points, shifted to positive space
        x = numpy.linspace(x_min, x_min + width - 1, width)
        y = numpy.linspace(y_min, y_min + height - 1, height)
        xs, ys = numpy.meshgrid(x, y)

        # Get interpolated height map from the grid
        points = numpy.vstack((xs.flatten(), ys.flatten())).T
        heights = self._interpolator(points)
        height_map = heights.reshape((height, width))

        # Normalize the height map values
        max_value = numpy.max(height_map)
        min_value = numpy.min(height_map)
        height_range = max(1, max_value - min_value)
        height_map = ((height_map - min_value) * 255 / height_range)

        return height_map.astype(numpy.uint8)

    def _interpolate_line(self, line: ndarray) -> ndarray:
        """Get interpolated points along a straight line."""

        x1, y1, x2, y2 = line
        distance = numpy.hypot(x2 - x1, y2 - y1)
        num_segments = max(int(distance / self._tolerance), 1)

        rows = numpy.linspace(x1, x2, num_segments + 1)
        cols = numpy.linspace(y1, y2, num_segments + 1)

        return numpy.array([
            (x, y, self.get_depth_at(x, y))
            for x, y in zip(rows, cols)
        ])

    def _filter_points(self, points: ndarray, tolerance: float) -> ndarray:
        """Extracts points where height differences exceed tolerance"""

        first_point = points[0]
        last_point = points[-1]
        lines = [first_point]
        last_z = first_point[2]

        for point in points:
            if abs(point[2] - last_z) >= tolerance:
                lines.append(point)
                last_z = point[2]

        if not numpy.array_equal(lines[-1], last_point):
            lines.append(last_point)

        return numpy.array(lines)

    def _create_interpolator(self, sparse_data: ndarray) -> LinearNDInterpolator:
        """Create a bivariate spline interpolator for a heightmap."""

        x = sparse_data[:, 0]
        y = sparse_data[:, 1]
        z = sparse_data[:, 2]

        return LinearNDInterpolator(list(zip(x, y)), z, fill_value=0.0)
