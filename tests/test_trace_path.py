import pytest
import numpy as np
from unittest.mock import Mock, patch
from gscrib import TracePath, GCodeBuilder
from gscrib.writers import BaseWriter


# --------------------------------------------------------------------
# Fixtures and helper classes
# --------------------------------------------------------------------

@pytest.fixture
def tracer(builder):
    return TracePath(builder)

@pytest.fixture
def mock_writer():
    return MockWriter()

@pytest.fixture
def mock_parametric():
    with patch('gscrib.trace_path.TracePath.parametric') as mock_parametric:
        yield mock_parametric

@pytest.fixture
def builder(mock_writer):
    builder = GCodeBuilder()
    builder._writers = [mock_writer]
    return builder

class MockWriter(BaseWriter):
    def __init__(self):
        self.written_lines = []
        self.is_connected = False

    def connect(self):
        self.is_connected = True

    def disconnect(self, wait=True):
        self.is_connected = False

    def write(self, data: bytes):
        self.written_lines.append(data.decode('utf-8').strip())


# --------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------

# Test path functions

def test_arc_quarter_circle(tracer, builder):
    builder.move(x=10, y=0)
    builder.set_resolution(2.0)
    tracer.arc(target=(0, 10), center=(-10, 0))
    final_pos = builder.position
    assert np.isclose(final_pos.x, 0, atol=0.1)
    assert np.isclose(final_pos.y, 10, atol=0.1)

def test_arc_with_z(tracer, builder):
    builder.move(x=10, y=0, z=0)
    builder.set_resolution(2.0)
    tracer.arc(target=(0, 10, 5), center=(-10, 0))
    final_pos = builder.position
    assert np.isclose(final_pos.x, 0, atol=0.1)
    assert np.isclose(final_pos.y, 10, atol=0.1)
    assert np.isclose(final_pos.z, 5, atol=0.1)

def test_circle(tracer, builder):
    builder.move(x=10, y=0)
    builder.set_resolution(2.0)
    tracer.circle(center=(-10, 0))
    final_pos = builder.position
    assert np.isclose(final_pos.x, 10, atol=0.1)
    assert np.isclose(final_pos.y, 0, atol=0.1)

def test_arc_radius(tracer, builder):
    builder.set_resolution(2.0)
    tracer.arc_radius(target=(10, 10), radius=10)
    final_pos = builder.position
    assert np.isclose(final_pos.x, 10, atol=0.1)
    assert np.isclose(final_pos.y, 10, atol=0.1)

def test_spline(tracer, builder):
    builder.set_resolution(2.0)
    tracer.spline([(5, 5), (10, -5), (15, 0)])
    final_pos = builder.position
    assert np.isclose(final_pos.x, 15, atol=0.1)
    assert np.isclose(final_pos.y, 0, atol=0.1)

def test_spline_relative(tracer, builder):
    builder.set_distance_mode("relative")
    builder.set_resolution(2.0)
    tracer.spline([(5, 5), (10, -5), (15, 0)])
    final_pos = builder.position
    assert np.isclose(final_pos.x, 30, atol=0.1)
    assert np.isclose(final_pos.y, 0, atol=0.1)

def test_spline_with_z(tracer, builder):
    builder.set_resolution(2.0)
    tracer.spline([(5, 5, 2), (10, -5, 4), (15, 0, 6)])
    final_pos = builder.position
    assert np.isclose(final_pos.x, 15, atol=0.1)
    assert np.isclose(final_pos.y, 0, atol=0.1)
    assert np.isclose(final_pos.z, 6, atol=0.1)

def test_spline_with_mixed_coordinates(tracer, builder):
    builder.set_resolution(2.0)
    tracer.spline([(5, 5), (10, -5, 4), (15, 0)])
    final_pos = builder.position
    assert np.isclose(final_pos.x, 15, atol=0.1)
    assert np.isclose(final_pos.y, 0, atol=0.1)
    assert np.isclose(final_pos.z, 4, atol=0.1)

