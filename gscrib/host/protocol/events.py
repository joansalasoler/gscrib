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

from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .event_parser import EventParser


@dataclass(frozen=True)
class HostEvent:
    """Base class for all events."""

@dataclass(frozen=True)
class HostExceptionEvent(HostEvent):
    """Event representing an unhandled exception."""

    error: Exception

@dataclass(frozen=True)
class DeviceEvent(HostEvent):
    """Base class for all device response events.

    Attributes:
        parser: Parser instance reference.
        message: Raw message received from the device.
    """

    parser: 'EventParser'
    message: str

@dataclass(frozen=True)
class DeviceBusyEvent(DeviceEvent):
    """Device is temporarily busy and cannot process commands"""

@dataclass(frozen=True)
class DeviceDebugEvent(DeviceEvent):
    """Debugging message received from the device."""

@dataclass(frozen=True)
class DeviceErrorEvent(DeviceEvent):
    """Indicates a non-fatal error occurred."""

@dataclass(frozen=True)
class DeviceReadyEvent(DeviceEvent):
    """Device is ready to receive the next command."""

@dataclass(frozen=True)
class DeviceOnlineEvent(DeviceEvent):
    """Device has just booted and is starting up."""

@dataclass(frozen=True)
class DeviceWaitEvent(DeviceEvent):
    """Device has emptied its buffer and is waiting for commands."""

@dataclass(frozen=True)
class DeviceFaultEvent(DeviceEvent):
    """Indicates a fatal error or hardware failure."""

@dataclass(frozen=True)
class DeviceFeedbackEvent(DeviceEvent):
    """Status or feedback information received from the device."""

    @cached_property
    def fields(self) -> dict[str, float]:
        """Parsed parameters from the device message."""

        try:
            return self.parser.extract_fields(self.message)
        except ValueError:
            return dict()  # Malformed message

@dataclass(frozen=True)
class DeviceResendEvent(DeviceEvent):
    """Device requests a resend of a specific command."""

    @cached_property
    def line_number(self) -> int:
        """Requested line number to resend."""

        return self.parser.extract_line_number(self.message)
