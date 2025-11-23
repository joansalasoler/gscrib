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

import platform, serial, subprocess
from typeguard import typechecked
from typing import Optional

from gscrib.excepts import DeviceError
from .base_device import BaseDevice


class SerialDevice(BaseDevice):
    """Serial port device communication."""

    @typechecked
    def connect(self, port: Optional[str] = None, baudrate: Optional[int] = None) -> None:
        """Establish serial connection."""

        self._port = port
        self._baudrate = baudrate

        if not self._port:
            raise DeviceError("No port specified")

        self._configure_serial_port()

        try:
            self._device = serial.Serial(
                port=self._port,
                baudrate=self._baudrate,
                timeout=0.25,
                parity=serial.PARITY_NONE
            )
        except (serial.SerialException, IOError) as e:
            self._logger.error(f"Serial connection failed: {self._port}")
            raise DeviceError(f"Cannot connect to serial port '{self._port}'") from e

    def disconnect(self) -> None:
        """Close serial connection."""
        if self._device:
            try:
                self._device.close()
            except Exception:
                pass
            finally:
                self._device = None

    def _check_connection_status(self) -> bool:
        """Check if serial connection is active."""
        return self._device.is_open

    def _read_line(self):
        """Read line from serial port."""
        try:
            return self._device.readline()
        except (serial.SerialException, OSError) as e:
            self._logger.error(f"Serial read error: {self._port}")
            raise DeviceError(f"Cannot read from serial port '{self._port}'") from e

    def _write_data(self, data: bytes) -> None:
        """Write data to serial port."""
        try:
            self._device.write(data)
        except serial.SerialException as e:
            self._logger.error(f"Serial write error: {self._port}")
            raise DeviceError(f"Cannot write to serial port '{self._port}'") from e

    def _configure_serial_port(self) -> None:
        """Configure serial port settings for Linux."""
        if platform.system() == "Linux":
            try:
                subprocess.run(["stty", "-F", self._port, "-hup"],
                             check=True, capture_output=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass