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

from gscrib.enums import DirectWrite
from .printrun_writer import PrintrunWriter
from .base_writer import BaseWriter


class SerialWriter(BaseWriter):
    """Writer that sends commands through a serial connection.

    This class implements a G-code writer that connects to a device
    through a serial port and sends G-code commands to it.

    Example:
        >>> writer = SerialWriter("/dev/ttyUSB0", 115200)
        >>> writer.write(b"G1 X10 Y10\\n")
        >>> writer.disconnect()
    """

    def __init__(self, port: str, baudrate: int):
        """Initialize the serial writer.

        Args:
            port (str): Serial port identifier
            baudrate (int): Communication speed in bauds
        """

        if not isinstance(baudrate, int) or baudrate <= 0:
            raise ValueError("Baudrate must be positive")

        self._writer_delegate = PrintrunWriter(
            mode=DirectWrite.SERIAL,
            host='localhost',
            port=port,
            baudrate=baudrate,
        )

    @property
    def is_connected(self) -> bool: # pragma: no cover
        """Check if device is currently connected."""
        return self._writer_delegate.is_connected

    @property
    def is_printing(self) -> bool: # pragma: no cover
        """Check if the device is currently printing."""
        return self._writer_delegate.is_printing

    def get_parameter(self, name: str) -> float: # pragma: no cover
        """Get the last reading for a parameter by name.

        This method retrieves the last reported value for a device
        parameter. These parameters are stored and updated each time
        the device reports a new value for them.

        Args:
            name (str): Name of the parameter (case-insensitive)

        Returns:
            float: Last value read for the parameter or None
        """

        return self._writer_delegate.get_parameter(name)

    def set_timeout(self, timeout: float) -> None: # pragma: no cover
        """Set the timeout for waiting for device operations.

        Args:
            timeout (float): Timeout in seconds.
        """

        self._writer_delegate.set_timeout(timeout)

    def connect(self) -> "SerialWriter": # pragma: no cover
        """Establish the serial connection to the device.

        Creates a `printcore` object with the configured port and
        baudrate, and waits for the connection to be established.

        Returns:
            SerialWriter: Self for method chaining

        Raises:
            DeviceConnectionError: If connection cannot be established
            DeviceTimeoutError: If connection times out
        """

        return self._writer_delegate.connect()

    def disconnect(self, wait: bool = True) -> None: # pragma: no cover
        """Close the serial connection if it exists.

        Args:
            wait: If True, waits for pending operations to complete

        Raises:
            DeviceTimeoutError: If waiting times out
        """

        self._writer_delegate.disconnect()

    def write(self, statement: bytes) -> None: # pragma: no cover
        """Send a G-code statement through the serial connection.

        Args:
            statement (bytes): The G-code statement to send

        Raises:
            DeviceConnectionError: If connection cannot be established
        """

        self._writer_delegate.write(statement)

    def __enter__(self) -> "SerialWriter":
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()
