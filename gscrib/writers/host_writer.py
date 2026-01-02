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

import logging, threading
from gscrib.excepts import DeviceError
from gscrib.excepts import DeviceConnectionError, DeviceWriteError
from gscrib.host import Connection, GCodeHost
from gscrib.host.protocol import DeviceErrorEvent, DeviceFaultEvent
from gscrib.host.protocol import DeviceFeedbackEvent
from gscrib.params import ParamsDict

from .base_writer import BaseWriter


class HostWriter(BaseWriter):
    """Writer that sends commands to a G-code device via serial or network.

    This class implements a G-code writer that connects to a device
    using the GCodeHost asynchronous communication interface. Commands
    are queued asynchronously and executed on the device. Device feedback,
    errors, and faults are monitored and can be queried via parameters.

    Supported URL examples:
        - COM3
        - /dev/ttyUSB0
        - socket://host:port
        - rfc2217://host:port

    Example:
        >>> writer = HostWriter("/dev/ttyUSB0", baudrate=115200)
        >>> writer.write(b"G1 X10 Y10\\n")
        >>> writer.disconnect()
    """

    def __init__(self, url: str, baudrate: int = 9600) -> None:
        """Initialize the host writer.

        Args:
            url (str): Connection URL
            baudrate (int): Baudrate for serial connections

        Raises:
            ValueError: If URL is empty or baudrate is invalid
        """

        if not isinstance(url, str) or url.strip() == "":
            raise ValueError("URL must be specified")

        if not isinstance(baudrate, int) or baudrate < 0:
            raise ValueError("Baudrate must be positive")

        self._logger = logging.getLogger(__name__)
        self._current_params = ParamsDict()
        self._connection = Connection(url, baudrate)
        self._connect_signal = threading.Event()
        self._fault_signal = threading.Event()
        self._sign_commands = False
        self._host = None

    @property
    def is_online(self) -> bool:
        """Check if device is connected and online.

        Returns:
            bool: True if connected and responding
        """

        return self._host and self._host.is_online

    @property
    def sign_commands(self) -> bool:
        """Check if command signing is enabled.

        Returns:
            bool: If line numbers and checksums are enabled
        """

        return self._sign_commands

    @sign_commands.setter
    def sign_commands(self, enabled: bool) -> None:
        """Enable or disable command signing.

        Args:
            enabled (bool): True to add line numbers and checksums
        """

        self._sign_commands = enabled

    def get_parameter(self, name: str) -> float | None:
        """Get the last reading for a device parameter.

        Retrieves the last reported value for a device parameter. These
        parameters are automatically updated when the device sends a
        feedback message. Some firmwares may report parameter readings
        automatically, while others may require specific commands to
        request status updates.

        Common parameters include: X, Y, Z (position), T (tool temperature),
        B (bed temperature), E (extruder position).

        Args:
            name (str): Parameter name (case-insensitive)

        Returns:
            float: Last value read for the parameter or None
        """

        return self._current_params.get(name)

    def connect(self) -> "HostWriter":
        """Establish the connection to the device.

        Returns:
            HostWriter: Self for method chaining

        Raises:
            DeviceConnectionError: If connection cannot be established
        """

        if self._connect_signal.is_set():
            return self

        try:
            self._fault_signal.clear()
            self._connection.open()
            self._host = GCodeHost(self._connection)
            self._host.sign_commands = self._sign_commands
            self._subscribe_to_events(self._host)
            self._host.start()
            self._connect_signal.set()
        except Exception as e:
            raise DeviceConnectionError("Connection failed") from e

        return self

    def disconnect(self, wait: bool = True) -> None:
        """Disconnect from the device and release all resources.

        Args:
            wait (bool): If True, wait for pending commands to be sent
                and acknowledged before disconnecting
        """

        if not self._connect_signal.is_set():
            return

        if wait and not self._fault_signal.is_set():
            self.sync()

        self._host.stop()
        self._unsubscribe_from_events(self._host)
        self._connection.close()
        self._connect_signal.clear()
        self._host = None

    def write(self, statement: bytes) -> None:
        """Send a G-code statement to the device.

        Queues a G-code command for transmission and returns immediately
        without waiting for acknowledgment. The connection is established
        automatically if not already connected.

        Args:
            statement (bytes): The G-code statement to send

        Raises:
            DeviceError: If device is in fault state
            DeviceWriteError: If command cannot be sent
            DeviceConnectionError: If connection cannot be established
            UnicodeDecodeError: If statement is not valid UTF-8
        """

        if self._fault_signal.is_set():
            raise DeviceError("Cannot write: device in fault state")

        if self._host is None:
            self.connect()

        try:
            command = statement.decode("utf-8")
            self._host.enqueue(command)
        except Exception as e:
            raise DeviceWriteError("Cannot write command") from e

    def sync(self) -> None:
        """Block until all queued commands are acknowledged.

        The device sends an acknowledgment after it considers a command
        complete. Depending on the firmware and the specific command, this
        may be sent immediately after the command is queued or only after
        the command has fully executed.

        As a result, this method may return immediately or may block for
        the full execution time of the queued commands.

        Raises:
            DeviceError: If device is in fault state or not connected
        """

        if self._fault_signal.is_set():
            raise DeviceError("Cannot sync: device in fault state")

        if self._host is None:
            raise DeviceError("Cannot sync: device not connected")

        self._host.join_queue()

    def _subscribe_to_events(self, host: GCodeHost) -> None:
        """Subscribe to host events."""

        host.subscribe(DeviceErrorEvent, self._on_device_error)
        host.subscribe(DeviceFaultEvent, self._on_device_fault)
        host.subscribe(DeviceFeedbackEvent, self._on_device_feedback)

    def _unsubscribe_from_events(self, host: GCodeHost) -> None:
        """Unsubscribe from host events."""

        host.unsubscribe(DeviceErrorEvent, self._on_device_error)
        host.unsubscribe(DeviceFaultEvent, self._on_device_fault)
        host.unsubscribe(DeviceFeedbackEvent, self._on_device_feedback)

    def _on_device_feedback(self, event: DeviceFeedbackEvent) -> None:
        """Handle device feedback event."""

        self._logger.debug("Device feedback: %s", event.message)
        self._current_params.update(event.fields)

    def _on_device_error(self, event: DeviceErrorEvent) -> None:
        """Handle device error event."""

        self._logger.error("Device error: %s", event.message)

    def _on_device_fault(self, event: DeviceFaultEvent) -> None:
        """Handle device fault event."""

        self._logger.critical("Device fault: %s", event.message)
        self._fault_signal.set()
        self.disconnect(wait=False)

    def __enter__(self) -> "HostWriter":
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()
