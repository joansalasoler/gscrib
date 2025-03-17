# -*- coding: utf-8 -*-

"""
Available machine modes.

This module provides a collection of enumeration classes that define
various operational modes for G-code generation. Each mode represents a
specific aspect of machine control that a user can combine to create
complete G-code programs.
"""

from .direct_write_mode import DirectWriteMode

__all__ = [
    "DirectWriteMode",
]
