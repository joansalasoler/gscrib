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

from pathlib import Path
from typing import Union, TextIO, BinaryIO
from typeguard import typechecked

from gscrib.types import OptFile
from .base_writer import BaseWriter


class FileWriter(BaseWriter):
    """Writer that outputs commands to a file or file-like object.

    This class implements a G-code writer that can write G-code commands
    to a file. The writer handles both text and binary output modes
    automatically, converting between bytes and strings as needed.

    Example:
        >>> writer = FileWriter("output.gcode")
        >>> writer.write(b"G1 X10 Y10\\n")
        >>> writer.disconnect()
    """

    __slots__ = (
        "_file",
        "_is_terminal",
        "_output"
    )

    @typechecked
    def __init__(self, output: Union[str, TextIO, BinaryIO]):
        """Initialize the file writer.

        Args:
            output (Union[str, TextIO, BinaryIO]): Either a file path
                or a file-like object to write the G-code to.
        """

        self._is_terminal = False
        self._file: OptFile = None
        self._output = output

    def connect(self) -> "FileWriter":
        """Establish the connection to the output file."""

        if self._file is not None:
            return self

        if isinstance(self._output, str):
            file_path = Path(self._output)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            self._file = file_path.open("wb+")
            self._is_terminal = False
        elif hasattr(self._output, "isatty"):
            self._file = self._output
            self._is_terminal = self._file.isatty()
        else:
            self._file = self._output
            self._is_terminal = False

        return self

    def disconnect(self, wait: bool = True) -> None:
        """Close the file if it was opened by this writer."""

        should_close = isinstance(self._output, str)

        if should_close and self._file is not None:
            self._file.close()

        self._file = None

    def write(self, statement: bytes) -> None:
        """Write a G-code statement to the file.

        Args:
            statement (bytes): The G-code statement to write.

        Raises:
            OSError: If an error occurred while writing to the file.
            TypeCheckError: If statement is not bytes-like
        """

        if self._file is None:
            self.connect()

        # We may not be in binary mode if the user provided an open
        # file, so we may need to convert bytes to strings

        if hasattr(self._file, 'encoding'):
            statement_str = statement.decode("utf-8")
            self._file.write(statement_str)
        else:
            self._file.write(statement)

        # Flush only if writing to a terminal

        if self._is_terminal:
            self._file.flush()

    def flush(self) -> None:
        """Flush the output buffer"""

        if self._file is not None:
            self._file.flush()

    def __enter__(self) -> "FileWriter":
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()
