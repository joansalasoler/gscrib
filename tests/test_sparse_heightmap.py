import os, tempfile
import numpy
import pytest
from numpy.testing import assert_array_almost_equal
from scipy.interpolate import LinearNDInterpolator

from gscrib.excepts import FileLoadError
from gscrib.heightmaps import SparseHeightMap


# --------------------------------------------------------------------
# Fixtures and helper classes
# --------------------------------------------------------------------

@pytest.fixture
def height_map(sample_data):
    return SparseHeightMap(sample_data)

@pytest.fixture
def sample_data():
    return numpy.array([
        [0.0, 0.0, 0.0],
        [0.0, 1.0, 1.0],
        [1.0, 0.0, 2.0],
        [1.0, 1.0, 3.0]
    ])


# --------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------

def test_height_map_init(sample_data):
    height_map = SparseHeightMap(sample_data)
    assert isinstance(height_map._interpolator, LinearNDInterpolator)
    assert height_map._scale_z == 1.0
    assert height_map._tolerance == 0.378

def test_create_from_path_success():
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("0,0,0\n0,1,1\n1,0,1\n1,1,2")
        temp_path = f.name

    try:
        height_map = SparseHeightMap.from_path(temp_path)
        assert isinstance(height_map, SparseHeightMap)
        assert height_map._scale_z == 1.0
        assert height_map._tolerance == 0.378
    finally:
        os.unlink(temp_path)

def test_from_path_invalid_data():
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("0,0\n0,1\n")  # 2 columns instead of 3
        temp_path = f.name

    try:
        with pytest.raises(FileLoadError):
            SparseHeightMap.from_path(temp_path)
    finally:
        os.unlink(temp_path)

def test_create_from_path_invalid_file():
    with pytest.raises(FileLoadError):
        SparseHeightMap.from_path('nonexistent_file.csv')

def test_set_scale(height_map):
    height_map.set_scale(2.0)
    assert height_map._scale_z == 2.0

    with pytest.raises(ValueError):
        height_map.set_scale(0)

    with pytest.raises(ValueError):
        height_map.set_scale(-1)

def test_set_tolerance(height_map):
    height_map.set_tolerance(0.05)
    assert height_map._tolerance == 0.05

    with pytest.raises(ValueError):
        height_map.set_tolerance(-0.1)

def test_get_depth_at(height_map):
    assert height_map.get_depth_at(0, 0) == pytest.approx(0.0)
    assert height_map.get_depth_at(0, 1) == pytest.approx(1.0)
    assert height_map.get_depth_at(1, 0) == pytest.approx(2.0)
    assert height_map.get_depth_at(1, 1) == pytest.approx(3.0)

def test_get_depth_at_with_scale(height_map):
    height_map.set_scale(2.0)
    assert height_map.get_depth_at(0, 0) == pytest.approx(0.0)
    assert height_map.get_depth_at(1, 1) == pytest.approx(6.0)

def test_sample_path(height_map):
    line = numpy.array([0, 0, 1, 1])
    points = height_map.sample_path(line)
    assert len(points) >= 2
    assert_array_almost_equal(points[0], [0, 0, 0])
    assert_array_almost_equal(points[-1], [1, 1, 3])

    height_map.set_tolerance(0.5)
    points_high = height_map.sample_path(line)
    assert len(points_high) <= len(points)

def test_filter_points(height_map):
    test_points = numpy.array([
        [0, 0, 0],
        [0.5, 0.5, 0.005],  # Below tolerance
        [1, 1, 2]
    ])

    filtered = height_map._filter_points(test_points, 0.01)

    assert len(filtered) == 2
    assert_array_almost_equal(filtered[0], [0, 0, 0])
    assert_array_almost_equal(filtered[-1], [1, 1, 2])

def test_sample_path_invalid_input(height_map):
    with pytest.raises(ValueError):
        height_map.sample_path([0, 0, 1])
