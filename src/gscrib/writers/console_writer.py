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

import sys
from typing import Any
from .file_writer import FileWriter


class ConsoleWriter(FileWriter):
    """Writer that outputs commands to the console.

    This class implements a G-code writer specifically designed for
    console output.

    Example:
        >>> writer = ConsoleWriter()
        >>> writer.write(b"G1 X10 Y10\\n")
    """

    def __init__(self, stderr: bool = False):
        """Initialize the console writer.

        Args:
            stderr (bool): If True writes to sys.stderr
        """

        super().__init__(
            self._get_stdout_file() if stderr is False else self._get_stderr_file()
        )

    def connect(self) -> "ConsoleWriter":
        """Establish the connection to the console output."""

        super().connect()
        self._is_terminal = True
        return self

    def _get_stdout_file(self) -> Any:
        """Get binary or text stdout file."""

        if hasattr(sys.stdout, "buffer"):
            return sys.stdout.buffer

        return sys.stdout

    def _get_stderr_file(self) -> Any:
        """Get binary or text stdout file."""

        if hasattr(sys.stderr, "buffer"):
            return sys.stderr.buffer

        return sys.stderr
