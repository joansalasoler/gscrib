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

import warnings
from .host_writer import HostWriter


class PrintrunWriter(HostWriter):  # pragma: no cover
    """Deprecated writer class for backward compatibility.

    .. deprecated:: 1.3.0
        PrintrunWriter has been renamed to HostWriter.
    """

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "PrintrunWriter is deprecated and will be removed in a"
            "future version. Use HostWriter instead.",
            DeprecationWarning, stacklevel=2
        )

        super().__init__(*args, **kwargs)
