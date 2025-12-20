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

import math
from typeguard import typechecked

from gscrib.types import MoveHook
from gscrib.enums import ExtrusionMode


@typechecked
def extrusion_hook(layer_height: float, nozzle_diameter: float,
                   filament_diameter: float) -> MoveHook:
    """Creates a hook function to automatically extrude filament.

    Args:
        layer_height: Height of each layer in work units
        nozzle_diameter: Diameter of the nozzle in work units
        filament_diameter: Diameter of the filament in work units

    Returns:
        A hook function that calculates extrusion amounts

    Example:
        >>> g.add_hook(extrusion_hook(
        ...    layer_height = 0.2,
        ...    nozzle_diameter = 0.4,
        ...    filament_diameter = 1.75
        ... ))
    """

    radius = filament_diameter / 2.0
    cross_section = math.pi * radius * radius
    extrusion_area = nozzle_diameter * layer_height

    def hook_function(origin, target, params, state):
        dt = target - origin

        segment_length = math.hypot(dt.x, dt.y)
        extrusion_volume = extrusion_area * segment_length
        filament_length = extrusion_volume / cross_section

        if state.extrusion_mode == ExtrusionMode.ABSOLUTE:
            filament_length += state.get_parameter("E") or 0.0

        params.update(E=filament_length)

        return params

    return hook_function
