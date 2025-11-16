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

import math
from gscrib.enums.base_enum import BaseEnum


SYNONYMS = {"cw": "clockwise", "ccw": "counter"}


class Direction(BaseEnum):
    """Directions for interpolated moves."""

    CLOCKWISE = "clockwise"
    COUNTER = "counter"

    @classmethod
    def _missing_(cls, value):
        if value in SYNONYMS:
            return cls(SYNONYMS[value])
        return None

    def enforce(self, angle: float) -> float:
        """Enforce the direction of an angular move.

        For ``CLOCKWISE`` direction, ensures the angle is negative. For
        ``COUNTER`` (counter-clockwise) direction, ensures the angle is
        positive. If the angle already has the correct sign, it is
        returned unchanged. Otherwise, adds or subtracts 2 * PI to flip
        the direction while maintaining the same final position.

        Args:
            angle: Rotation angle in radians

        Returns:
            Enforced angle
        """

        if self is Direction.CLOCKWISE:
            if angle >= 0:
                angle -= 2 * math.pi
        else:
            if angle <= 0:
                angle += 2 * math.pi

        return angle

    def full_turn(self) -> float:
        """Returns a signed full rotation (±2π) based on direction.

        Returns:
            float: 2π for counter-clockwise, -2π for clockwise
        """

        if self is Direction.CLOCKWISE:
            return -2 * math.pi

        return 2 * math.pi
