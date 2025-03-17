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

import vpype
from vpype_mecode.builder.enums import BaseEnum


class LengthUnits(BaseEnum):
    """Units of length measurement."""

    INCHES = "in"
    MILLIMETERS = "mm"

    def __init__(self, value):
        self.scale_factor = 1.0 / vpype.convert_length(value)

    def scale(self, value_in_px: float) -> float:
        """Scale a value in pixels to this unit"""

        return value_in_px * self.scale_factor

    def to_pixels(self, value_in_units: float) -> float:
        """Scale a value in this unit to pixels"""

        return value_in_units / self.scale_factor
