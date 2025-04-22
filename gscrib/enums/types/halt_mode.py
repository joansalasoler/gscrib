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

from gscrib.enums.base_enum import BaseEnum


class HaltMode(BaseEnum):
    """Program termination and pause modes."""

    OFF = "off"
    PAUSE = "pause"
    OPTIONAL_PAUSE = "optional-pause"
    END_WITHOUT_RESET = "end-without-reset"
    END_WITH_RESET = "end-with-reset"
    PALLET_EXCHANGE = "pallet-exchange"
    WAIT_FOR_BED = "wait-for-bed"
    WAIT_FOR_HOTEND = "wait-for-hotend"
    WAIT_FOR_CHAMBER = "wait-for-chamber"
    WAIT_FOR_MOTION = "wait-for-motion"
