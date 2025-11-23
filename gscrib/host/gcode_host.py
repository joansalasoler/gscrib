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

import threading, logging, traceback
from queue import Queue, Empty as QueueEmpty
from typeguard import typechecked
from typing import Optional

from gscrib.excepts import DeviceError
from .base_device import BaseDevice


class GCodeHost:
    """Core 3D printer host functionality.

    Provides connection management, command queuing, and communication
    with 3D printers and CNC machines via serial or network connections.

    Attributes:
        Connection state: _connected, _device, _port, _baud
        Processing state: _ready, _busy, _command_queue
        Threading: _read_thread, _send_thread, stop flags
        Callbacks: _message_callback, _error_callback, _connect_callback
    """

    __slots__ = (
        "_logger", "_baud", "_port", "_device", "_lock",
        "_ready", "_connected", "_busy", "_command_queue",
        "_message_callback", "_error_callback", "_connect_callback",
        "_read_thread", "_send_thread", "_stop_event",
    )

    @typechecked
    def __init__(self, port: Optional[str] = None, baud: Optional[int] = None) -> None:
        self._logger = logging.getLogger(__name__)
        self._lock = threading.RLock()

        # Connection parameters
        self._port = port
        self._baud = baud
        self._device = None

        # State management
        self._connected = False
        self._ready = True
        self._busy = False
        self._command_queue = Queue(0)

        # Event callbacks
        self._message_callback = None
        self._error_callback = None
        self._connect_callback = None

        # Threading control
        self._read_thread = None
        self._send_thread = None
        self._stop_event = threading.Event()

        # Auto-connect if both parameters provided
        if port and baud:
            self.connect(port, baud)

    def __del__(self) -> None:
        """Ensure threads and connections are cleaned up when object is destroyed."""
        try:
            self.disconnect()
        except Exception:
            pass  # Ignore errors during cleanup

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure cleanup."""
        self.disconnect()

    # Status Properties
    def is_connected(self) -> bool:
        """True if device is connected and online."""
        return self._connected

    def is_busy(self) -> bool:
        """True if device is processing commands."""
        return self._busy

    def is_ready(self) -> bool:
        """True if device is ready to receive commands."""
        return self._ready

    def has_queued_commands(self) -> bool:
        """True if commands are waiting in queue."""
        return not self._command_queue.empty()

    def has_device(self) -> bool:
        """True if device connection exists."""
        return self._device is not None

    # Callback Configuration
    def set_connect_callback(self, callback) -> None:
        """Set callback for connection events."""
        self._connect_callback = callback

    def set_error_callback(self, callback) -> None:
        """Set callback for error events."""
        self._error_callback = callback

    def set_message_callback(self, callback) -> None:
        """Set callback for message events."""
        self._message_callback = callback

    def log_error(self, error: str) -> None:
        """Log error via callback or fallback to logger."""
        if self._error_callback:
            try:
                self._error_callback(error)
            except Exception:
                self._logger.error(traceback.format_exc())
        else:
            self._logger.error(error)

    # Connection Management
    def disconnect(self) -> None:
        """Safely disconnect from device and stop all threads."""
        with self._lock:
            if not self._device:
                return

            # Signal threads to stop
            self._stop_event.set()

            # Wait for threads to finish
            if self._read_thread and self._read_thread != threading.current_thread():
                self._read_thread.join()
                self._read_thread = None

            if self._send_thread and self._send_thread != threading.current_thread():
                self._send_thread.join()
                self._send_thread = None

            # Close device connection
            if self._device:
                try:
                    self._device.disconnect()
                except Exception:
                    pass  # Ignore errors during cleanup

            # Always reset state
            self._device = None
            self._connected = False
            self._busy = False

    @typechecked
    def connect(self, port: Optional[str] = None, baud: Optional[int] = None) -> None:
        """Connect to device and start communication threads.

        Args:
            port: Serial port or network address
            baud: Baud rate for serial connections
        """
        with self._lock:
            # Disconnect existing connection
            if self._device:
                self.disconnect()

            # Update connection parameters
            if port:
                self._port = port
            if baud:
                self._baud = baud

            # Validate parameters
            if not self._port:
                self.log_error("Connection error: No port specified")
                return

            # For serial connections, baud rate is required
            if ':' not in self._port and not self._baud:
                self.log_error("Connection error: No baud rate specified for serial connection")
                return

            # Establish connection using factory
            try:
                # Use baud rate or default to 0 for socket connections
                baud_rate = self._baud if self._baud is not None else 0
                self._device = BaseDevice.create(self._port, baud_rate)
                self._device.connect(self._port, baud_rate)
            except DeviceError as e:
                self.log_error(f"Connection error: {e}")
                self._device = None
                return

            # Start communication threads
            self._start_threads()

    # Communication Methods
    def _readline(self) -> Optional[str]:
        """Read and process a line from device."""
        try:
            line_bytes = self._device.readline()
            if line_bytes is None:  # READ_EOF
                self.log_error("Device disconnected during read")
                self._stop_event.set()
                return None

            line = line_bytes.decode('utf-8')

            # Process non-empty lines
            if len(line) > 1:
                self._handle_message(line)
                self._logger.info("RECV: %s", line.rstrip())

            return line

        except UnicodeDecodeError:
            self.log_error(f"Invalid data from {self._port} at {self._baud} baud")
            return None
        except DeviceError as e:
            self.log_error(f"Read error: {e}")
            return None

    def _handle_message(self, line: str) -> None:
        """Process incoming message through callback."""
        if self._message_callback:
            try:
                self._message_callback(line)
            except Exception:
                self.log_error(traceback.format_exc())

    def _should_continue_listening(self) -> bool:
        """Check if read thread should continue."""
        return (not self._stop_event.is_set() and
                self._device and
                self._device.is_connected)

    def _wait_for_online(self) -> None:
        """Wait for device to come online and respond."""
        ONLINE_INDICATORS = ('start', 'Grbl ', 'ok', 'T:')
        MAX_EMPTY_LINES = 15

        while not self._connected and self._should_continue_listening():
            self._send("G4 P0")  # Send keepalive
            empty_lines = 0

            while self._should_continue_listening():
                line = self._readline()
                if line is None:
                    break

                if not line.strip():
                    empty_lines += 1
                    if empty_lines >= MAX_EMPTY_LINES:
                        break
                else:
                    empty_lines = 0
                    if any(line.startswith(indicator) for indicator in ONLINE_INDICATORS):
                        self._set_connected()
                        return

    def _set_connected(self) -> None:
        """Mark device as connected and trigger callback."""
        self._connected = True
        if self._connect_callback:
            try:
                self._connect_callback()
            except Exception:
                self.log_error(traceback.format_exc())

    # Threading Methods
    def _listen_loop(self) -> None:
        """Main read thread loop for processing device messages."""
        self._ready = True

        # Wait for initial connection
        if not self._busy:
            self._wait_for_online()

        # Process incoming messages
        while self._should_continue_listening():
            line = self._readline()
            if line is None:
                self._logger.debug('Read failed, exiting listen loop')
                break

            self._process_response(line)

        self._ready = True
        self._logger.debug('Read thread terminated')

    def _process_response(self, line: str) -> None:
        """Process a response line from the device."""
        line = line.strip()
        if line.startswith(('start', 'Grbl ', 'ok')):
            self._ready = True
        elif line.startswith('Error'):
            self.log_error(line)

    def _start_threads(self) -> None:
        """Start communication threads."""
        # Reset stop event
        self._stop_event.clear()

        # Start read thread
        self._read_thread = threading.Thread(
            target=self._listen_loop, name='read_thread')
        self._read_thread.start()

        # Start send thread
        self._send_thread = threading.Thread(
            target=self._sender_loop, name='send_thread')
        self._send_thread.start()



    def _sender_loop(self) -> None:
        """Main send thread loop for processing command queue."""
        while not self._stop_event.is_set():
            try:
                command = self._command_queue.get(timeout=0.1)
            except QueueEmpty:
                continue

            self._wait_until_ready()
            self._send(command)
            self._wait_until_ready()

    def _wait_until_ready(self) -> None:
        """Wait until device is ready for next command."""
        while self._device and self._busy and not self._ready and not self._stop_event.is_set():
            self._stop_event.wait(0.001)

    # Command Processing Control
    def start_processing(self) -> bool:
        """Start processing queued commands."""
        if not (self._connected and self._device):
            return False
        self._busy = True
        return True

    def stop_processing(self) -> None:
        """Stop processing queued commands."""
        self._busy = False

    # Command Sending
    @typechecked
    def enqueue(self, command: str) -> None:
        """Queue command for sending to device."""
        if not self._connected:
            self.log_error("Cannot send command: not connected")
            return
        self._command_queue.put_nowait(command)

    @typechecked
    def _send(self, command: str) -> None:
        """Send command directly to device."""
        if not self._device:
            return

        self._logger.info("SENT: %s", command)
        try:
            self._device.write(f"{command}\n".encode('ascii'))
        except DeviceError as e:
            self.log_error(f"Write error: {e}")