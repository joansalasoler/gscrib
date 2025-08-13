import pytest
from unittest.mock import Mock
from gscrib.hooks import heightmap_hook
from gscrib.geometry import Point
from gscrib import ParamsDict, GState


# --------------------------------------------------------------------
# Fixtures and helper classes
# --------------------------------------------------------------------

@pytest.fixture
def mock_heightmap():
    heightmap = Mock()
    heightmap.get_depth_at.return_value = 5.0
    return heightmap

@pytest.fixture
def mock_state():
    return Mock(spec=GState)


# --------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------

def test_heightmap_hook_creation(mock_heightmap):
    hook = heightmap_hook(mock_heightmap)
    assert callable(hook)

def test_heightmap_hook_sets_z_coordinate(mock_heightmap, mock_state):
    mock_heightmap.get_depth_at.return_value = 2.5
    hook = heightmap_hook(mock_heightmap)

    origin = Point(0, 0, 0)
    target = Point(10, 20, 0)
    params = ParamsDict()

    result = hook(origin, target, params, mock_state)

    mock_heightmap.get_depth_at.assert_called_once_with(10, 20)
    assert result.get('Z') == 2.5

def test_heightmap_hook_overwrites_existing_z(mock_heightmap, mock_state):
    mock_heightmap.get_depth_at.return_value = 3.7
    hook = heightmap_hook(mock_heightmap)

    origin = Point(0, 0, 0)
    target = Point(5, 15, 10)
    params = ParamsDict(Z=10)

    result = hook(origin, target, params, mock_state)

    mock_heightmap.get_depth_at.assert_called_once_with(5, 15)
    assert result.get('Z') == 3.7

def test_heightmap_hook_preserves_other_params(mock_heightmap, mock_state):
    mock_heightmap.get_depth_at.return_value = 1.2
    hook = heightmap_hook(mock_heightmap)

    origin = Point(0, 0, 0)
    target = Point(8, 12, 0)
    params = ParamsDict(F=1500, X=8, Y=12)

    result = hook(origin, target, params, mock_state)

    assert result.get('F') == 1500
    assert result.get('X') == 8
    assert result.get('Y') == 12
    assert result.get('Z') == 1.2

def test_heightmap_hook_with_negative_z(mock_heightmap, mock_state):
    mock_heightmap.get_depth_at.return_value = -2.3
    hook = heightmap_hook(mock_heightmap)

    origin = Point(0, 0, 0)
    target = Point(1, 1, 0)
    params = ParamsDict()

    result = hook(origin, target, params, mock_state)

    assert result.get('Z') == -2.3

def test_heightmap_hook_with_zero_coordinates(mock_heightmap, mock_state):
    mock_heightmap.get_depth_at.return_value = 0.5
    hook = heightmap_hook(mock_heightmap)

    origin = Point(5, 5, 0)
    target = Point(0, 0, 0)
    params = ParamsDict()

    result = hook(origin, target, params, mock_state)

    mock_heightmap.get_depth_at.assert_called_once_with(0, 0)
    assert result.get('Z') == 0.5
