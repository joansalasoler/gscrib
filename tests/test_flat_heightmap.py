import pytest
from pytest import approx
from numpy import ndarray
from gscrib.heightmaps.flat_heightmap import FlatHeightMap


# --------------------------------------------------------------------
# Fixtures and helper classes
# --------------------------------------------------------------------

@pytest.fixture
def height_map():
    return FlatHeightMap()


# --------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------

def test_flat_heightmap_get_depth_at(height_map):
    depth = height_map.get_depth_at(0, 0)
    assert depth == 0.0

def test_sample_path(height_map):
    line = [2.0, 5.0, 8.0, 5.0]
    points = height_map.sample_path(line)
    assert isinstance(points, ndarray)
    assert points.shape[1] == 3
    assert points[0] == approx([2.0, 5.0, 0.0])
    assert points[-1] == approx([8.0, 5.0, 0.0])

def test_sample_path_invalid_input(height_map):
    with pytest.raises(ValueError):
        height_map.sample_path([0, 0, 1])
