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

import logging
from .base_writer import BaseWriter


class LogWriter(BaseWriter):
    """Writer that outputs commands to Python's logging system.

    This class implements a G-code writer that logs G-code commands
    using Python's logging framework.

    Example:
        >>> writer = LogWriter()
        >>> writer.set_level("info")
        >>> writer.write(b"G1 X10 Y10\\n")
    """

    __slots__ = (
        "_logger",
    )

    def __init__(self):
        """Initialize the logger writer."""

        self._logger = logging.getLogger(__name__)

    def get_logger(self) -> logging.Logger:
        """Get the logger used by this writer.

        Returns:
            logging.Logger: The logger used by this writer.
        """

        return self._logger

    def set_level(self, level: int | str) -> None:
        """Set the logging level for the logger.

        Args:
            level (int | str): The logging level to set.
        """

        if isinstance(level, str):
            level = level.upper()

        self._logger.setLevel(level)


    def connect(self) -> "LogWriter":
        return self

    def disconnect(self, wait: bool = True) -> None:
        pass  # No actual connection to close

    def write(self, statement: bytes) -> None:
        """Write a G-code statement to the default logger.

        Args:
            statement (bytes): The G-code statement to write.
        """

        if not self._logger.handlers:
            logging.basicConfig(level=logging.INFO)

        statement_str = statement.decode("utf-8")
        self._logger.info(statement_str.strip())

    def __enter__(self) -> "LogWriter":
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()
