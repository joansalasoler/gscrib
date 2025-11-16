# -*- coding: utf-8 -*-

"""Type aliases for the gscrib package."""

from typing import TypeAlias
from typing import Callable, Sequence, Tuple, Union
from typing import TYPE_CHECKING

from numpy import ndarray


if TYPE_CHECKING:
    from gscrib.geometry.point import Point
    from gscrib.params import ParamsDict


OptFloat: TypeAlias = float | None
"""An optional float value."""

PathFn: TypeAlias = Callable[[ndarray], ndarray]
"""A parametric function for path interpolation."""

PointLike: TypeAlias = Union["Point", Sequence[float | None], ndarray, None]
"""Objects that can be interpreted as a point in 3D space."""

ProcessedParams: TypeAlias = Tuple["Point", "ParamsDict", str | None]
"""A tuple containing processed parameters for moves."""

Bound: TypeAlias = Union[int, float, PointLike]
"""Boundary value that can be either numeric or a point."""


__all__ = [
    "Bound",
    "OptFloat",
    "PathFn",
    "PointLike",
    "ProcessedParams",
]
