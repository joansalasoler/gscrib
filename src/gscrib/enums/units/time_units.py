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

from gscrib.enums.base_enum import BaseEnum

SYNONYMS = {"s": "seconds", "ms": "milliseconds"}


class TimeUnits(BaseEnum):
    """Units of time measurement."""

    SECONDS = "seconds"
    MILLISECONDS = "milliseconds"

    @classmethod
    def _missing_(cls, value):
        if value in SYNONYMS:
            return cls(SYNONYMS[value])
        return None

    def scale(self, value_in_seconds: float) -> float:
        """Scale a value in `seconds` to this unit"""

        if self == TimeUnits.MILLISECONDS:
            return value_in_seconds * 1000
        return value_in_seconds
