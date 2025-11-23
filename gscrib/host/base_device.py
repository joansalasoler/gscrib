# -*- coding: utf-8 -*-

# Gscrib. Supercharge G-code with Python.
# Portions of this file are derived from Printrun.
# Copyright (C) 2025 Joan Sala <contact@joansala.com>
# Copyright (C) 2011-2024 Kliment Yanev, Guillaume Seguin, et al.
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
from typing import Optional
from typeguard import typechecked
from gscrib.excepts import DeviceError

READ_EOF = None   # End-of-file
READ_EMPTY = b''  # Empty or no data


class BaseDevice:
    """Base class for device communication."""

    __slots__ = ("_logger", "_port", "_baudrate", "_device")

    @typechecked
    def __init__(self, port: Optional[str] = None, baudrate: int = 9600) -> None:
        self._logger = logging.getLogger(__name__)
        self._port = port
        self._baudrate = baudrate
        self._device = None

    def __del__(self) -> None:
        """Ensure connections are closed when object is destroyed."""
        try:
            self.disconnect()
        except Exception:
            pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure cleanup."""
        self.disconnect()

    @property
    def is_connected(self) -> bool:
        """True if device connection is active."""
        return self._device is not None and self._check_connection_status()

    def readline(self):
        """Read one line from device."""
        if not self._device:
            raise DeviceError("Cannot read: device not connected")
        return self._read_line()

    @typechecked
    def write(self, data: bytes) -> None:
        """Write data to device."""
        if not self._device:
            raise DeviceError("Cannot write: device not connected")
        self._write_data(data)

    # Abstract methods to be implemented by subclasses
    def connect(self, port: Optional[str] = None, baudrate: Optional[int] = None) -> None:
        """Establish connection to device."""
        raise NotImplementedError

    def disconnect(self) -> None:
        """Close connection and cleanup resources."""
        raise NotImplementedError

    def _check_connection_status(self) -> bool:
        """Check if connection is still active."""
        raise NotImplementedError

    def _read_line(self):
        """Read line from device."""
        raise NotImplementedError

    def _write_data(self, data: bytes) -> None:
        """Write data to device."""
        raise NotImplementedError

    @staticmethod
    def create(port: Optional[str] = None, baudrate: int = 9600):
        """Create appropriate device instance based on port type."""
        from .socket_device import SocketDevice
        from .serial_device import SerialDevice

        if port and ':' in port:
            # Try to create socket device, fall back to serial if invalid
            socket_dev = SocketDevice(port, baudrate)
            if socket_dev._parse_network_address(port):
                return socket_dev
        return SerialDevice(port, baudrate)