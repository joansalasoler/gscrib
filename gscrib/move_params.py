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


class MoveParams(dict):
    """A case-insensitive dictionary for G-code movement parameters.

    This dictionary subclass automatically converts all keys to
    uppercase, allowing case-insensitive access to movement parameters.
    This is useful for G-code generation where parameter letters are
    traditionally case-insensitive.

    Examples:
        >>> params = MoveParams()
        >>> params['F'] = 1000
        >>> params['f']  # Returns 1000
        >>> params['F']  # Returns 1000
    """

    def __init__(self, *args, **kwargs):
        """Initialize with uppercase keys."""

        super().__init__()

        if args or kwargs:
            self.update(dict(*args, **kwargs))

    def __setitem__(self, key, value):
        """Store value with uppercase key."""

        super().__setitem__(key.upper(), value)

    def __getitem__(self, key):
        """Retrieve value using uppercase key, None if not found."""

        return super().get(key.upper())

    def __delitem__(self, key):
        """Delete item using uppercase key."""

        super().__delitem__(key.upper())

    def __contains__(self, key):
        """Check existence using uppercase key."""

        return super().__contains__(key.upper())

    def get(self, key, default=None):
        """Get value, return default if not found."""

        return super().get(key.upper(), default)

    def setdefault(self, key, default=None):
        """Set default value if key not found."""

        return super().setdefault(key.upper(), default)

    def update(self, *args, **kwargs):
        """Update dictionary converting all keys to uppercase."""

        for key, value in dict(*args, **kwargs).items():
            self[key.upper()] = value
