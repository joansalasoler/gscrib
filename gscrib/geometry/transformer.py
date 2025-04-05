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
from .transform import Transform


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
        '_transforms_stack',
        '_current_transform',
    )

    def __init__(self) -> None:
        """Initialize with identity matrix."""

        matrix = np.eye(4)
        pivot = Point.zero()

        self._transforms_stack: List[Transform] = []
        self._current_transform: Transform = Transform(matrix, pivot)

    def set_pivot(self, point: PointLike) -> None:
        """Set the pivot point for subsequent transformations.

        The pivot point is the reference around which transformations
        like rotation and scaling occur. For example, to rotate a circle
        around its center, set the pivot point to the circle’s midpoint
        before applying the rotation. By default it is set to the
        origin of coordinates.

        Args:
            point: Pivot point in absolute coordinates.
        """

        point = Point(*point)
        self._current_transform._set_pivot(point)

    def save_state(self) -> None:
        """Save the current transformation state onto the stack.

        This allows for temporary modifications to the transformation
        state, which can later be reverted using `restore_state()`. The
        cuurrent transformation matrix and pivot point are saved.
        """

        transform = copy.deepcopy(self._current_transform)
        self._transforms_stack.append(transform)

    def restore_state(self) -> None:
        """Restore the last saved transformation state.

        This reverts the transformation matrix and pivot point to the
        last saved state. This is useful for undoing temporary
        transformations or changes made after a `save_state()` call.

        Raises:
            IndexError: If attempting to pop from an empty stack.
        """

        if len(self._transforms_stack) < 1:
            raise IndexError("Cannot restore state: stack is empty")

        transform = self._transforms_stack.pop()
        self._current_transform = transform

    def chain_transform(self, transform_matrix: np.ndarray) -> None:
        """Chain a new transformation with the current matrix.

        Args:
            transform_matrix: A 4x4 transformation matrix to apply.

        Raises:
            ValueError: If the input matrix is not 4x4.
        """

        self._current_transform._chain_matrix(transform_matrix)

    @typechecked
    def translate(self, x: float, y: float, z: float = 0.0) -> None:
        """Apply a 3D translation transformation.

        Args:
            x: Translation in X axis.
            y: Translation in Y axis.
            z: Translation in Z axis (default: 0.0).
        """

        translation_matrix = np.eye(4)
        translation_matrix[:-1, -1] = [x, y, z]
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

    def apply_transform(self, point: PointLike) -> Point:
        """Transform a point using the current transformation matrix.

        Args:
            point: A Point or point-like object.

        Returns:
            A Point with the transformed (x, y, z) coordinates.
        """

        return self._current_transform.apply(point)

    def reverse_transform(self, point: PointLike) -> Point:
        """Invert a transformed point using the current matrix.

        Args:
            point: A Point or point-like object.

        Returns:
            A Point with the inverted (x, y, z) coordinates.
        """

        return self._current_transform.reverse(point)

    def _copy_state(self) -> Tuple:
        """Create a deep copy of the current state."""

        return (
            copy.deepcopy(self._current_transform),
            copy.deepcopy(self._transforms_stack),
        )

    def _revert_state(self, state: Tuple) -> None:
        """Revert to a previous state."""

        self._current_transform = state[0]
        self._transforms_stack = state[1]

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
