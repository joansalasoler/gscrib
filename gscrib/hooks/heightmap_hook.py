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

from typing import Callable
from typeguard import typechecked

from gscrib.heightmaps import BaseHeightMap


@typechecked
def heightmap_hook(heightmap: BaseHeightMap) -> Callable:
    """Creates a hook that adjusts Z coordinates using a heightmap.

    This hook modifies the Z coordinate of each motion command by looking
    up the heightmap value at the target (X, Y) position, enabling
    automatic height compensation for uneven surfaces.

    Note:
        Since only the final Z coordinate is adjusted, long moves across
        uneven terrain may not accurately follow the surface contour.
        For more precise tracking, use the method
        :meth:`sample_path <gscrib.heightmaps.BaseHeightMap.sample_path>`
        of the heightmap implementation to split the move into smaller
        segments that better match the heightmap's shape.

    Args:
        heightmap: Height map for Z coordinate lookup

    Returns:
        Hook function for automatic height compensation

    Example:
        >>> heightmap = SparseHeightMap.from_path("surface.csv")
        >>> g.add_hook(heightmap_hook(heightmap))
        >>> g.move(x=10, y=10)  # Sets Z from the heightmap
    """

    def hook_function(origin, target, params, state):
        z_value = heightmap.get_depth_at(target.x, target.y)
        params.update(Z=z_value)

        return params

    return hook_function
