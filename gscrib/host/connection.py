# -*- coding: utf-8 -*-

# Gscrib. Supercharge G-code with Python.
# Copyright (C) 2026 Joan Sala <contact@joansala.com>
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

import serial, time
from serial import SerialException

from .exceptions import HostConnectError
from .exceptions import HostReadError, HostWriteError


class Connection:
    """Unified interface for serial and socket connections.

    Supported URL examples:
        - COM3
        - /dev/ttyUSB0
        - socket://host:port
        - rfc2217://host:port

    Warnings:
        - Enabling DSR/DTR handshaking often triggers a hardware reset
          on microcontrollers (like Arduino/ESP32) because the DTR pin is
          physically wired to the Reset line.
        - RTS/CTS and DSR/DTR settings are only effective on physical
          serial ports or RFC2217 network streams.
    """

    _NEWLINE = b'\n'
    _READ_TIMEOUT = 0.2  # seconds
    _WRITE_TIMEOUT = 10.0  # seconds
    _SETTLE_TIME = 0.1  # seconds
    _BAUDRATE = 9600

    __slots__ = (
        "_url",
        "_backend",
        "_baudrate",
        "_dsrdtr",
        "_rtscts",
        "_rx_buffer",
    )

    def __init__(self, url: str, baudrate: int = _BAUDRATE) -> None:
        """Initialize a Connection instance.

        Args:
            url (str): Connection URL.
            baudrate (int): Only used for serial ports.
        """

        self._url = url
        self._baudrate = baudrate
        self._rx_buffer = bytearray()
        self._rtscts = False
        self._dsrdtr = False
        self._backend = None

    @property
    def is_open(self) -> bool:
        """Check if the connection is currently open."""

        return bool(self._backend and self._backend.is_open)

    @property
    def is_network_transport(self) -> bool:
        """Check if the URL represents a network transport."""

        return self._url.startswith(("socket://", "rfc2217://"))

    @property
    def has_flow_control(self) -> bool:
        """Check if hardware handshake is active."""

        return self._rtscts or self._dsrdtr

    @property
    def can_stream_commands(self) -> bool:
        """Check support for streaming without acknowledgments"""

        return self.is_network_transport or self.has_flow_control

    @property
    def rtscts(self) -> bool:
        """Check if RTS/CTS hardware handshake is enabled."""

        return self._rtscts

    @rtscts.setter
    def rtscts(self, value: bool) -> None:
        """Enable or disable RTS/CTS hardware handshake."""

        self._rtscts = value

        if self._backend:
            self._backend.rtscts = value

    @property
    def dsrdtr(self) -> bool:
        """Check if DSR/DTR hardware flow control is enabled."""

        return self._dsrdtr

    @dsrdtr.setter
    def dsrdtr(self, value: bool) -> None:
        """Enable or disable DSR/DTR hardware flow control."""

        self._dsrdtr = value

        if self._backend:
            self._backend.dsrdtr = value

    def open(self) -> 'Connection':
        """Establish the connection to the device.

        Raises:
            RuntimeError: If the connection is already open.
            HostConnectError: If the connection fails to open.
        """

        if self._backend:
            raise RuntimeError("Connection is already open.")

        try:
            self._backend = serial.serial_for_url(
                url=self._url,
                baudrate=self._baudrate,
                timeout=self._READ_TIMEOUT,
                write_timeout=self._WRITE_TIMEOUT,
                do_not_open=True
            )

            # Standard G-code settings: 8-N-1
            self._backend.parity = serial.PARITY_NONE
            self._backend.rtscts = self._rtscts
            self._backend.dsrdtr = self._dsrdtr

            # Open the connection
            self._backend.open()

            # Flush junk data (electrical noise) from the lines
            self._backend.reset_input_buffer()
            self._backend.reset_output_buffer()
            self._rx_buffer.clear()

            # Small settle time for MCU bootloaders
            time.sleep(self._SETTLE_TIME)
        except (SerialException, OSError) as e:
            self._backend = None
            raise HostConnectError(f"Cannot connect to '{self._url}'") from e

        return self

    def close(self) -> None:
        """Close the connection and release resources."""

        if not self._backend:
            return

        try:
            self._backend.close()
        finally:
            self._backend = None

    def read_line(self, timeout: float = _READ_TIMEOUT) -> str:
        """Read and decode a single line from the device.

        It will wait until a full line (terminated by \\n) is available
        or the read timeout expires. If a timeout occurs before a full
        line is assembled, an empty string  is returned.

        Args:
            timeout (float): Timeout in seconds for the read operation.

        Returns:
            str: Decoded line or an empty string on timeout.

        Raises:
            HostConnectError: If the underlying connection is not open.
            HostReadError: If reading from the device fails.
        """

        self._validate_connection()

        if timeout != self._backend.timeout:
            self._backend.timeout = timeout

        try:
            data = self._buffered_readline()
            if not data: return str()  # Read time out
            return data.decode('ascii', errors='replace').strip()
        except (SerialException, OSError) as e:
            raise HostReadError(f"Read failed: {e}") from e

    def write_line(self, gcode: str, timeout: float = _WRITE_TIMEOUT) -> None:
        """Encode and send a string command to the device.

        Args:
            gcode (str): G-code command string.
            timeout (float): Timeout in seconds for the write operation.

        Raises:
            HostConnectError: If the connection is not open.
            HostWriteError: If the write operation fails.
            UnicodeEncodeError: If gcode contains non-ASCII characters.
        """

        self._validate_connection()

        if timeout != self._backend.write_timeout:
            self._backend.write_timeout = timeout

        try:
            payload = (gcode.strip() + "\n").encode('ascii')
            self._write_payload(payload)
            self._backend.flush()
        except (SerialException, OSError) as e:
            raise HostWriteError(f"Write failed: {e}") from e

    def _validate_connection(self):
        """Ensure the connection is open."""

        if not self._backend or not self._backend.is_open:
            raise HostConnectError("Connection is not open")

    def _write_payload(self, payload: bytes) -> None:
        """Write the full payload to the backend."""

        written_bytes = self._backend.write(payload)

        if written_bytes != len(payload):
            raise HostWriteError("Partial write detected")

    def _buffered_readline(self) -> bytes:
        """Read from the backend and extract a complete line."""

        # Check if a complete line is already in the buffer

        if self._NEWLINE in self._rx_buffer:
            return self._pop_buffered_line()

        # Read available bytes or wait for at least one

        read_size = max(self._backend.in_waiting, 1)
        read_chunk = self._backend.read(read_size)
        if read_chunk: self._rx_buffer.extend(read_chunk)

        # Check again for a complete line in the buffer

        if self._NEWLINE in self._rx_buffer:
            return self._pop_buffered_line()

        return bytes()

    def _pop_buffered_line(self) -> bytes:
        """Extracts the first complete line from the buffer.

        Returns:
            bytes: First complete line or an empty bytes object.
        """

        line, _, remainder = self._rx_buffer.partition(self._NEWLINE)
        self._rx_buffer = bytearray(remainder)
        return bytes(line)
