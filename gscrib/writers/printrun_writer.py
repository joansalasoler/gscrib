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

import logging, time, signal

from gscrib.enums import DirectWrite
from gscrib.printrun import printcore, gcoder
from gscrib.excepts import DeviceError
from gscrib.excepts import DeviceWriteError
from gscrib.excepts import DeviceConnectionError
from gscrib.excepts import DeviceTimeoutError
from .base_writer import BaseWriter


DEFAULT_TIMEOUT = 30.0  # seconds
POLLING_INTERVAL = 0.1  # seconds
SUCCESS_PREFIXES = ('ok',)
ERROR_PREFIXES = ('error', 'alarm', '!!')


class PrintrunWriter(BaseWriter):
    """Writer that sends commands through a serial or socket connection.

    This class implements a G-code writer that connects to a device
    using `printrun` core.
    """

    __slots__ = (
        "_mode",
        "_device",
        "_host",
        "_port",
        "_baudrate",
        "_timeout",
        "_logger",
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

    @property
    def has_pending_operations(self) -> bool:
        """Check if there are pending operations."""

        return self.is_connected and (
            self._device.printing or
            not self._device.clear or
            not self._device.priqueue.empty()
        )

    def set_timeout(self, timeout: float) -> None:
        """Set the timeout for waiting for device operations.

        Args:
            timeout (float): Timeout in seconds.
        """

        if timeout <= 0:
            raise ValueError("Timeout must be positive")

        self._timeout = timeout

    def connect(self) -> "PrintrunWriter":
        """Establish the connection to the device.

        Returns:
            PrintrunWriter: Self for method chaining

        Raises:
            DeviceConnectionError: If connection cannot be established
            DeviceTimeoutError: If connection times out
        """

        if self._shutdown_requested:
            return

        if self.is_connected:
            return self

        try:
            self._device = self._create_device()
            self._device.loud = True
            self._wait_for_connection()
            self._start_print_thread()
        except Exception as e:
            if self._device:
                self._device.disconnect()
                self._device = None

            raise DeviceConnectionError(str(e)) from e

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

        self._logger.info("Disconnect")

        try:
            if wait == True:
                self._wait_for_pending_operations()
        finally:
            if self._device:
                self._device.cancelprint()
                self._device.disconnect()
                self._device = None

        self._logger.info("Disconnect successful")

    def write(self, statement: bytes) -> None:
        """Send a G-code statement through the device connection.

        Args:
            statement (bytes): The G-code statement to send

        Raises:
            DeviceConnectionError: If connection cannot be established
            DeviceTimeoutError: If connection times out
            DeviceWriteError: If write failed
        """

        if self._shutdown_requested:
            return

        if not self.is_connected:
            self.connect()

        try:
            command = statement.decode("utf-8").strip()
            self._logger.info("Send command: %s", command)
            self._device.send(command)
            self._wait_for_acknowledgment()
        except Exception as e:
            raise DeviceWriteError(
                f"Failed to send command: {str(e)}") from e

    def _create_socket_device(self):
        """Create socket connection."""

        socket_url = f"{self._host}:{self._port}"
        self._logger.info("Connect to socket: %s", socket_url)
        return printcore(socket_url, 0)

    def _create_serial_device(self):
        """Create serial connection."""

        self._logger.info("Connect to serial: %s", self._port)
        return printcore(self._port, self._baudrate)

    def _create_device(self):
        """Create serial or socket connection."""

        return (
            self._create_socket_device()
            if self._mode == DirectWrite.SOCKET
            else self._create_serial_device()
        )

    def _start_print_thread(self) -> None:
        """Starts the print process in a separate thread.

        This initiates the print operation using a dedicated thread to
        improve reliability. It enables features like line numbering,
        checksums, resends, acknowledgment-based flow control, etc.
        """

        if self.is_connected and not self.is_printing:
            self._device.startprint(gcoder.GCode([]))
            self._logger.info("Print thread started")

    def _wait_for_pending_operations(self) -> None:
        """Wait for pending operations to complete.

        Raises:
            DeviceConnectionError: Shutdown requested or connection
                is lost while waiting
        """

        self._logger.info("Wait for pending operations")

        while self.has_pending_operations:
            if self._shutdown_requested:
                raise DeviceConnectionError("Shutdown requested")

            if not self.is_connected:
                raise DeviceConnectionError("Connection lost")

            time.sleep(POLLING_INTERVAL)

        self._logger.info("Pending operations completed")

    def _wait_for_connection(self) -> None:
        """Wait for the connection to be established.

        Raises:
            DeviceConnectionError: Shutdown requested while waiting
            DeviceTimeoutError: Connection not established within timeout
        """

        self._logger.info("Wait for device connection")
        start_time = time.time()

        while not self.is_connected:
            if self._shutdown_requested:
                raise DeviceConnectionError("Shutdown requested")

            if time.time() - start_time > self._timeout:
                raise DeviceTimeoutError(f"Operation timed out")

            time.sleep(POLLING_INTERVAL)

        self._logger.info("Device connected")

    def _wait_for_acknowledgment(self) -> None:
        """Wait until machine responds with acknowledgment or error.

        Raises:
            DeviceConnectionError: Shutdown requested while waiting
            DeviceTimeoutError: Response not received within timeout
            DeviceError: If device replied with an error
        """

        self._logger.info("Wait for acknowledgment")
        original_callback = self._device.recvcb
        response = []

        def receive_callback(line):
            message = line.strip().lower()

            if message.startswith(SUCCESS_PREFIXES):
                response.append(message)
            elif message.startswith(ERROR_PREFIXES):
                response.append(message)

        try:
            self._device.recvcb = receive_callback

            while not len(response):
                if self._shutdown_requested:
                    raise DeviceConnectionError("Shutdown requested")

                time.sleep(POLLING_INTERVAL)

            message = response[0] if len(response) else "None"
            self._logger.info(f"Acknowledgment: {message}")

            if message.startswith(ERROR_PREFIXES):
                raise DeviceError(message)
        finally:
            self._device.recvcb = original_callback

    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals by disconnecting cleanly."""

        try:
            self._logger.info("Shutdown requested")
            self._shutdown_requested = True
            self.disconnect(False)
        except Exception as e:
            self._logger.exception("Error during shutdown: %s", e)

    def __enter__(self) -> "PrintrunWriter":
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()
