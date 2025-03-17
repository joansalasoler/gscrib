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

from typing import Union, TextIO, BinaryIO

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

    def __init__(self, output: Union[str, TextIO, BinaryIO]):
        """Initialize the file writer.

        Args:
            output (Union[str, TextIO, BinaryIO]): Either a file path
                or a file-like object to write the G-code to.
        """

        self._output = output
        self._file = None

    def connect(self) -> None:
        """Establish the connection to the output file."""

        self._file = self._output

        if isinstance(self._output, str):
            self._file = open(self._output, "wb+")

    def disconnect(self, wait: bool = True) -> None:
        """Close the file if it was opened by this writer."""

        should_close = isinstance(self._output, str)

        if should_close and self._file is not None:
            self._file.close()
            self._file = None

    def write(self, statement: bytes, requires_response: bool = False) -> None:
        """Write a G-code statement to the file.

        Args:
            statement (bytes): The G-code statement to write.
        """

        if self._file is None:
            self.connect()

        if hasattr(self._file, 'encoding'):
            statement = statement.decode("utf-8")

        self._file.write(statement)

        if hasattr(self._file, 'flush'):
            self._file.flush()

        return None
