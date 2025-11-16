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

import re
import threading
import logging
import time
import signal

from gscrib.enums import DirectWrite
from gscrib.printrun import printcore, gcoder
from gscrib.excepts import GscribError
from gscrib.excepts import DeviceError
from gscrib.excepts import DeviceWriteError
from gscrib.excepts import DeviceConnectionError
from gscrib.excepts import DeviceTimeoutError
from gscrib.params import ParamsDict

from .base_writer import BaseWriter


DEFAULT_TIMEOUT = 30.0  # seconds
POLLING_INTERVAL = 0.1  # seconds
SUCCESS_PREFIXES = ("ok",)
ERROR_PREFIXES = ("error", "alarm", "!!")
AXES = ("X", "Y", "Z", "A", "B", "C")
VALUE_PATTERN = re.compile(r"([A-Za-z0-9]+):(-?\d+(?:\.\d+)?(?:,-?\d+(?:\.\d+)?)*)")

class PrintrunWriter(BaseWriter):
    """Writer that sends commands through a serial or socket connection.

    This class implements a G-code writer that connects to a device
    using `printrun` core.
    """

    def __init__(self, mode: DirectWrite | str, host: str, port: str, baudrate: int):
        """Initialize the printrun writer.

        Args:
            mode (DirectWrite | str): Connection mode (socket or serial).
            host (str): The hostname or IP address of the remote machine.
            port (int): The TCP or serial port identifier
            baudrate (int): Communication speed in bauds
        """

        if not isinstance(host, str) or host.strip() == "":
            raise ValueError("Host must be specified")

        if not isinstance(port, str) or port.strip() == "":
            raise ValueError("Port must be specified")

        if not isinstance(baudrate, int) or baudrate < 0:
            raise ValueError("Baudrate must be positive")

        self._mode = DirectWrite(mode)
        self._device = None
        self._host = host
        self._port = port
        self._baudrate = baudrate
        self._timeout = DEFAULT_TIMEOUT
        self._device_error = None
        self._shutdown_requested = False
        self._reported_params = set()
        self._current_params = ParamsDict()
        self._logger = logging.getLogger(__name__)
        self._setup_device_events()
        self._setup_signal_handlers()

    def _setup_device_events(self):
        """Set up device synchronization events."""

        self._ack_event = threading.Event()
        self._online_event = threading.Event()

    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""

        signal.signal(signal.SIGTERM, self._on_shutdown_signal)
        signal.signal(signal.SIGINT, self._on_shutdown_signal)

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
            self._device.printing
            or not self._device.clear
            or not self._device.priqueue.empty()
        )

    def get_parameter(self, name: str) -> float:
        """Get the last reading for a parameter by name.

        This method retrieves the last reported value for a device
        parameter. These parameters are stored and updated each time
        the device reports a new value for them.

        Args:
            name (str): Name of the parameter (case-insensitive)

        Returns:
            float: Last value read for the parameter or None
        """

        return self._current_params.get(name)

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
            self._device_error = None
            self._device = self._create_device()
            self._connect_device(self._device)
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
            if wait:
                self._wait_for_pending_operations()
        finally:
            if self._device:
                self._device.cancelprint()
                self._device.disconnect()
                self._online_event.clear()
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
            self._send_statement(statement)
            self._wait_for_acknowledgment()
        except Exception as e:
            raise DeviceWriteError(f"Failed to send command: {str(e)}") from e

        self._abort_on_device_error()

    def _create_device(self):
        """Create serial or socket connection."""

        device = printcore()
        device.loud = True
        device.onlinecb = lambda: self._on_device_online()
        device.errorcb = lambda error: self._on_printrun_error(error)
        device.recvcb = lambda line: self._on_device_message(line)

        return device

    def _connect_device(self, device: printcore) -> None:
        """Connect to the device."""

        self._online_event.clear()

        if self._mode == DirectWrite.SOCKET:
            socket_url = f"{self._host}:{self._port}"
            self._logger.info("Connect to socket: %s", socket_url)
            device.connect(socket_url, 0)
        else:
            self._logger.info("Connect to serial: %s", self._port)
            device.connect(self._port, self._baudrate)

    def _start_print_thread(self) -> None:
        """Starts the print process in a separate thread.

        This initiates the print operation using a dedicated thread to
        improve reliability. It enables features like line numbering,
        checksums, resends, acknowledgment-based flow control, etc.
        """

        if self.is_connected and not self.is_printing:
            self._logger.info("Starting print thread")
            self._device.startprint(gcoder.GCode([]))
            self._wait_for_pending_operations()

    def _send_statement(self, statement: bytes) -> None:
        """Send a command to the device."""

        command = statement.decode("utf-8").strip()
        self._logger.info("Send command: %s", command)

        self._ack_event.clear()
        self._device.send(command)

    def _wait_for_connection(self) -> None:
        """Wait for the connection to be established.

        Raises:
            DeviceError: If device reported an error
            DeviceConnectionError: Shutdown requested or connection lost
            DeviceTimeoutError: Connection not established within timeout
        """

        self._logger.info("Wait for device connection")

        if self._device.printer is None:
            raise DeviceConnectionError("Could not connect to device")

        if not self._online_event.wait(timeout=self._timeout):
            raise DeviceTimeoutError("Connection timed out")

        self._abort_on_device_error()
        self._logger.info("Device connected")

    def _wait_for_pending_operations(self) -> None:
        """Wait for pending operations to complete.

        Raises:
            DeviceError: If device reported an error
            DeviceConnectionError: Shutdown requested or connection lost
        """

        self._logger.info("Wait for pending operations")

        while self.has_pending_operations:
            self._abort_on_device_error()
            time.sleep(POLLING_INTERVAL)

        self._logger.info("Pending operations completed")

    def _wait_for_acknowledgment(self) -> None:
        """Wait for an acknowledgment from the device."""

        self._logger.info("Wait for acknowledgment")
        self._ack_event.wait()

    def _on_device_online(self) -> None:
        """Callback to handle device online event."""

        self._logger.info("Device online")
        self._online_event.set()

    def _on_printrun_error(self, message: str) -> None:
        """Callback to handle errors reported by printrun."""

        self._logger.error("Error: %s", message)
        self._device_error = DeviceError(message)
        self._ack_event.set()

    def _on_device_message(self, message: str) -> None:
        """Callback to handle messages from the device."""

        try:
            message = message.strip()
            lower_message = message.lower()

            self._logger.debug("Device message: %s", message)

            if lower_message.startswith(SUCCESS_PREFIXES):
                self._ack_event.set()
                return
            elif lower_message.startswith(ERROR_PREFIXES):
                error_message = self._format_error(message)
                self._device_error = DeviceError(error_message)
                self._ack_event.set()
                return

            self._parse_message(message)
        except Exception as e:
            self._logger.exception("Cannot process message: %s", message)
            self._device_error = GscribError(f"Internal error: {str(e)}")

    def _on_shutdown_signal(self, signum, frame):
        """Handle shutdown signals by disconnecting cleanly."""

        try:
            self._logger.info("Shutdown requested")
            self._shutdown_requested = True
            self._online_event.set()
            self._ack_event.set()
            self.disconnect(False)
        except DeviceError:
            raise
        except Exception as e:
            message = f"Error during shutdown: {str(e)}"
            self._logger.exception(message)
            raise GscribError(message) from e
        finally:
            self._online_event.set()
            self._ack_event.set()

    def _abort_on_device_error(self) -> None:
        """Check for errors in the device state.

        Raises:
            DeviceError: If device reported an error
            DeviceConnectionError: If shutdown is requested
            DeviceConnectionError: If connection is lost
        """

        if self._device_error is not None:
            exception = self._device_error
            self._device_error = None
            raise exception

        if not self.is_connected:
            raise DeviceConnectionError("Connection lost")

        if self._shutdown_requested:
            raise DeviceConnectionError("Shutdown requested")

    def _parse_message(self, message: str) -> None:
        """Extract paramter readings from a device message."""

        self._reported_params.clear()

        for key, value in VALUE_PATTERN.findall(message):
            try:
                if len(key) == 1 and key.isalnum():
                    self._update_param(key, float(value))
                elif key == "FS" and message.startswith("<"):
                    feed, speed = value.split(",")
                    self._update_param("F", float(feed))
                    self._update_param("S", float(speed))
                elif key in ("MPos", "WPos", "PRB"):
                    coords = map(float, value.split(","))

                    for axis, coord in zip(AXES, coords):
                        self._update_param(axis, coord)
            except Exception as e:
                self._logger.exception("Error parsing value: %s", e)

    def _update_param(self, key: str, value: float) -> None:
        """Update a parameter value if it hasn't been processed."""

        if key not in self._reported_params:
            self._reported_params.add(key)
            self._current_params[key] = value
            self._logger.debug("Set '%s' to %s", key, value)

    def _format_error(self, message: str) -> str:
        """Format an error message from the device.

        Override this method to customize error formatting. This is
        useful for translating or modifying error messages received from
        the device to be more user-friendly.

        Args:
            message (str): The error message from the device.

        Returns:
            str: Formatted error message.
        """

        return message

    def __enter__(self) -> "PrintrunWriter":
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()
