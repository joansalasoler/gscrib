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

import os
from array import array
from numbers import Number

import numpy as np
from typeguard import typechecked

from .base_formatter import BaseFormatter


DEFAULT_DECIMAL_PLACES = 5
DEFAULT_COMMENT_SYMBOLS = ";"
COMMENT_OPENINGS = ("(", "[", "{", "<", '"', "'", "/*")
COMMENT_ENDINGS = (")", "]", "}", ">", '"', "'", "*/")
VALID_AXES = ( "X", "Y", "Z" )


class DefaultFormatter(BaseFormatter):
    """Formats G-code output."""

    __slots__ = (
        "_labels",
        "_line_endings",
        "_decimal_places",
        "_comment_template"
    )

    def __init__(self):
        """Initialize with default settings."""

        self._line_endings = os.linesep
        self._decimal_places = DEFAULT_DECIMAL_PLACES
        self._labels = { a: a for a in VALID_AXES }
        self.set_comment_symbols(DEFAULT_COMMENT_SYMBOLS)

    @typechecked
    def set_axis_label(self, axis: str, label: str):
        """Set a custom label for an axis.

        Args:
            axis: The axis to relabel ('x', 'y', or 'z')
            label: The new label for the axis

        Raises:
            ValueError: If axis is invalid or label is empty
        """

        if axis.upper() not in VALID_AXES:
            raise ValueError(f"Invalid axis: {axis}")

        if not label.strip():
            raise ValueError("Axis label cannot be empty")

        self._labels[axis.upper()] = label.strip().upper()

    @typechecked
    def set_comment_symbols(self, value: str) -> None:
        """Set the comment symbols for G-code comments.

        Args:
            value: Comment symbols to use (non-empty string)

        Raises:
            ValueError: If value is empty or not a string
        """

        if not value.strip():
            raise ValueError("Comment symbols cannot be empty")

        template = self._to_comment_template(value.strip())
        self._comment_template = template

    @typechecked
    def set_decimal_places(self, value: int) -> None:
        """Set the maximum number of decimal places for number formatting.

        Args:
            value: Number of decimal places (non-negative integer)

        Raises:
            ValueError: If value is negative
        """

        if value < 0:
            raise ValueError("Decimal places must be non-negative")

        self._decimal_places = value

    @typechecked
    def set_line_endings(self, line_endings: str):
        """Set the line ending style.

        Args:
            line_endings: Line ending style ('os' or custom string)
        """

        self._line_endings = os.linesep

        if line_endings != "os":
            chars = bytes(line_endings, "utf-8")
            self._line_endings = chars.decode("unicode-escape")

    @typechecked
    def format_number(self, number: Number) -> str:
        """Format a number with specified decimal places.

        Args:
            number: The number to format

        Returns:
            Formatted number string

        Raises:
            ValueError: If value is not finite
            TypeError: If value is a complex number
            typeguard.TypeCheckError: If value is not a number
        """

        if number == 0:
            return "0"

        if not np.isfinite(float(number)):
            raise ValueError("Number cannot be infinite or NaN")

        return np.format_float_positional(
            number,
            precision=self._decimal_places,
            unique=True,
            fractional=True,
            sign=False,
            trim="-"
        )

    @typechecked
    def format_line(self, statement: str) -> str:
        """Format a single G-code statement for output.

        Args:
            statement: The G-code statement to format

        Returns:
            Formatted statement with proper line endings
        """

        return f"{statement.rstrip()}{self._line_endings}"

    @typechecked
    def format_comment(self, text: str) -> str:
        """Format text as a G-code comment.

        Args:
            text: Text to be formatted as a comment

        Returns:
            Formatted comment string
        """

        return self._comment_template.format(text)

    @typechecked
    def format_command(self, command: str, params: dict = {}) -> str:
        """Format a G-code command with optional parameters.

        Args:
            command: The G-code command (e.g., G0, G1, M104)
            params: Dictionary of parameters and their values

        Returns:
            Formatted command statement string
        """

        if isinstance(params, dict) and len(params) > 0:
            formatted_params = self.format_parameters(params)
            return f"{command} {formatted_params}"

        return command

    @typechecked
    def format_parameters(self, params: dict) -> str:
        """Format G-code statement parameters.

        Args:
            params: Statement parameters

        Returns:
            Formatted parameters string
        """

        space = " "
        buffer = array('u')
        upper_params = { k.upper(): v for k, v in params.items() }

        # Handle XYZ axis parameters

        for axis in (a for a in VALID_AXES if a in upper_params):
            param = upper_params[axis]

            if isinstance(param, Number):
                buffer.extend(space)
                buffer.extend(self._labels[axis])
                buffer.extend(self.format_number(param))

        # Handle other parameters

        for label in (a for a in upper_params if a not in VALID_AXES):
            param = upper_params[label]
            is_number = isinstance(param, Number)
            value = self.format_number(param) if is_number else str(param)
            buffer.extend(space)
            buffer.extend(label)
            buffer.extend(value)

        return buffer.tounicode()[1:]

    @typechecked
    def _to_comment_template(self, open_symbols: str) -> str:
        """Create a template for G-code comments."""

        if open_symbols in COMMENT_OPENINGS:
            index = COMMENT_OPENINGS.index(open_symbols)
            end_symbols = COMMENT_ENDINGS[index]
            return f"{open_symbols} {{}} {end_symbols}"

        return f"{open_symbols} {{}}"
