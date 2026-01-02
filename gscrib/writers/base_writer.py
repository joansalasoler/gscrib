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

from abc import ABC, abstractmethod


class BaseWriter(ABC):
    """Base class for all the G-code writing implementations.

    This class defines the interface for writing G-code commands to
    various outputs, such as files, serial connections, or network sockets.

    Subclasses should implement connect(), disconnect(), and write()
    methods. The flush() method has a default no-op implementation but
    can be overridden for outputs that support buffering.
    """

    @abstractmethod
    def connect(self) -> "BaseWriter":
        """Establish connection or open resource for writing.

        Returns:
            BaseWriter: Self for method chaining
        """

    @abstractmethod
    def disconnect(self, wait: bool = True) -> None:
        """Close connection or resource.

        Args:
            wait (bool): If True, wait for pending operations to complete
        """

    @abstractmethod
    def write(self, statement: bytes) -> None:
        """Write G-code statement.

        Args:
            statement (bytes): The G-code statement to write
        """

    def flush(self) -> None:
        """Flush the output buffer."""
