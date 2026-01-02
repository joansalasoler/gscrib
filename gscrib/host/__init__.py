# -*- coding: utf-8 -*-

"""
Host module for device communication.

This module provides asynchronous communication with G-code devices via
unified connection interfaces. It handles command scheduling, execution,
and response parsing with event-based notification.
"""

from .connection import Connection
from .gcode_host import GCodeHost
from .exceptions import HostConnectError, HostReadError, HostWriteError

__all__ = [
    'Connection',
    'GCodeHost',
    'HostConnectError',
    'HostReadError',
    'HostWriteError'
]