def test_helix(tracer, builder):
    builder.set_resolution(2.0)
    tracer.helix(target=(5, 0), center=(-10, 0), turns=3)
    final_pos = builder.position
    assert np.isclose(final_pos.x, 5, atol=0.1)
    assert np.isclose(final_pos.y, 0, atol=0.1)

def test_helix_with_z(tracer, builder):
    builder.set_resolution(2.0)
    tracer.helix(target=(5, 0, 10), center=(-10, 0), turns=3)
    final_pos = builder.position
    assert np.isclose(final_pos.x, 5, atol=0.1)
    assert np.isclose(final_pos.y, 0, atol=0.1)
    assert np.isclose(final_pos.z, 10, atol=0.1)

def test_thread(tracer, builder):
    builder.set_resolution(2.0)
    tracer.thread(target=(10, 0, 10), pitch=1)
    final_pos = builder.position
    assert np.isclose(final_pos.x, 10, atol=0.1)
    assert np.isclose(final_pos.y, 0, atol=0.1)
    assert np.isclose(final_pos.z, 10, atol=0.1)

def test_thread_with_z(tracer, builder):
    builder.set_resolution(2.0)
    tracer.thread(target=(10, 0, 10), pitch=1)
    final_pos = builder.position
    assert np.isclose(final_pos.x, 10, atol=0.1)
    assert np.isclose(final_pos.y, 0, atol=0.1)
    assert np.isclose(final_pos.z, 10, atol=0.1)

def test_spiral(tracer, builder):
    builder.set_resolution(2.0)
    tracer.spiral(target=(10, 0), turns=2)
    final_pos = builder.position
    assert np.isclose(final_pos.x, 10, atol=0.1)
    assert np.isclose(final_pos.y, 0, atol=0.1)

def test_spiral_with_z(tracer, builder):
    builder.set_resolution(2.0)
    tracer.spiral(target=(10, 0, 5), turns=2)
    final_pos = builder.position
    assert np.isclose(final_pos.x, 10, atol=0.1)
    assert np.isclose(final_pos.y, 0, atol=0.1)
    assert np.isclose(final_pos.z, 5, atol=0.1)

def test_polyline(tracer, builder):
    tracer.polyline(targets=[(5, 5), (10, -5), (15, 0)])
    final_pos = builder.position
    assert np.isclose(final_pos.x, 15, atol=0.1)
    assert np.isclose(final_pos.y, 0, atol=0.1)
    assert np.isclose(final_pos.z, 0, atol=0.1)

def test_polyline_relative(tracer, builder):
    builder.set_distance_mode("relative")
    tracer.polyline(targets=[(5, 5), (10, -5), (15, 0)])
    final_pos = builder.position
    assert np.isclose(final_pos.x, 30, atol=0.1)
    assert np.isclose(final_pos.y, 0, atol=0.1)
    assert np.isclose(final_pos.z, 0, atol=0.1)

def test_parametric(tracer, builder):
    def circle(thetas):
        x = 10 * np.cos(2 * np.pi * thetas)
        y = 10 * np.sin(2 * np.pi * thetas)
        z = np.zeros_like(thetas)
        return np.column_stack((x, y, z))

    builder.set_resolution(2.0)
    tracer.parametric(circle, length=2 * np.pi * 10)
    final_pos = builder.position
    assert np.isclose(final_pos.x, 10, atol=0.1)
    assert np.isclose(final_pos.y, 0, atol=0.1)
    assert np.isclose(final_pos.z, 0, atol=0.1)

def test_estimate_length(tracer):
    def line(thetas):
        return np.column_stack((
            thetas,
            thetas,
            np.zeros_like(thetas)
        ))

    length = tracer.estimate_length(100, line)
    assert pytest.approx(length, 0.01) == np.sqrt(2)

# Test filter segments

def test_filter_segments(tracer, builder):
    points = np.array([[0, 0], [0.05, 0], [0.1, 0]])
    builder.set_resolution(0.1)
    filtered = tracer._filter_segments(points)

    # Should contain first and last points
    assert filtered.shape == (2, 2)
    assert np.array_equal(filtered[0], points[0])
    assert np.array_equal(filtered[-1], points[-1])

