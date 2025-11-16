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

from typeguard import typechecked
from gscrib.enums import BaseEnum


class GCodeEntry:
    """Represents a single G-Code instruction entry."""

    @typechecked
    def __init__(self, enum: BaseEnum, instruction: str, description: str):
        self._enum = enum
        self._instruction = instruction
        self._description = description
        self._validate_entry()

    @property
    def enum(self) -> BaseEnum:
        """Enum value associated with this entry."""
        return self._enum

    @property
    def instruction(self) -> str:
        """G-Code instruction associated with the enum value."""
        return self._instruction

    @property
    def description(self) -> str:
        """Description of what the G-Code instruction does"""
        return self._description

    def _validate_entry(self):
        """Check that no entry fields are empty."""

        if len(self._instruction) < 1:
            raise ValueError("Instruction cannot be empty")

        if len(self._description) < 1:
            raise ValueError("Description cannot be empty")
