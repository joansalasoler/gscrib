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

from vpype_mecode.builder.enums import DirectWrite
from .printrun_writer import PrintrunWriter
from .base_writer import BaseWriter


class SocketWriter(BaseWriter):
    """Writer that sends commands through a network socket connection.

    This class implements a G-code writer that connects to a device
    through a TCP/IP socket and sends G-code commands to it.

    Example:
        >>> writer = SocketWriter("localhost", 8000)
        >>> writer.write(b"G1 X10 Y10\\n")
        >>> writer.disconnect()
    """

    def __init__(self, host: str, port: int):
        """Initialize the socket writer.

        Args:
            host (str): The hostname or IP address of the remote machine.
            port (int): The TCP port number to connect to.
        """

        if not host:
            raise ValueError("Host must be specified")

        if not isinstance(port, int) or port <= 0 or port > 65535:
            raise ValueError("Port number is not valid.")

        self._writer_delegate = PrintrunWriter(
            mode=DirectWrite.SOCKET,
            host=host,
            port=str(port),
            baudrate=0
        )

    @property
    def is_connected(self) -> bool:
        """Check if device is currently connected."""
        return self._writer_delegate.is_connected

    @property
    def is_printing(self) -> bool:
        """Check if the device is currently printing."""
        return self._writer_delegate.is_printing

    def set_timeout(self, timeout: float) -> None:
        """Set the timeout for waiting for device operations.

        Args:
            timeout (float): Timeout in seconds.
        """

        self._writer_delegate.set_timeout(timeout)

    def connect(self) -> "SocketWriter":
        """Establish the socket connection to the device.

        Creates a `printcore` object with the configured host and
        port, and waits for the connection to be established.

        Returns:
            SocketWriter: Self for method chaining

        Raises:
            DeviceConnectionError: If connection cannot be established
            DeviceTimeoutError: If connection times out
        """

        return self._writer_delegate.connect()

    def disconnect(self, wait: bool = True) -> None:
        """Close the socket connection if it exists.

        Args:
            wait: If True, waits for pending operations to complete

        Raises:
            DeviceTimeoutError: If waiting times out
        """

        self._writer_delegate.disconnect()

    def write(self, statement: bytes) -> None:
        """Send a G-code statement through the socket connection.

        Args:
            statement (bytes): The G-code statement to send

        Raises:
            DeviceConnectionError: If connection cannot be established
        """

        self._writer_delegate.write(statement)

    def __enter__(self) -> "SocketWriter":
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()
