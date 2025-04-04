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

import copy
from typing import List, Tuple

import numpy as np
from typeguard import typechecked
from scipy.spatial.transform import Rotation
from scipy import linalg

from gscrib.enums import Axis, Plane
from .point import Point, PointLike


class CoordinateTransformer:
    """Coordinate system transformations using 4x4 matrices.

    This class provides methods for transforming the coordinate system
    through operations such as translation, rotation, scaling, and
    reflection. It maintains a transformation stack for nested
    transformations.

    Transformations are represented internally using 4x4 homogeneous
    transformation matrices, allowing for chaining of operations.

    Example:
        >>> with CoordinateTransformer() as t:
        ...     t.translate(10.0, 0.0)
        ...     t.rotate(90, axis = 'z')
        ...     t.scale(2.0)
    """

    __slots__ = (
        '_to_pivot',
        '_from_pivot',
        '_curent_pivot',
        '_current_matrix',
        '_inverse_matrix',
        '_matrix_stack',
        '_pivot_stack',
    )

    def __init__(self) -> None:
        """Initialize with identity matrix."""

        self.set_pivot(point=(0, 0, 0))
        self._current_matrix: np.ndarray = np.eye(4)
        self._inverse_matrix: np.ndarray = np.eye(4)
        self._matrix_stack: List[np.ndarray] = []
        self._pivot_stack: List[Point] = []

    @typechecked
    def set_pivot(self, point: PointLike) -> None:
        """Set the pivot point for transformations.

        The pivot point is the reference around which transformations
        like rotation and scaling occur. For example, to rotate a circle
        around its center, set the pivot point to the circle’s midpoint
        before applying the rotation. By default it is set to the
        origin of coordinates.

        Args:
            point: Pivot point in absolute coordinates.
        """


        point = Point(*point).resolve()
        x, y, z = point

        self._from_pivot = self._tranlation_matrix(-x, -y, -z)
        self._to_pivot = self._tranlation_matrix(x, y, z)
        self._curent_pivot = point

    def save_state(self) -> None:
        """Save the current transformation state onto the stack.

        This allows for temporary modifications to the transformation
        state, which can later be reverted using `restore_state()`. The
        cuurrent transformation matrix and pivot point are saved.
        """

        self._matrix_stack.append(self._current_matrix.copy())
        self._pivot_stack.append(self._curent_pivot)

    def restore_state(self) -> None:
        """Restore the last saved transformation state.

        This reverts the transformation matrix and pivot point to the
        last saved state. This is useful for undoing temporary
        transformations or changes made after a `save_state()` call.

        Raises:
            IndexError: If attempting to pop from an empty stack.
        """

        if not self._matrix_stack:
            raise IndexError("Cannot restore state: stack is empty")

        self._current_matrix = self._matrix_stack.pop()
        self._inverse_matrix = linalg.inv(self._current_matrix)

        pivot_point = self._pivot_stack.pop()
        self.set_pivot(pivot_point)

    @typechecked
    def chain_transform(self, transform_matrix: np.ndarray) -> None:
        """Chain a new transformation with the current matrix.

        Args:
            transform_matrix: A 4x4 transformation matrix to apply.

        Raises:
            ValueError: If the input matrix is not 4x4.
        """

        if transform_matrix.shape != (4, 4):
            raise ValueError("Transform matrix must be 4x4")

        matrix = self._to_pivot @ transform_matrix @ self._from_pivot
        self._current_matrix = matrix @ self._current_matrix
        self._inverse_matrix = linalg.inv(self._current_matrix)

    @typechecked
    def translate(self, x: float, y: float, z: float = 0.0) -> None:
        """Apply a 3D translation transformation.

        Args:
            x: Translation in X axis.
            y: Translation in Y axis.
            z: Translation in Z axis (default: 0.0).
        """

        translation_matrix = self._tranlation_matrix(x, y, z)
        self.chain_transform(translation_matrix)

    @typechecked
    def scale(self, *scale: float) -> None:
        """Apply uniform or non-uniform scaling to axes.

        Args:
            *scale: Scale factors for the axes.

        Example:
            >>> matrix.scale(2.0) # Scale everything by 2x
            >>> matrix.scale(2.0, 0.5) # Stretch in x, compress in y
            >>> matrix.scale(2.0, 1.0, 0.5) # Stretch x, preserve y, compress z

        Raises:
            ValueError: If number of scale factors is not between 1 and 3.
        """

        if not 1 <= len(scale) <= 3:
            raise ValueError("Scale accepts 1 to 3 parameters")

        if any(factor == 0 for factor in scale):
            raise ValueError("Scale cannot be zero")

        scale_vector = (*scale, *scale, *scale, 1.0)

        if len(scale) > 1:
            scale_vector = (*scale, *(1.0,) * (4 - len(scale)))

        scale_matrix = np.diag(scale_vector)
        self.chain_transform(scale_matrix)

    @typechecked
    def rotate(self, angle: float, axis: Axis | str = Axis.Z) -> None:
        """Apply a rotation transformation around any axis.

        Args:
            angle: Rotation angle in degrees.
            axis: Axis of rotation ('x', 'y', or 'z').

        Raises:
            KeyError: If axis is not 'x', 'y', or 'z'.
        """

        axis = Axis(axis)
        rotation_vector = self._rotation_vector(angle, axis)
        rotation = Rotation.from_rotvec(rotation_vector)

        rotation_matrix = np.eye(4)
        rotation_matrix[:3, :3] = rotation.as_matrix()

        self.chain_transform(rotation_matrix)

    @typechecked
    def reflect(self, normal: List[float]) -> None:
        """Apply a reflection transformation across a plane.

        The reflection matrix is calculated using the Householder
        transformation: R = I - 2 * (n ⊗ n), where n is the normalized
        normal vector and ⊗ is outer product

        Args:
            normal: Normal as a 3D vector (nx, ny, nz)
        """

        if all(value == 0 for value in normal):
            raise ValueError("Normal vector cannot be zero")

        n = np.array(normal[:3])
        n = n / linalg.norm(n)

        reflection_matrix = np.eye(4)
        reflection_matrix[:3, :3] = np.eye(3) - 2 * np.outer(n, n)

        self.chain_transform(reflection_matrix)

    @typechecked
    def mirror(self, plane: Plane | str = Plane.ZX) -> None:
        """Apply a mirror transformation across a plane.

        Args:
            plane: Mirror plane ("xy", "yz", or "zx").

        Raises:
            ValueError: If the plane is not "xy", "yz", or "zx".
        """

        plane = Plane(plane)
        self.reflect(plane.normal())

    @typechecked
    def apply_transform(self, point: PointLike) -> Point:
        """Transform a point using the current transformation matrix.

        Args:
            point: A Point or point-like object.

        Returns:
            A Point with the transformed (x, y, z) coordinates.
        """

        point = Point(*point)
        vector = self._current_matrix @ point.to_vector()
        return Point.from_vector(vector)

    @typechecked
    def reverse_transform(self, point: PointLike) -> Point:
        """Invert a transformed point using the current matrix.

        Args:
            point: A Point or point-like object.

        Returns:
            A Point with the inverted (x, y, z) coordinates.
        """

        point = Point(*point)
        vector = self._inverse_matrix @ point.to_vector()
        return Point.from_vector(vector)

    def _copy_state(self) -> Tuple:
        """Create a deep copy of the current state."""

        return (
            copy.deepcopy(self._current_matrix),
            copy.deepcopy(self._inverse_matrix),
            copy.deepcopy(self._matrix_stack),
            copy.deepcopy(self._from_pivot),
            copy.deepcopy(self._to_pivot),
        )

    def _revert_state(self, state: Tuple) -> None:
        """Revert to a previous state."""

        self._current_matrix = copy.deepcopy(state[0])
        self._inverse_matrix = copy.deepcopy(state[1])
        self._matrix_stack = copy.deepcopy(state[2])
        self._from_pivot = copy.deepcopy(state[3])
        self._to_pivot = copy.deepcopy(state[4])

    def _rotation_vector(self, angle: float, axis: Axis) -> List[float]:
        """Create a rotation vector for the specified axis and angle.

        Args:
            angle: Rotation angle in degrees.
            axis: Axis of rotation ('x', 'y', or 'z').

        Returns:
            The rotation vector.

        Raises:
            KeyError: If axis is not 'x', 'y', or 'z'.
        """

        angle_rad = np.radians(angle)

        return {
            Axis.X: [angle_rad, 0, 0],
            Axis.Y: [0, angle_rad, 0],
            Axis.Z: [0, 0, angle_rad]
        }[axis]

    def _tranlation_matrix(self, x: float, y: float, z: float) -> np.array:
        """Create a translation matrix for the given point.

        Args:
            x: Translation in X axis.
            y: Translation in Y axis.
            z: Translation in Z axis

        Returns:
            The translation matrix.
        """

        translation_matrix = np.eye(4)
        translation_matrix[:-1, -1] = [x, y, z]

        return translation_matrix

