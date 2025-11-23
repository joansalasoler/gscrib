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

from io import StringIO
from .file_writer import FileWriter


class StringWriter(FileWriter):
    """A writer that outputs G-code to an in-memory string buffer.

    This class allows to generate G-code directly in memory and retrieve
    it as a string. For more advanced string-buffer operations, `FileWriter`
    can be instantiated directly with an `io.StringIO()` object.

    Example:
        >>> writer = StringWriter()
        >>> writer.write(b"G1 X10 Y10\\n")
        >>> print(writer.get_string())
    """

    def __init__(self):
        super().__init__(StringIO())
        self.connect()

    def __str__(self) -> str:
        return self.to_string()

    def to_string(self) -> str:
        """Return a string with the accumulated G-code content.

        Returns:
            str: The G-code content written so far.
        """

        if self._file is None:
            self.connect()

        return self._file.getvalue()
