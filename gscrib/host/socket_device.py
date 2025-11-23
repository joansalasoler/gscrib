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

import socket, ipaddress
from typeguard import typechecked
from typing import Optional

from gscrib.excepts import DeviceError
from .base_device import BaseDevice, READ_EOF


class SocketDevice(BaseDevice):
    """Network socket device communication."""

    __slots__ = ("_hostname", "_port_number", "_socketfile", "_is_connected", "_timeout")

    @typechecked
    def __init__(self, port: Optional[str] = None, baudrate: int = 9600) -> None:
        super().__init__(port, baudrate)
        self._hostname = None
        self._port_number = None
        self._socketfile = None
        self._is_connected = False
        self._timeout = 0.25

    @typechecked
    def connect(self, port: Optional[str] = None, baudrate: Optional[int] = None) -> None:
        """Establish socket connection."""
        if port:
            self._port = port

        if not self._port:
            raise DeviceError("No address specified")

        if not self._parse_network_address(self._port):
            raise DeviceError(f"Invalid network address: {self._port}")

        self._device = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._device.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self._device.settimeout(self._timeout)

        try:
            self._device.connect((self._hostname, self._port_number))
            self._socketfile = self._device.makefile('rb')
            self._is_connected = True
        except OSError as e:
            self._cleanup_resources()
            address = f"{self._hostname}:{self._port_number}"
            self._logger.error(f"Socket connection failed: {address}")
            raise DeviceError(f"Cannot connect to {address}") from e

    def disconnect(self) -> None:
        """Close socket connection."""
        self._is_connected = False
        try:
            self._cleanup_resources()
        except Exception:
            pass
        finally:
            self._device = None

    def _check_connection_status(self) -> bool:
        """Check if socket connection is active."""
        return self._is_connected

    def _read_line(self):
        """Read line from socket."""
        try:
            line = self._socketfile.readline()
            if not line:
                self._is_connected = False
                return READ_EOF
            return line
        except OSError as e:
            self._is_connected = False
            address = f"{self._hostname}:{self._port_number}"
            self._logger.error(f"Socket read error: {address}")
            raise DeviceError(f"Cannot read from {address}") from e

    def _write_data(self, data: bytes) -> None:
        """Write data to socket."""
        try:
            self._device.sendall(data)
        except (OSError, RuntimeError) as e:
            self._is_connected = False
            address = f"{self._hostname}:{self._port_number}"
            self._logger.error(f"Socket write error: {address}")
            raise DeviceError(f"Cannot write to {address}") from e

    def _parse_network_address(self, address: str) -> bool:
        """Parse and validate network address (host:port)."""
        if ':' not in address:
            return False

        try:
            host, port = address.split(':', 1)
            port_num = int(port)

            if not (1 <= port_num <= 65535):
                return False

            if self._is_valid_hostname(host):
                self._hostname = host
                self._port_number = port_num
                return True
        except ValueError:
            pass

        return False

    def _is_valid_hostname(self, hostname: str) -> bool:
        """Validate hostname or IP address."""
        try:
            ipaddress.ip_address(hostname)
            return True
        except ValueError:
            pass

        try:
            socket.getaddrinfo(hostname, None)
            return True
        except (socket.gaierror, UnicodeError):
            return False

    def _cleanup_resources(self) -> None:
        """Clean up socket resources."""
        if self._socketfile:
            try:
                self._socketfile.close()
            except Exception:
                pass
            self._socketfile = None

        if self._device:
            try:
                self._device.close()
            except Exception:
                pass