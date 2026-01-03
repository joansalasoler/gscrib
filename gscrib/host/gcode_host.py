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

import logging, threading, itertools
from queue import PriorityQueue, Empty
from typing import Callable, Type

from .connection import Connection
from .protocol import EventDispatcher, EventParser
from .scheduler import Command, TaskPriority
from .scheduler import SendTask, CommandTracker
from .scheduler import QuotaTracker, ConsumeQuotaTimeout
from .exceptions import EmptyCommand, MultipleCommands

from .protocol.events import (
    HostEvent,
    HostExceptionEvent,
    DeviceErrorEvent,
    DeviceFaultEvent,
    DeviceOnlineEvent,
    DeviceReadyEvent,
    DeviceResendEvent
)


class GCodeHost:
    """Manages asynchronous communication with G-code devices.

    This class handles the low-level details of communicating with a
    G-code device, including:

    - Managing the connection (serial, socket, etc.)
    - Sending commands in a background thread.
    - Receiving and parsing responses in a background thread.
    - Handling flow control (wait for 'ok', line numbering, checksums).
    - Dispatching events for device status changes.

    The host uses three configurable timeout values:

    - write_timeout: Maximum time to wait when writing commands to the
      device. If exceeded, processing stops immediately. Default is 10.0
      seconds, safe for most serial/socket connections.

    - online_timeout: Maximum time to wait for the device to send its
      initial handshake. If exceeded, the sender proceeds assuming the
      communication will recover automatically. Default is 10.0 seconds.

    - poll_timeout: Time interval for polling operations (reading input,
      checking queues, etc.). Lower values increase responsiveness but
      consume more CPU. Default is 0.2 seconds.
    """

    _WRITE_TIMEOUT = 10.0 # seconds
    _ONLINE_TIMEOUT = 10.0 # seconds
    _POLL_TIMEOUT = 0.2 # seconds

    def __init__(self, connection: Connection):
        """Initializes the host with a specific connection.

        Args:
            connection (Connection): A connection instance
        """

        if not isinstance(connection, Connection):
            raise TypeError("Connection is required")

        self._logger = logging.getLogger(__name__)

        self._connection = connection
        self._worker_threads: list[threading.Thread] = []
        self._parser = EventParser()
        self._send_queue = PriorityQueue()
        self._send_history = CommandTracker()
        self._send_quota = QuotaTracker()
        self._events = EventDispatcher()

        self._clear_signal = threading.Event()
        self._online_signal = threading.Event()
        self._shutdown_signal = threading.Event()

        self._line_counter = itertools.count(1)
        self._task_counter = itertools.count()
        self._write_timeout = self._WRITE_TIMEOUT
        self._online_timeout = self._ONLINE_TIMEOUT
        self._poll_timeout = self._POLL_TIMEOUT
        self._sign_commands = False
        self._was_started = False

    @property
    def is_busy(self) -> bool:
        """Check if the host is busy sending commands.

        Returns:
            bool: If there are pending commands to send or acknowledge.
        """

        if self._shutdown_signal.is_set():
            return False

        if not self._send_queue.empty():
            return True

        return self._send_quota.pending()

    @property
    def is_online(self) -> bool:
        """Check if the device is online.

        Returns:
            bool: If the hardware has responded to a handshake.
        """

        return self._online_signal.is_set()

    @property
    def sign_commands(self) -> bool:
        """Check if command signing is enabled.

        Returns:
            bool: If checksums must be added to commands.
        """

        return self._sign_commands

    @sign_commands.setter
    def sign_commands(self, enabled: bool) -> None:
        """Enable or disable command signing.

        Args:
            enabled (bool): Whether to checsum sent commands.
        """

        self._sign_commands = enabled

    @property
    def write_timeout(self) -> float:
        """Get the write operation timeout in seconds.

        Returns:
            float: Write timeout in seconds. Default is 10.0.
        """

        return self._write_timeout

    @write_timeout.setter
    def write_timeout(self, seconds: float) -> None:
        """Set the write operation timeout in seconds.

        Args:
            seconds (float): Write timeout in seconds.

        Raises:
            ValueError: If seconds is not positive.
        """

        self._validate_timeout(seconds, "Write timeout")
        self._write_timeout = seconds

    @property
    def online_timeout(self) -> float:
        """Get the device online signal timeout in seconds.

        Returns:
            float: Online signal timeout in seconds. Default is 10.0.
        """

        return self._online_timeout

    @online_timeout.setter
    def online_timeout(self, seconds: float) -> None:
        """Set the device online signal timeout in seconds.

        Args:
            seconds (float): Online signal timeout in seconds.

        Raises:
            ValueError: If seconds is not positive.
        """

        self._validate_timeout(seconds, "Online timeout")
        self._online_timeout = seconds

    @property
    def poll_timeout(self) -> float:
        """Get the polling operation timeout in seconds.

        Returns:
            float: Poll timeout in seconds. Default is 0.2.
        """

        return self._poll_timeout

    @poll_timeout.setter
    def poll_timeout(self, seconds: float) -> None:
        """Set the polling operation timeout in seconds.

        Args:
            seconds (float): Poll timeout in seconds.

        Raises:
            ValueError: If seconds is not positive.
        """

        self._validate_timeout(seconds, "Poll timeout")
        self._poll_timeout = seconds

    # ------------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------------

    def subscribe(self, event_type: Type, handler: Callable) -> None:
        """Subscribe to events from the host.

        Handlers can be registered for a specific event or a base class
        to receive all events of that subclass that type.

        Args:
            event_type (Type): The type of event to subscribe to.
            handler (Callable): Callback to invoke when the event occurs.
        """

        self._events.subscribe(event_type, handler)

    def unsubscribe(self, event_type: Type, handler: Callable) -> None:
        """Unsubscribe from events from the host.

        Args:
            event_type (Type): The type of event to unsubscribe from.
            handler (Callable): The callback function to remove.
        """

        self._events.unsubscribe(event_type, handler)

    def start(self) -> None:
        """Starts the background sender and receiver threads.

        Initializes and starts the worker threads for sending commands
        and receiving responses. Threads will continue to run until
        stop() is called or an unhandled exception occurs.

        Raises:
            RuntimeError: If the host has already been started.
        """

        if self._was_started:
            raise RuntimeError("Host can only be started once")

        self._was_started = True
        self._clear_signal.set()

        self._worker_threads = [
            threading.Thread(
                target=self._run_receiver,
                name="gcode_receiver"
            ),
            threading.Thread(
                target=self._run_sender,
                name="gcode_sender"
            )
        ]

        for thread in self._worker_threads:
            thread.start()

    def stop(self, timeout: float | None = None) -> None:
        """Signals all threads to stop and waits for them to terminate.

        Initiates a graceful shutdown of the host, clearing queues and
        waiting for worker threads to join. Any pending commands will
        not be sent. Users should use join_queue() to wait for all
        commands to be sent and acknowledged.

        Args:
            timeout (float | None): Maximum time in seconds to wait for
                each worker thread to terminate. If None, waits indefinitely.

        Raises:
            RuntimeError: If the host is not running.
        """

        if self._shutdown_signal.is_set():
            return

        if not self._was_started:
            raise RuntimeError("Host is not running")

        self._force_host_shutdown()

        for thread in self._worker_threads:
            thread.join(timeout=timeout)

    def join_queue(self) -> None:
        """Blocks until all queued commands are processed and acknowledged.

        Waits for the send queue to be empty and for all sent commands
        to be acknowledged by the device. This may block indefinitely if
        the device is unresponsive. Users should call stop() to force
        termination in such cases.
        """

        self._send_queue.join()
        self._send_quota.join()

    def enqueue(self, raw_gcode: str) -> bool:
        """Adds a G-code instruction to the sending queue.

        Queues a raw G-code instruction for sending. Returns False if the
        input is empty or contains only comments (silently ignored). This
        method is thread-safe.

        Args:
            raw_gcode (str): Raw G-code instruction to send.

        Returns:
            bool: If the instruction was queued

        Raises:
            RuntimeError: If the host is shutting down or multiple
                commands are provided in a single string.
        """

        if self._shutdown_signal.is_set():
            raise RuntimeError("Cannot enqueue commands during shutdown")

        try:
            command = self._build_command(raw_gcode)
            return self._enqueue(command, TaskPriority.NORMAL)
        except EmptyCommand:
            return False  # Ignore empty commands
        except MultipleCommands as e:
            raise RuntimeError("Cannot enqueue multiple commands") from e

    # ------------------------------------------------------------------------
    # Command scheduling
    # ------------------------------------------------------------------------

    def _build_command(self, raw_gcode: str) -> Command:
        """Builds a G-code command object ready for sending.

        A unique and monotonically increasing line number is assigned
        to the command. If command signing is enabled, the command will
        include a checksum and line number.

        Args:
            raw_gcode (str): Raw G-code instruction.

        Returns:
            Command: The constructed command object.
        """

        signed = self.sign_commands
        line_number = next(self._line_counter)
        return Command(line_number, raw_gcode, signed)

    def _enqueue(self, command: Command, priority: TaskPriority) -> bool:
        """Adds a G-code command to the execution queue.

        Queues a command, only if the service is active and not stopping,
        otherwise this method returns false.

        Args:
            command (Command): The command object to queue.
            priority (TaskPriority): Priority of the command.

        Returns:
            bool: If the command was queued
        """

        if self._shutdown_signal.is_set():
            return False

        sequence_number = next(self._task_counter)
        task = SendTask(priority, sequence_number, command)
        self._send_queue.put(task)

        return True

    def _enqueue_resend(self, line_number: int) -> None:
        """Resend a previously sent command.

        Retrieves a command from history by line number and re-queues it
        with system priority.

        Args:
            line_number (int): The line number of the command to resend.

        Raises:
            KeyError: If the command is not found in history (not sent
                or evicted from history).
        """

        command = self._send_history.fetch(line_number)
        self._enqueue(command, TaskPriority.SYSTEM)

    def _enqueue_line_reset(self) -> None:
        """Enqueues a command to reset the line counter on the device."""

        command = Command(0, "M110 N0", signed=False)
        self._enqueue(command, TaskPriority.SYSTEM)

    def _enqueue_synch(self) -> None:
        """Enqueues a synchronization command."""

        command = self._build_command("G4 P0")
        self._enqueue(command, TaskPriority.SYSTEM)

    def _enqueue_handshake(self) -> None:
        """Enqueues the initial handshake commands.

        Sends line reset (if signing is enabled) and synchronization
        commands to establish communication state.
        """

        if self.sign_commands:
            self._enqueue_line_reset()

        self._enqueue_synch()

    def _purge_send_queue(self) -> None:
        """Removes all pending tasks from the send queue"""

        try:
            while True:
                self._send_queue.get_nowait()
                self._send_queue.task_done()
        except Empty:
            pass

    @staticmethod
    def _validate_timeout(timeout: float, name: str) -> None:
        """Validate that a timeout value is positive."""

        if timeout is None or timeout <= 0:
            raise ValueError(f"{name} must be positive")

    # ------------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------------

    def _handle_incoming_message(self, message: str) -> None:
        """Handle incoming messages from the device.

        Args:
            message (str): Message string received from the device.
        """

        event: HostEvent = self._parser.parse(message)

        match event:
            case DeviceOnlineEvent():
                self._handle_device_ready(event)
            case DeviceReadyEvent():
                self._handle_device_ready(event)
            case DeviceResendEvent():
                self._handle_device_resend(event)
            case DeviceErrorEvent():
                self._handle_device_error(event)
            case DeviceFaultEvent():
                self._handle_device_fault(event)

        self._events.dispatch(event)

    def _handle_device_ready(self, _event: HostEvent) -> None:
        """Handle acknowledgment events from the device."""

        self._send_quota.reclaim()
        self._online_signal.set()
        self._clear_signal.set()

    def _handle_device_error(self, _event: HostEvent) -> None:
        """Handle error events from the device."""

        self._send_quota.reclaim()
        self._clear_signal.set()

    def _handle_device_resend(self, event: HostEvent) -> None:
        """Handle resend events from the device."""

        line_number = event.line_number
        self._enqueue_resend(line_number)
        self._send_quota.reclaim()
        self._clear_signal.set()

    def _handle_device_fault(self, _event: HostEvent) -> None:
        """Handle failure events from the device."""

        self._logger.error("Device fault. Shutting down.")
        self._force_host_shutdown()

    def _handle_host_exception(self, error: Exception) -> None:
        """Handle exceptions occurring in worker threads."""

        self._force_host_shutdown()
        event = HostExceptionEvent(error)
        self._events.dispatch(event)

    # ------------------------------------------------------------------------
    # Device communication
    # ------------------------------------------------------------------------

    def _force_host_shutdown(self) -> None:
        """Force the host into a shutdown state."""

        self._shutdown_signal.set()
        self._online_signal.clear()
        self._clear_signal.set()

        self._purge_send_queue()
        self._send_quota.flush()

    def _prepare_for_acknowledgment(self) -> None:
        """Wait for acknowledgment only if required.

        If device doesn't support streaming, force the sender to wait
        for the device to acknowledge the last sent command before
        sending the next one.
        """

        if not self._connection.can_stream_commands():
            self._clear_signal.clear()

    def _wait_for_acknowledgment(self, poll_timeout: float) -> None:
        """Blocks until an acknowledgment has been received.

        If device doesn't support streaming, waits for the device to
        acknowledge the last sent command, otherwise returns immediately.

        Args:
            poll_timeout (float): Polling timeout in seconds.

        Raises:
            TimeoutError: If the host is shutting down while waiting.
        """

        while not self._shutdown_signal.is_set():
            if self._clear_signal.wait(timeout=poll_timeout):
                break

        if self._shutdown_signal.is_set():
            raise TimeoutError("Shutdown requested")

    def _run_receiver(self) -> None:
        """Background loop that reads responses from the device.

        Incoming messages are parsed and converted into events. Users
        can subscribe to these events using the subscribe() method.
        """

        self._logger.info("Starting receiver thread")
        poll_timeout = self.poll_timeout

        while not self._shutdown_signal.is_set():
            try:
                line = self._connection.read_line(timeout=poll_timeout)
                if line: self._handle_incoming_message(line)
            except Exception as e:  # pylint: disable=W0718
                self._logger.error("Receiver exception: %s", e)
                self._handle_host_exception(e)

        self._logger.info("Receiver thread exiting")

    def _run_sender(self) -> None:
        """Background loop that dispatches commands to the device.

        Before entering the main streaming loop, a short startup sequence
        is used to wait for the device to become ready, avoid sending
        commands too early, and establish a known synchronization point.

        1. Wait for an initial message from the device (e.g. "start",
           "Grbl", or "ok") for up to N seconds. Devices typically send
           this immediately after connecting.

        2. If signing is enabled, send a line number reset command
           (M110 N0). Ensures the device starts counting lines from 1.

        3. Send a synchronization command (G4 P0). Most devices will
           acknowledge this only after the action has completed.

        4. Enter the main loop: dequeue commands, apply flow control,
           send them, and wait for acknowledgements.

        If the device becomes unresponsive, this may block indefinitely.
        Users should call stop() to force termination in such cases.
        """

        self._logger.info("Starting sender thread")

        write_timeout = self.write_timeout
        poll_timeout = self.poll_timeout

        self._online_signal.wait(timeout=self.online_timeout)
        self._enqueue_handshake()

        while not self._shutdown_signal.is_set():
            task: SendTask = None

            try:
                self._wait_for_acknowledgment(poll_timeout)
                task = self._send_queue.get(timeout=poll_timeout)
                line = task.command.format_line()

                size = 1 + len(line)
                self._send_quota.consume(size, timeout=poll_timeout)
                self._prepare_for_acknowledgment()

                self._connection.write_line(line, timeout=write_timeout)
                self._send_history.record(task.command)
                self._send_queue.task_done()
            except ConsumeQuotaTimeout:
                self._send_queue.put(task)
                self._send_queue.task_done()
            except Empty:
                continue
            except Exception as e:  # pylint: disable=W0718
                if task: self._send_queue.task_done()
                if self._shutdown_signal.is_set(): break
                self._logger.error("Sender exception: %s", e)
                self._handle_host_exception(e)

        self._logger.info("Sender thread exiting")
