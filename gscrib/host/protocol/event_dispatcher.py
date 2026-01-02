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

import threading
from collections import defaultdict
from typing import Callable, Type
from .events import HostEvent


class EventDispatcher:
    """Dispatches events to registered handlers.

    Handlers can be registered for a specific event or a base class to
    receive all events that are instances of that class or any subclass.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._handlers = defaultdict(list)

    def subscribe(self, event_type: Type, handler: Callable) -> None:
        """Registers a handler for a specific event type.

        Args:
            event_type: The class of the event to subscribe to.
            handler: The callable to execute when the event occurs.
        """

        with self._lock:
            self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: Type, handler: Callable) -> None:
        """Unregisters a handler for a specific event type.

        Args:
            event_type: The class of the event to unsubscribe from.
            handler: The callable to remove from the registry.
        """

        with self._lock:
            if handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)

    def dispatch(self, event: HostEvent) -> None:
        """Dispatches an event to all handlers registered for its type.

        Args:
            event: The event instance to dispatch.
        """

        targets = []

        with self._lock:
            for event_type, handlers in self._handlers.items():
                if isinstance(event, event_type):
                    targets.extend(handlers)

        for handler in targets:
            handler(event)
