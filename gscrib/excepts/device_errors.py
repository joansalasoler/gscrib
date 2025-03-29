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


class DeviceError(Exception):
    """Base exception for device-related errors."""


class DeviceTimeoutError(DeviceError):
    """Raised when a device operation times out."""


class DeviceConnectionError(DeviceError):
    """Raised when a device connection fails."""


class DeviceWriteError(DeviceError):
    """Raised when a sending data to a device fails."""
