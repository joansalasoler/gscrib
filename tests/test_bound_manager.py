import pytest
from gscrib.geometry import BoundManager, Point


# --------------------------------------------------------------------
# Fixtures and helper classes
# --------------------------------------------------------------------

@pytest.fixture
def manager():
    return BoundManager()


# --------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------

def test_bound_manager_initialization(manager):
    assert isinstance(manager._bounds, dict)
    assert len(manager._bounds) == 0

def test_get_bounds_nonexistent(manager):
    min_bound, max_bound = manager.get_bounds("feed-rate")
    assert min_bound is None
    assert max_bound is None

def test_set_bounds_numeric(manager):
    manager.set_bounds("feed-rate", 0, 100)
    min_bound, max_bound = manager.get_bounds("feed-rate")
    assert min_bound == 0
    assert max_bound == 100

def test_set_bounds_point(manager):
    min_point = Point(0, 0, 0)
    max_point = Point(100, 100, 100)
    manager.set_bounds("axes", min_point, max_point)
    min_bound, max_bound = manager.get_bounds("axes")
    assert min_bound == min_point
    assert max_bound == max_point

def test_validate_within_bounds(manager):
    manager.set_bounds("feed-rate", 0, 100)
    manager.validate("feed-rate", 0)
    manager.validate("feed-rate", 50)
    manager.validate("feed-rate", 100)

# Error handling tests

def test_set_bounds_invalid_property(manager):
    with pytest.raises(ValueError):
        manager.set_bounds("invalid-property", 0, 100)

def test_set_bounds_invalid_bounds(manager):
    with pytest.raises(ValueError):
        manager.set_bounds("feed-rate", 100, 0)

def test_set_bounds_invalid_type_numeric(manager):
    with pytest.raises(TypeError):
        manager.set_bounds("feed-rate", Point(0, 0, 0), 1)

def test_set_bounds_invalid_type_point(manager):
    with pytest.raises(TypeError):
        manager.set_bounds("axes", 0, Point(1, 1, 1))

    with pytest.raises(TypeError):
        manager.set_bounds("axes", Point(0, 0, 0), 1)

def test_validate_out_of_bounds(manager):
    manager.set_bounds("feed-rate", 0, 100)

    with pytest.raises(ValueError):
        manager.validate("feed-rate", -1)

    with pytest.raises(ValueError):
        manager.validate("feed-rate", 101)

def test_validate_out_of_bounds_point(manager):
    min_point = Point(0, 0, 0)
    max_point = Point(100, 100, 100)

    manager.set_bounds("axes", min_point, max_point)
    manager.validate("axes", Point(50, 50, 50))

    with pytest.raises(ValueError):
        manager.validate("axes", Point(-1, 50, 50))

    with pytest.raises(ValueError):
        manager.validate("axes", Point(0, 0, 101))

def test_validate_undefined_bounds(manager):
    manager.validate("feed-rate", 1000) # Should not raise exception