def test_filter_segments_no_points(tracer):
    points = np.array([])
    filtered = tracer._filter_segments(points)
    assert filtered.size == 0  # Should return empty array

def test_filter_segments_single_point(tracer):
    points = np.array([[0, 0]])
    filtered = tracer._filter_segments(points)
    assert filtered.shape == (1, 2)  # Should return point
    assert np.array_equal(filtered, points)

def test_filter_segments_all_points_below_resolution(tracer, builder):
    builder.set_resolution(10.0)
    points = np.array([[0, 0], [0.5, 0], [0.5, 0], [0.9, 0]])
    filtered = tracer._filter_segments(points)
    assert filtered.shape == (2, 2) # Should keep first and last
    assert np.array_equal(filtered[0], points[0])
    assert np.array_equal(filtered[-1], points[-1])

def test_filter_segments_some_points_below_resolution(tracer, builder):
    builder.set_resolution(1.0)
    points = np.array([[0, 0], [0.5, 0.5], [1.5, 1.5], [2.5, 2.5]])
    filtered = tracer._filter_segments(points)
    assert filtered.shape == (3, 2)
    assert np.array_equal(filtered[0], points[0])
    assert np.array_equal(filtered[1], points[2])
    assert np.array_equal(filtered[2], points[3])

def test_filter_segments_close_to_resolution(tracer, builder):
    builder.set_resolution(0.1)
    points = np.array([[0, 0], [0.99, 0], [2.01, 0], [3.0, 0]])
    filtered = tracer._filter_segments(points)
    assert filtered.shape == (4, 2)
    assert np.array_equal(filtered[0], points[0])
    assert np.array_equal(filtered[1], points[1])
    assert np.array_equal(filtered[2], points[2])
    assert np.array_equal(filtered[3], points[3])

def test_filter_segments_large_gaps(tracer, builder):
    builder.set_resolution(1.0)
    points = np.array([[0, 0], [5, 0], [10, 0]])
    filtered = tracer._filter_segments(points)
    assert filtered.shape == (3, 2)
    assert np.array_equal(filtered, points)

# Test distance modes

def test_arc_distance_modes(tracer, builder):
    # Test in absolute mode (default)
    builder.set_distance_mode("absolute")
    builder.set_axis((0, 0, 0))
    builder.move(x=10, y=0)
    builder.set_resolution(2.0)
    tracer.arc(target=(0, 10), center=(-10, 0))
    absolute_commands = len(builder._writers[0].written_lines)
    absolute_final_pos = builder.position

    # Reset and test in relative mode
    builder._writers[0].written_lines.clear()
    builder.set_distance_mode("relative")
    builder.set_axis((0, 0, 0))
    builder.move(x=10, y=0)
    tracer.arc(target=(-10, 10), center=(-10, 0))
    relative_commands = len(builder._writers[0].written_lines)
    relative_final_pos = builder.position

    # Verify same number of points generated
    assert absolute_commands == relative_commands

    # Verify same final position reached
    assert np.isclose(absolute_final_pos.x, relative_final_pos.x, atol=0.1)
    assert np.isclose(absolute_final_pos.y, relative_final_pos.y, atol=0.1)

def test_arc_relative_parametric(tracer, builder, mock_parametric):
    builder.parametric = Mock()
    builder.set_distance_mode("relative")
    builder.move(x=10, y=10)
    builder.set_resolution(2.0)
    tracer.arc(target=(10, 10), center=(5, 5))

    mock_parametric.assert_called_once()
    parametric_function = mock_parametric.call_args[0][0]
    result = parametric_function(np.array([1.0]))
    assert np.allclose(result, (20, 20, 0), atol=0.1)

def test_arc_radius_relative_parametric(tracer, builder, mock_parametric):
    builder.parametric = Mock()
    builder.set_distance_mode("relative")
    builder.move(x=10, y=10)
    builder.set_resolution(2.0)
    tracer.arc_radius(target=(10, 10), radius=7.07)

    mock_parametric.assert_called_once()
    parametric_function = mock_parametric.call_args[0][0]
    result = parametric_function(np.array([1.0]))
    assert np.allclose(result, (20, 20, 0), atol=0.1)

