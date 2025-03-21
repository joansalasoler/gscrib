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

import logging, time, signal

from vpype_mecode.builder.enums import DirectWrite
from vpype_mecode.builder.printrun import printcore
from vpype_mecode.builder.excepts import DeviceConnectionError
from vpype_mecode.builder.excepts import DeviceTimeoutError
from .base_writer import BaseWriter


DEFAULT_TIMEOUT = 30.0  # seconds
POLLING_INTERVAL = 0.1  # seconds


class PrintrunWriter(BaseWriter):
    """Writer that sends commands through a serial or socket connection.

    This class implements a G-code writer that connects to a device
    using `printrun` core.
    """

    __slots__ = (
        "_logger",
        "_mode",
        "_device",
        "_timeout",
        "_baudrate",
        "_host",
        "_port",
        "_shutdown_requested"
    )

    def __init__(self, mode: DirectWrite, host: str, port: str, baudrate: int):
        """Initialize the printrun writer.

        Args:
            mode (DirectWrite): Connection mode (socket or serial).
            host (str): The hostname or IP address of the remote machine.
            port (int): The TCP or serial port identifier
            baudrate (int): Communication speed in bauds
        """


        self._mode = mode
        self._device = None
        self._host = host
        self._port = port
        self._baudrate = baudrate
        self._timeout = DEFAULT_TIMEOUT
        self._logger = logging.getLogger(__name__)
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""

        self._shutdown_requested = False
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

    @property
    def is_connected(self) -> bool:
        """Check if device is currently connected."""
        return self._device is not None and self._device.online

    @property
    def is_printing(self) -> bool:
        """Check if the device is currently printing."""
        return self.is_connected and self._device.printing

    def set_timeout(self, timeout: float) -> None:
        """Set the timeout for waiting for device operations.

        Args:
            timeout (float): Timeout in seconds.
        """

        self._timeout = timeout

    def connect(self) -> "PrintrunWriter":
        """Establish the connection to the device.

        Returns:
            PrintrunWriter: Self for method chaining

        Raises:
            DeviceConnectionError: If connection cannot be established
            DeviceTimeoutError: If connection times out
        """

        if self.is_connected:
            return self

        if self._shutdown_requested:
            return self

        try:
            self._device = self._create_device()
            wait_condition = lambda: self._device.online
            self._wait_for(wait_condition)
        except Exception as e:
            if self._device:
                self._device.disconnect()
                self._device = None

            raise DeviceConnectionError(
                f"Failed to connect: {str(e)}") from e

        return self

    def disconnect(self, wait: bool = True) -> None:
        """Close the connection if it exists.

        Args:
            wait: If True, waits for pending operations to complete

        Raises:
            DeviceTimeoutError: If waiting times out
        """

        if self._device is None:
            return

        self._logger.info(f"Disconnect from {self._mode.value}")

        try:
            if wait and self._device.printing:
                wait_condition = lambda: not self._device.printing
                self._wait_for(wait_condition)
        finally:
            self._device.disconnect()
            self._device = None

    def write(self, statement: bytes, wait: bool = False) -> str | None:
        """Send a G-code statement through the device connection.

        Args:
            statement (bytes): The G-code statement to send
            wait (bool): Whether to wait for response

        Returns:
            Optional[str]: Response from the device if wait is True

        Raises:
            DeviceConnectionError: If connection cannot be established
        """

        if not self.is_connected:
            self.connect()

        command = statement.decode("utf-8").strip()
        self._logger.debug(f"Send to {self._mode.value}: {command}")

        if not wait:
            self._device.send(command)
            return None

        try:
            responses = []
            wait_condition = lambda: bool(responses)

            def response_callback(line: str):
                if line.strip(): # Ignore empty lines
                    self._on_response_received(line)
                    responses.append(line)

            self._device.recvcb = response_callback
            self._device.send(command)

            self._logger.debug("Wait for response")
            self._wait_for(wait_condition, check_connection=True)

            if len(responses) > 0:
                return responses[0]
        except DeviceTimeoutError:
            self._logger.warning("Timeout waiting for response")
        finally:
            self._device.recvcb = None

        return None

    def _create_socket_device(self):
        """Create socket connection."""

        socket_url = f"{self._host}:{self._port}"
        self._logger.info(f"Connect to socket: {socket_url}")
        return printcore(socket_url, 0)

    def _create_serial_device(self):
        """Create serial connection."""

        self._logger.info(f"Connect to serial: {self._port}")
        return printcore(self._port, self._baudrate)

    def _create_device(self):
        """Create serial or socket connection."""

        return (
            self._create_socket_device()
            if self._mode == DirectWrite.SOCKET
            else self._create_serial_device()
        )

    def _wait_for(self, condition: callable, check_connection: bool = False) -> None:
        """Wait for a condition to be met with timeout.

        Args:
            condition: Function that returns True when condition is met
            check_connection: Fail if device is disconnected

        Raises:
            DeviceConnectionError: If connection is lost while waiting
            DeviceTimeoutError: If condition is not met within timeout
        """

        start_time = time.time()

        while not condition():
            if self._shutdown_requested:
                raise DeviceConnectionError("Shutdown requested")

            if check_connection and not self.is_connected:
                raise DeviceConnectionError("Connection lost")

            if time.time() - start_time > self._timeout:
                raise DeviceTimeoutError(f"Operation timed out")

            time.sleep(POLLING_INTERVAL)

    def _on_response_received(self, line: str) -> str:
        """Invoked when a response was received"""

    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals by disconnecting cleanly."""

        try:
            self._shutdown_requested = True
            self.disconnect(wait=True)
        except Exception as e:
            self._logger.error(f"Error during shutdown: {e}")

    def __enter__(self) -> "PrintrunWriter":
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()
