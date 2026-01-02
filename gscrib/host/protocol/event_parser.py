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

import re
from .events import DeviceEvent
from .events_map import EVENTS_MAP

# Matches a line number from a resend message
_RE_LINE_NUMBER = re.compile(r'N?:?(\d+)')

# Matches a key-value pair from a feedback message
_RE_PARAMETER = re.compile(r'([A-Za-z0-9@]+):([\d.,\-]+)')

# Axes order for position readings
_ORDERED_AXES = ("X", "Y", "Z")


class EventParser:
    """Lightweight G-code response parser.

    This class is responsible for parsing raw string responses from a
    device into structured event objects. It also provides utility methods
    to extract specific data fields from status report messages.

    Note that this parser is intentionally permissive to accommodate
    firmware variations. It cannot reliably detect malformed messages that
    may result from *serial* communication errors. For safety-critical
    applications, consider implementing additional validation.
    """

    def parse(self, raw_response: str) -> DeviceEvent:
        """Parse a raw device response into a DeviceEvent.

        Matches the response prefix against a predefined map of event
        types. If a match is found, the corresponding event class is
        instantiated. Otherwise, a generic DeviceEvent is returned.

        Args:
            raw_response (str): The raw string received from the device.

        Returns:
            DeviceEvent: A DeviceEvent or one of its subclasses.
        """

        for prefix, event_type in EVENTS_MAP:
            if raw_response.startswith(prefix):
                return event_type(self, raw_response)

        return DeviceEvent(self, raw_response)

    @staticmethod
    def extract_line_number(raw_response: str) -> int:
        """Extract the line number from a resend message.

        Args:
            raw_response: The raw string containing the resend request.

        Returns:
            int: The extracted line number or -1 if not found.
        """

        match = _RE_LINE_NUMBER.search(raw_response)
        return int(match.group(1)) if match else -1

    @staticmethod
    def extract_fields(raw_response: str) -> dict[str, float]:
        """Extract parameter readings from a device message.

        Parses key-value pairs from status reports (e.g., Grbl status
        lines or RepRap M114/M105 responses). Handles specific formats
        like MPos/WPos coordinates and FS (Feed/Speed) values.

        Args:
            raw_response: The raw string containing parameter data.

        Returns:
            dict: Mapping of parameter names to their values.

        Raises:
            ValueError: If the device message is malformed.
        """

        fields = dict()

        for key, value in _RE_PARAMETER.findall(raw_response):
            parts = tuple(map(float, value.split(",")))

            if key in ("MPos", "WPos", "PRB"):
                for axis, coord in zip(_ORDERED_AXES, parts):
                    fields.setdefault(axis, coord)
            elif key == "FS" and raw_response.startswith("<"):
                if len(parts) == 2:
                    fields.setdefault("F", parts[0])
                    fields.setdefault("S", parts[1])
                else:
                    raise ValueError("Invalid format")
            elif key[0].isupper() or key[0] == "@":
                fields.setdefault(key, parts[0])

        return fields
