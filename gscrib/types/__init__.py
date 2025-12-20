# -*- coding: utf-8 -*-

"""Type aliases for the gscrib package."""

from typing import TypeAlias
from typing import Callable, Sequence, Tuple, Union
from typing import TextIO, BinaryIO
from typing import TYPE_CHECKING

from numpy import ndarray


if TYPE_CHECKING:
    from gscrib.geometry.point import Point
    from gscrib.params import ParamsDict
    from gscrib.gcode_state import GState

OptFloat: TypeAlias = float | None
"""An optional float value."""

OptFile: TypeAlias = Union[TextIO, BinaryIO, None]
"""An optional file-like object supporting both text and binary modes."""

PathFn: TypeAlias = Callable[[ndarray], ndarray]
"""A parametric function for path interpolation."""

PointLike: TypeAlias = Union['Point', Sequence[float | None], ndarray, None]
"""Objects that can be interpreted as a point in 3D space."""

ProcessedParams: TypeAlias = Tuple['Point', 'ParamsDict', str | None]
"""A tuple containing processed parameters for moves."""

Bound: TypeAlias = Union[int, float, PointLike]
"""Boundary value that can be either numeric or a point."""

MoveHook: TypeAlias = Callable[['Point', 'Point', 'ParamsDict', 'GState'], 'ParamsDict']
"""A hook function that processes movement parameters before execution."""


__all__ = [
    "Bound",
    "MoveHook",
    "OptFloat",
    "OptFile",
    "PathFn",
    "PointLike",
    "ProcessedParams",
]
