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

class HostError(Exception):
    """Base exception for host-related errors."""


class HostConnectError(HostError):
    """Raised when connection fails or is not available."""


class HostReadError(HostError):
    """Raised when reading data from a device fails."""


class HostWriteError(HostError):
    """Raised when sending data to a device fails."""


class EmptyCommand(HostError):
    """Raised when a command is empty or contains only comments."""


class MultipleCommands(HostError):
    """Raised when multiple commands are provided in a single string."""
