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

import time, threading
from collections import deque


class ConsumeQuotaTimeout(TimeoutError):
    """Timeout waiting for write quota to be available."""


class QuotaTracker:
    """Thread-safe device buffer memory reservation system.

    Tracks the available buffer space on a remote device to prevent buffer
    overflows. It blocks producers when the buffer is full and releases
    space when commands are acknowledged.
    """

    def __init__(self, max_bytes: int = 127):
        """Initializes the quota tracker.

        Args:
            max_bytes: Total capacity of the device buffer in bytes.

        Raises:
            ValueError: If max_bytes is not positive.
        """

        self._validate_max_bytes(max_bytes)

        self._in_flight = deque()
        self._condition = threading.Condition()
        self._max_bytes = max_bytes
        self._free_bytes = max_bytes

    def consume(self, size: int, timeout: float = 2.0) -> None:
        """Reserves memory for a write operation.

        Blocks until sufficient buffer space is available or the timeout
        expires.

        Args:
            size (int): Number of bytes to reserve.
            timeout (float): Maximum time to wait in seconds.

        Raises:
            ValueError: If size is invalid or exceeds total capacity, or
                if timeout is not positive.
            SendQuotaConsumeTimeout: If the reservation cannot be fulfilled
                within the timeout period.
        """

        self._validate_timeout(timeout)
        self._validate_size(size, self._max_bytes)

        with self._condition:
            end = time.monotonic() + timeout

            while self._free_bytes < size:
                remaining = end - time.monotonic()
                if remaining <= 0: raise ConsumeQuotaTimeout()
                self._condition.wait(remaining)

            self._in_flight.append(size)
            self._free_bytes -= size

    def reclaim(self) -> None:
        """Releases memory for the oldest in-flight write.

        This should be called when a command has been acknowledged by the
        device, freeing up buffer space for subsequent commands.
        """

        with self._condition:
            if self._in_flight:
                size = self._in_flight.popleft()
                self._free_bytes += size
                self._condition.notify_all()

    def join(self) -> None:
        """Blocks until all in-flight commands have been reclaimed."""

        with self._condition:
            while self._in_flight:
                self._condition.wait()

    def flush(self) -> None:
        """Reset the quota state, clearing the in-flight queue.

        Clears all in-flight tracking and restores the full buffer capacity.
        This is typically used after a device reset or error condition.
        """

        with self._condition:
            self._in_flight.clear()
            self._free_bytes = self._max_bytes
            self._condition.notify_all()

    @staticmethod
    def _validate_max_bytes(max_bytes: int) -> None:
        """Validates that the maximum buffer size is positive."""

        if max_bytes <= 0:
            raise ValueError("'max_bytes' must be positive")

    @staticmethod
    def _validate_size(size: int, max_bytes: int) -> None:
        """Validates that size is positive and less than max_bytes."""

        if size <= 0:
            raise ValueError("'size' must be positive")

        if size > max_bytes:
            raise ValueError("'size' exceeds buffer capacity")

    @staticmethod
    def _validate_timeout(timeout: float) -> None:
        """Validates that the timeout is positive."""

        if timeout <= 0:
            raise ValueError("'timeout' must be positive")
