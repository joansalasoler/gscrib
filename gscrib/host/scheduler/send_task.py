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

from typing import NamedTuple

from .command import Command
from .task_priority import TaskPriority


class SendTask(NamedTuple):
    """Unit of work representing a command scheduled for transmission.

    Combines a command with scheduling metadata used by the send loop,
    including priority and a monotonically increasing sequence number.
    """

    priority: TaskPriority
    sequence_number: int
    command: Command