def test_helix_relative_parametric(tracer, builder, mock_parametric):
    builder.parametric = Mock()
    builder.set_distance_mode("relative")
    builder.move(x=10, y=10)
    builder.set_resolution(2.0)
    tracer.helix(target=(10, 10), center=(5, 5))

    mock_parametric.assert_called_once()
    parametric_function = mock_parametric.call_args[0][0]
    result = parametric_function(np.array([1.0]))
    assert np.allclose(result, (20, 20, 0), atol=0.1)

def test_spline_relative_parametric(tracer, builder, mock_parametric):
    builder.parametric = Mock()
    builder.set_distance_mode("relative")
    builder.move(x=10, y=10)
    builder.set_resolution(2.0)
    tracer.spline(targets=[(0, 0), (10, 10), (10, 10)])

    mock_parametric.assert_called_once()
    parametric_function = mock_parametric.call_args[0][0]
    result = parametric_function(np.array([1.0]))
    assert np.allclose(result, (30, 30, 0), atol=0.1)

def test_thread_relative_parametric(tracer, builder, mock_parametric):
    builder.parametric = Mock()
    builder.set_distance_mode("relative")
    builder.move(x=10, y=10)
    builder.set_resolution(2.0)
    tracer.thread(target=(10, 10))

    mock_parametric.assert_called_once()
    parametric_function = mock_parametric.call_args[0][0]
    result = parametric_function(np.array([1.0]))
    assert np.allclose(result, (20, 20, 0), atol=0.1)

# Test spline control points

def test_spline_points_close_to_targets(tracer, builder, mock_parametric):
    resolution = 0.1
    points = [(5, 5, 5), (10, 10, 10), (15, 15, 15)]

    builder.set_resolution(resolution)
    tracer.spline(targets=points)

    mock_parametric.assert_called_once()
    parametric_function = mock_parametric.call_args[0][0]
    segments = parametric_function(np.linspace(0, 1, 100))
    results = tracer._filter_segments(segments)

    for point in points:
        assert any([
            np.allclose(point, result, atol=resolution)
            for result in results
        ])

# Test resolution

def test_resolution_affects_segment_count(tracer, builder, mock_writer):
    builder.move(x=10, y=0)

    # Count moves with coarse resolution
    builder.set_resolution(3.0)
    initial_moves = len(mock_writer.written_lines)
    tracer.arc(target=(0, 10), center=(-10, 0))
    coarse_moves = len(mock_writer.written_lines) - initial_moves

    # Reset and count moves with fine resolution
    mock_writer.written_lines.clear()
    builder.move(x=10, y=0)
    builder.set_resolution(2.0)
    initial_moves = len(mock_writer.written_lines)
    tracer.arc(target=(0, 10), center=(-10, 0))
    fine_moves = len(mock_writer.written_lines) - initial_moves

    # Fine resolution should generate more moves
    assert fine_moves > coarse_moves

# Test error handling

def test_arc_invalid_radius(tracer):
    with pytest.raises(ValueError):
        tracer.arc(target=(10, 0), center=(0, 0))

def test_arc_invalid_center(tracer):
    with pytest.raises(ValueError):
        tracer.arc(target=(10, 0), center=(0, -5))

def test_arc_radius_invalid(tracer):
    with pytest.raises(ValueError):
        tracer.arc_radius(target=(10, 10), radius=0)

def test_spline_invalid_targets(tracer):
    with pytest.raises(ValueError):
        tracer.spline(targets=[(0, 0)])

def test_helix_invalid_turns(tracer):
    with pytest.raises(ValueError):
        tracer.helix(target=(5, 0), center=(-10, 0), turns=0)

def test_thread_invalid_pitch(tracer):
    with pytest.raises(ValueError):
        tracer.thread(target=(10, 0, 10), pitch=0)
