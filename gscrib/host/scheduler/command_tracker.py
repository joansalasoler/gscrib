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

from collections import OrderedDict
from .command import Command


class CommandTracker:
    """Bounded FIFO history of sent commands.

    Maintains a fixed-size, insertion-ordered mapping of recently sent
    commands keyed by line number. When the capacity limit is exceeded,
    the oldest command is evicted.

    FIFO eviction order is correctness-critical and is relied upon to
    support firmware resend requests.
    """

    def __init__(self, limit: int = 127):
        """Initializes the command history tracker.

        Args:
            limit (int): Maximum number of commands to retain. When
                exceeded, the oldest entries are evicted in FIFO order.
        """

        self._entries = OrderedDict()
        self._limit = limit

    def record(self, command: Command) -> None:
        """Records a command as sent.

        Records the command in the history, replacing any existing command
        with the same line number. If recording exceeds the configured
        capacity, the oldest recorded command is removed.

        Args:
            command (Command): The command object to record.
        """

        self._entries[command.line_number] = command

        while len(self._entries) > self._limit:
            self._entries.popitem(last=False)

    def fetch(self, line_number: int) -> Command:
        """Fetches a previously sent command by its line number.

        Args:
            line_number (int): Line number of the command to retrieve.

        Returns:
            Command: The stored command instance.

        Raises:
            KeyError: If the command is not in the history.
        """

        return self._entries[line_number]
