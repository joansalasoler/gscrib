import numpy
import pytest
from unittest.mock import patch
from numpy import ndarray, float32
from scipy.interpolate import RectBivariateSpline

from gscrib.excepts import ImageLoadError
from gscrib.heightmaps import RasterHeightMap
from gscrib.heightmaps.raster_heightmap import UINT8_MAX, UINT16_MAX


# --------------------------------------------------------------------
# Fixtures and helper classes
# --------------------------------------------------------------------

@pytest.fixture
def height_map(sample_uint8_image):
    return RasterHeightMap(sample_uint8_image)

@pytest.fixture
def sample_uint8_image():
    height, width = 10, 20
    image_data = numpy.zeros((height, width), dtype=numpy.uint8)

    for i in range(height):
        for j in range(width):
            image_data[i, j] = (i + j) * 12 % 256

    return image_data


@pytest.fixture
def sample_uint16_image():
    height, width = 10, 20
    image_data = numpy.zeros((height, width), dtype=numpy.uint16)

    for i in range(height):
        for j in range(width):
            image_data[i, j] = (i + j) * 3000 % 65536

    return image_data


# --------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------

def test_height_map_init(sample_uint8_image):
    height_map = RasterHeightMap(sample_uint8_image)
    assert isinstance(height_map._height_map, ndarray)
    assert isinstance(height_map._interpolator, RectBivariateSpline)
    assert height_map._height_map.dtype == float32
    assert height_map._scale_z == 1.0
    assert height_map._tolerance == 0.378
    assert height_map.get_width() == 20
    assert height_map.get_height() == 10

def test_init_with_uint8_image(sample_uint8_image):
    height_map = RasterHeightMap(sample_uint8_image)
    assert numpy.all(height_map._height_map >= 0)
    assert numpy.all(height_map._height_map <= 1)

    sample_value = sample_uint8_image[5, 5]
    map_value = height_map._height_map[5, 5]
    expected = float(sample_value) / UINT8_MAX
    assert map_value == pytest.approx(expected)

def test_init_with_uint16_image(sample_uint16_image):
    height_map = RasterHeightMap(sample_uint16_image)
    assert numpy.all(height_map._height_map >= 0)
    assert numpy.all(height_map._height_map <= 1)

    sample_value = sample_uint16_image[5, 5]
    map_value = height_map._height_map[5, 5]
    expected = float(sample_value) / UINT16_MAX
    assert map_value == pytest.approx(expected)

@patch('cv2.imread')
def test_create_from_path_success(mock_imread, sample_uint8_image):
    mock_imread.return_value = sample_uint8_image
    height_map = RasterHeightMap.from_path('test_image.png')
    assert isinstance(height_map, RasterHeightMap)
    assert height_map._scale_z == 1.0

@patch('cv2.imread')
def test_create_from_path_failure(mock_imread):
    mock_imread.return_value = None

    with pytest.raises(ImageLoadError):
        RasterHeightMap.from_path('nonexistent_image.png')

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
    height = height_map.get_depth_at(5, 5)

    assert isinstance(height, float)
    assert height <= 1.0
    assert height >= 0.0

def test_get_depth_at_with_scale(height_map):
    scale_factor = 2.5
    height = height_map.get_depth_at(5, 5)
    height_map.set_scale(scale_factor)
    scaled_height = height_map.get_depth_at(5, 5)

    assert height_map._scale_z == scale_factor
    assert scaled_height == scale_factor * height
    assert scaled_height <= scale_factor
    assert scaled_height >= 0.0

def test_sample_path(height_map):
    line = numpy.array([2.0, 5.0, 8.0, 5.0])
    points = height_map.sample_path(line)

    assert isinstance(points, ndarray)
    assert points.shape[1] == 3
    assert points[0][0] == 2.0
    assert points[0][1] == 5.0
    assert points[-1][0] == 8.0
    assert points[-1][1] == 5.0

    height_map.set_tolerance(0.5)
    points_high = height_map.sample_path(line)
    assert len(points_high) <= len(points)

def test_filter_points(height_map):
    test_points = numpy.array([
        [0, 0, 0.0],
        [1, 0, 0.005],  # Below tolerance
        [2, 0, 0.02],   # Above tolerance
        [3, 0, 0.025],  # Below tolerance
        [4, 0, 0.1]     # Above tolerance
    ])

    filtered = height_map._filter_points(test_points, 0.01)

    assert len(filtered) == 3
    assert numpy.array_equal(filtered[0], test_points[0])
    assert numpy.array_equal(filtered[1], test_points[2])
    assert numpy.array_equal(filtered[2], test_points[4])

def test_sample_path_invalid_input(height_map):
    with pytest.raises(ValueError):
        height_map.sample_path([0, 0, 1])
