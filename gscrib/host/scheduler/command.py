# -*- coding: utf-8 -*-

# Gscrib. Supercharge G-code with Python.
# Copyright (C) 2026 Joan Sala <contact@joansala.com>
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

import re, operator
from dataclasses import dataclass
from functools import reduce

from ..exceptions import EmptyCommand, MultipleCommands


# Regex for removing line comments from G-code lines
_RE_LINE_COMMENT = re.compile(r';.*$', re.MULTILINE)

# Regex for removing inline comments from G-code lines
_RE_INLINE_COMMENT = re.compile(r'\(.*?\)', re.MULTILINE)


@dataclass(frozen=True)
class Command:
    """Represents a G-code command ready for transmission.

    This class encapsulates a single G-code instruction along with its
    line number and transmission settings. It handles normalization
    of the G-code string (removing comments, whitespace) and formatting,
    including optional checksum generation.

    Attributes:
        line_number (int): Line number for this command.
        instruction (str): The G-code instruction string.
        signed (bool): Whether to append line number and checksum.
    """

    line_number: int
    instruction: str
    signed: bool

    def __post_init__(self) -> None:
        """Validate and normalize the G-code string.

        Raises:
            EmptyCommandError: If G-code is empty or only comments.
            MultipleCommandsError: If G-code contains multiple lines.
        """

        if not self.instruction:
            raise EmptyCommand("G-code cannot be empty")

        clean_code = self._normalize_gcode(self.instruction)

        if "\n" in clean_code:
            raise MultipleCommands("G-code must be a single line")

        if not clean_code:
            raise EmptyCommand("G-code cannot be empty or only comments")

        object.__setattr__(self, "instruction", clean_code)

    def format_line(self) -> str:
        """Return the command string ready for sending.

        If signed is true, includes line number and checksum. Otherwise,
        returns the normalized G-code as-is.

        Returns:
            str: The formatted G-code line.
        """

        return (
            self.instruction if not self.signed
            else self._format_with_checksum()
        )

    def _format_with_checksum(self) -> str:
        """Format with line number and checksum.

        Returns:
            str: The signed command string.
        """

        numbered_line = f"N{self.line_number} {self.instruction}"
        checksum = self._xor_checksum(numbered_line)
        signed_line = f"{numbered_line}*{checksum}"

        return signed_line

    @staticmethod
    def _normalize_gcode(raw_gcode: str) -> str:
        """Normalize a G-code line for transmission.

        Removes inline comments (parentheses), line comments (semicolon),
        and surrounding whitespace. Replaces line endings with newlines.
        Converts to uppercase.

        Args:
            raw_gcode (str): The input G-code string.

        Returns:
            str: The normalized G-code string.
        """

        clean_gcode = raw_gcode.replace("\r", "\n")
        clean_gcode = _RE_INLINE_COMMENT.sub('', clean_gcode)
        clean_gcode = _RE_LINE_COMMENT.sub('', clean_gcode)
        clean_gcode = clean_gcode.strip().upper()

        return clean_gcode

    @staticmethod
    def _xor_checksum(line: str) -> int:
        """Compute XOR checksum for a line of G-code.

        Args:
            line (str): The string to checksum.

        Returns:
            int: The calculated checksum value.
        """

        return reduce(operator.xor, bytearray(line, "ascii"), 0)
