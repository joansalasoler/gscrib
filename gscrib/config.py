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

from dataclasses import dataclass, field
from typing import BinaryIO, TextIO
from .enums import DirectWrite


@dataclass
class GConfig():
    """Configuration settings for the G-code builders.

    This class holds various configuration options for controlling the
    behavior of G-code generation. See :class:`GCodeCore` for details on
    how these settings are used in the G-code generation process.

    Example:
        >>> g = GCodeCore({
        ...     "output": "filename.gcode",
        ...     "decimal_places": 5,
        ...     "comment_symbols": ";",
        ... })
    """

    # Output settings
    output: str | TextIO | BinaryIO | None = field(default=None)
    decimal_places: int = field(default=5)
    comment_symbols: str = field(default=";")
    line_endings: str = field(default="os")
    print_lines: bool | str = field(default=False)

    # Direct write settings
    direct_write: str | DirectWrite = field(default='DirectWrite.OFF')
    host: str = field(default="localhost")
    port: int = field(default=8000)
    baudrate: int = field(default=250000)

    # Axis naming settings
    x_axis: str = field(default="X")
    y_axis: str = field(default="Y")
    z_axis: str = field(default="Z")
