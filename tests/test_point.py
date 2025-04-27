import pytest
import numpy as np
from gscrib.geometry import Point


# --------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------

# Test initialization

def test_default_initialization():
    point = Point()
    assert point.x == None
    assert point.y == None
    assert point.z == None

def test_initialization_with_values():
    point = Point(1.0, 2.0, 3.0)
    assert point.x == 1.0
    assert point.y == 2.0
    assert point.z == 3.0

# Test class methods

def test_zero():
    point = Point.zero()
    assert point == Point(0.0, 0.0, 0.0)
    assert isinstance(point.x, float)
    assert isinstance(point.y, float)
    assert isinstance(point.z, float)

def test_from_vector():
    vector = np.array([1.0, 2.0, 3.0, 1.0])
    point = Point.from_vector(vector)
    assert point == Point(1.0, 2.0, 3.0)

def test_from_vector_with_different_sizes():
    vector_3d = np.array([1.0, 2.0, 3.0])
    vector_2d = np.array([1.0, 2.0])
    point_3d = Point.from_vector(vector_3d)
    point_2d = Point.from_vector(vector_2d)
    assert point_3d == Point(1.0, 2.0, 3.0)
    assert point_2d == Point(1.0, 2.0, 0.0)

def test_to_vector():
    point = Point(1.0, 2.0, 3.0)
    vector = point.to_vector()
    assert isinstance(vector, np.ndarray)
    assert vector.shape == (4,)
    assert np.array_equal(vector, np.array([1.0, 2.0, 3.0, 1.0]))

# Test replace method

def test_replace_with_all_values():
    point = Point(1.0, 2.0, 3.0)
    new_point = point.replace(4.0, 5.0, 6.0)
    assert new_point == Point(4.0, 5.0, 6.0)
    assert point == Point(1.0, 2.0, 3.0)

def test_replace_with_none_values():
    point = Point(1.0, 2.0, 3.0)
    new_point = point.replace(None, None, None)
    assert new_point == Point(1.0, 2.0, 3.0)

def test_replace_with_mixed_values():
    point = Point(1.0, 2.0, 3.0)
    new_point = point.replace(4.0, None, 6.0)
    assert new_point == Point(4.0, 2.0, 6.0)

def test_replace_with_zeros():
    point = Point(1.0, 2.0, 3.0)
    new_point = point.replace(0.0, 0.0, 0.0)
    assert new_point == Point(0.0, 0.0, 0.0)

# Test arithmetic operations

def test_addition():
    p1 = Point(1.0, 2.0, 3.0)
    p2 = Point(4.0, 5.0, 6.0)
    result = p1 + p2
    assert result == Point(5.0, 7.0, 9.0)
    assert isinstance(result, Point)

def test_subtraction():
    p1 = Point(4.0, 5.0, 6.0)
    p2 = Point(1.0, 2.0, 3.0)
    result = p1 - p2
    assert result == Point(3.0, 3.0, 3.0)
    assert isinstance(result, Point)

def test_multiply():
    p1 = Point(1.0, 2.0, 3.0)
    result = 2 * p1
    assert result == Point(2.0, 4.0, 6.0)
    assert isinstance(result, Point)
    result = p1 * 2
    assert result == Point(2.0, 4.0, 6.0)
    assert isinstance(result, Point)

def test_divide():
    p1 = Point(2.0, 4.0, 6.0)
    result = p1 / 2
    assert result == Point(1.0, 2.0, 3.0)
    assert isinstance(result, Point)

# Test immutability

def test_immutability():
    point = Point(1.0, 2.0, 3.0)

    with pytest.raises(AttributeError):
        point.x = 4.0

def test_operations_create_new_instances():
    p1 = Point(1.0, 2.0, 3.0)
    p2 = Point(4.0, 5.0, 6.0)
    result = p1 + p2
    assert id(result) != id(p1)
    assert id(result) != id(p2)

# Test comparison operators

def test_point_equality():
    p1 = Point(1.0, 2.0, 3.0)
    p2 = Point(1.0, 2.0, 3.0)
    assert p1 == p2

    p3 = Point(1.0, 2.0, 4.0)
    assert p1 != p3

    p4 = Point(None, 2.0, 3.0)
    p5 = Point(None, 2.0, 3.0)
    assert p4 == p5

def test_point_less_than():
    p1 = Point(1.0, 2.0, 3.0)
    p2 = Point(2.0, 2.0, 3.0)
    assert p1 < p2

    p3 = Point(1.0, 2.0, 3.0)
    p4 = Point(1.0, 2.0, 3.0)
    assert not (p3 < p4)

    p5 = Point(1.0, 2.0, 3.0)
    p6 = Point(1.0, 3.0, 3.0)
    assert p5 < p6

def test_point_greater_than():
    p1 = Point(2.0, 2.0, 3.0)
    p2 = Point(1.0, 2.0, 3.0)
    assert p1 > p2

    p3 = Point(1.0, 2.0, 3.0)
    p4 = Point(1.0, 2.0, 3.0)
    assert not (p3 > p4)

def test_point_less_than_or_equal():
    p1 = Point(1.0, 2.0, 3.0)
    p2 = Point(1.0, 2.0, 3.0)
    p3 = Point(2.0, 2.0, 3.0)

    assert p1 <= p2
    assert p1 <= p3
    assert not (p3 <= p1)

def test_point_greater_than_or_equal():
    p1 = Point(1.0, 2.0, 3.0)
    p2 = Point(1.0, 2.0, 3.0)
    p3 = Point(0.0, 2.0, 3.0)

    assert p1 >= p2
    assert p1 >= p3
    assert not (p3 >= p1)

def test_point_comparison_with_none_values():
    p1 = Point(None, 2.0, 3.0)
    p2 = Point(None, 2.0, 3.0)
    p3 = Point(None, 3.0, 3.0)

    assert p1 == p2
    assert p1 != p3

def test_point_comparison_with_edge_cases():
    p1 = Point(0.0, 0.0, 0.0)
    p2 = Point(0.0, 0.0, 0.0)
    assert p1 == p2
    assert p1 <= p2
    assert p1 >= p2

    p3 = Point(-1.0, -2.0, -3.0)
    p4 = Point(-2.0, -2.0, -3.0)
    assert p4 < p3
