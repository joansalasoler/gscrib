# -*- coding: utf-8 -*-
import unittest

from gscrib.geometry import grid, Point


class TestPatterns(unittest.TestCase):
    def test_grid_row_order(self):
        """Test the grid iterator with row order."""
        points = list(grid(rows=2, columns=3, row_step=10, col_step=5))
        expected_points = [
            Point(0, 0), Point(5, 0), Point(10, 0),
            Point(0, 10), Point(5, 10), Point(10, 10),
        ]
        self.assertEqual(points, expected_points)

    def test_grid_column_order(self):
        """Test the grid iterator with column order."""
        points = list(grid(rows=2, columns=3, row_step=10, col_step=5, order='column'))
        expected_points = [
            Point(0, 0), Point(0, 10),
            Point(5, 0), Point(5, 10),
            Point(10, 0), Point(10, 10),
        ]
        self.assertEqual(points, expected_points)

    def test_grid_snake_order(self):
        """Test the grid iterator with snake order."""
        points = list(grid(rows=3, columns=2, row_step=10, col_step=5, order='snake'))
        expected_points = [
            Point(0, 0), Point(5, 0),
            Point(5, 10), Point(0, 10),
            Point(0, 20), Point(5, 20),
        ]
        self.assertEqual(points, expected_points)

    def test_grid_single_row(self):
        """Test the grid iterator for a single row."""
        points = list(grid(rows=1, columns=3, row_step=10, col_step=5))
        expected_points = [Point(0, 0), Point(5, 0), Point(10, 0)]
        self.assertEqual(points, expected_points)

    def test_grid_single_column(self):
        """Test the grid iterator for a single column."""
        points = list(grid(rows=3, columns=1, row_step=10, col_step=5))
        expected_points = [Point(0, 0), Point(0, 10), Point(0, 20)]
        self.assertEqual(points, expected_points)

    def test_grid_float_steps(self):
        """Test the grid iterator with floating point steps."""
        points = list(grid(rows=2, columns=2, row_step=0.5, col_step=0.5))
        expected_points = [
            Point(0, 0), Point(0.5, 0),
            Point(0, 0.5), Point(0.5, 0.5),
        ]
        self.assertEqual(points, expected_points)

    def test_grid_invalid_order(self):
        """Test that the grid iterator raises an error for an invalid order."""
        with self.assertRaises(ValueError):
            list(grid(rows=2, columns=2, row_step=1, col_step=1, order='invalid_order'))
