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
from logging import Logger
from .base_writer import BaseWriter


class LogWriter(BaseWriter):
    """Writer that outputs commands to Python's logging system.

    This class implements a G-code writer that logs G-code commands
    using Python's logging framework. Useful for debugging, monitoring,
    or integrating with logging infrastructure.

    Example:
        >>> writer = LogWriter()
        >>> writer.set_level("debug")
        >>> writer.write(b"G1 X10 Y10\\n")
    """

    __slots__ = (
        "_logger",
        "_level",
    )

    def __init__(self):
        """Initialize the logger writer."""

        self._logger = logging.getLogger(f"{__name__}.{id(self)}")
        self._level = logging.INFO

    def get_logger(self) -> Logger:
        """Get the logger used by this writer.

        Returns:
            Logger: The logger instance used by this writer
        """

        return self._logger

    def set_level(self, level: int | str) -> None:
        """Set the logging level for statements.

        Args:
            level (int | str): The logging level to set.

        Raises:
            ValueError: If the level is not a valid logging level
        """

        try:
            if isinstance(level, str):
                name = level.upper()
                level = getattr(logging, name)
        except AttributeError as e:
            raise ValueError("Invalid logging level string") from e

        self._level = level

    def connect(self) -> "LogWriter":
        """Establish the connection (no-op for logging).

        Returns:
            LogWriter: Self for method chaining
        """

        return self

    def disconnect(self, wait: bool = True) -> None:
        """Close the connection (no-op for logging).

        Args:
            wait (bool): Ignored for logging writer
        """

    def write(self, statement: bytes) -> None:
        """Write to the logger at the configured level.

        Args:
            statement (bytes): The G-code statement to write
        """

        statement_str = statement.decode("utf-8")
        self._logger.log(self._level, statement_str.strip())

    def flush(self) -> None:
        """Flush all attached logger handlers."""

        for handler in self._logger.handlers:
            handler.flush()

    def __enter__(self) -> "LogWriter":
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()
