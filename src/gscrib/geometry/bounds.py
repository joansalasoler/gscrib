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

from typing import Union, Tuple
from typeguard import typechecked

from gscrib.types import Bound
from .point import Point


VALID_PROPERTIES = (
    "axes",
    "bed-temperature",
    "chamber-temperature",
    "hotend-temperature",
    "feed-rate",
    "tool-number",
    "tool-power",
)


class BoundManager:
    """Bounds manager and validator."""

    def __init__(self):
        self._bounds = {}

    def get_bounds(self, name: str) -> Tuple[Bound | None, Bound | None]:
        """Retrieve the bounds for a given property.

        Args:
            name (str): Parameter name

        Returns:
            Tuple[Bound, Bound]: The min and max bounds
        """

        if name not in VALID_PROPERTIES:
            raise ValueError(f"Unknown property '{name}'")

        return self._bounds.get(name, (None, None))

    @typechecked
    def set_bounds(self, name: str, min: Bound, max: Bound) -> None:
        """Set the bounds for a given property.

        Args:
            name (str): The property for which bounds are being set.
            min (Bound): The minimum value of the property.
            max (Bound): The maximum value of the property.

        Raises:
            ValueError: If bounds are not valid or property is unknown.
            TypeError: If the type of min/max is incorrect.
        """

        if name not in VALID_PROPERTIES:
            raise ValueError(f"Unknown property '{name}'")

        if name == "axes":
            if not isinstance(min, Point):
                raise TypeError(f"Min value must be a Point")
            if not isinstance(max, Point):
                raise TypeError(f"Max value must be a Point")
        else:
            if not isinstance(min, (int, float)):
                raise TypeError(f"Min value must be a number")
            if not isinstance(max, (int, float)):
                raise TypeError(f"Max value must be a number")

        if min >= max:
            raise ValueError(f"Min value must be less than max value")

        self._bounds[name] = (min, max)

    @typechecked
    def validate(self, name: str, value: Union[int, float, Point]) -> None:
        """Validate whether a given value is within bounds.

        Args:
            name (str): The property to validate.
            value (Union[int, float, Point]): The value to validate.

        Raises:
            ValueError: If bounds where defined for the property and the
                provided value is outside bounds.
        """

        if name not in VALID_PROPERTIES:
            raise ValueError(f"Unknown property '{name}'")

        if name not in self._bounds:
            return

        min_value, max_value = self._bounds.get(name)

        if isinstance(value, Point):
            if not value.within_bounds(min_value, max_value):
                raise ValueError(f"Point {value} is out of bounds for '{name}'")
        elif not (min_value <= value <= max_value):
            raise ValueError(f"Value {value} is out of bounds for '{name}'")
