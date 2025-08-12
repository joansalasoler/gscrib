# -*- coding: utf-8 -*-
"""A collection of functions to generate geometric patterns."""
from __future__ import annotations

from .point import Point


def _grid_row_order(rows, columns, row_step, col_step):
    """Generate grid points in row-major order."""
    for i in range(rows):
        for j in range(columns):
            yield Point(j * col_step, i * row_step)


def _grid_column_order(rows, columns, row_step, col_step):
    """Generate grid points in column-major order."""
    for j in range(columns):
        for i in range(rows):
            yield Point(j * col_step, i * row_step)


def _grid_snake_order(rows, columns, row_step, col_step):
    """Generate grid points in a snake-like (bi-directional) order."""
    for i in range(rows):
        if i % 2 == 0:  # Even rows, left to right
            for j in range(columns):
                yield Point(j * col_step, i * row_step)
        else:  # Odd rows, right to left
            for j in range(columns - 1, -1, -1):
                yield Point(j * col_step, i * row_step)


_GRID_ORDERS = {
    'row': _grid_row_order,
    'column': _grid_column_order,
    'snake': _grid_snake_order,
}


def grid(rows: int, columns: int, row_step: float, col_step: float, order: str = 'row'):
    """Generate points over a rectangular grid starting from the origin.

    This function uses a strategy pattern to dispatch to different traversal
    order implementations.

    Args:
        rows (int): The number of rows in the grid.
        columns (int): The number of columns in the grid.
        row_step (float): The distance between rows (along the y-axis).
        col_step (float): The distance between columns (along the x-axis).
        order (str, optional): The order in which to traverse the grid.
            Supported values are 'row', 'column', and 'snake'.
            Defaults to 'row'.

    Yields:
        Point: The next point in the grid.

    Raises:
        ValueError: If an unsupported order is specified.
    """
    if order not in _GRID_ORDERS:
        raise ValueError(
            f"Unsupported order: '{order}'. "
            f"Supported orders are {list(_GRID_ORDERS.keys())}."
        )
    yield from _GRID_ORDERS[order](rows, columns, row_step, col_step)
