import pytest

from numpy.testing import assert_array_equal

from gscrib import Point
from gscrib import GCodeCore
from gscrib.writers import BaseWriter


# --------------------------------------------------------------------
# Fixtures and helper classes
# --------------------------------------------------------------------

@pytest.fixture
def mock_writer():
    return MockWriter()

@pytest.fixture
def builder(mock_writer):
    builder = GCodeCore()
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

# Test Initialization

def test_default_initialization():
    builder = GCodeCore()
    assert builder.position == Point.unknown()
    assert not builder.distance_mode.is_relative
    assert len(builder._writers) > 0

def test_custom_initialization():
    builder = GCodeCore(
        output="test.gcode",
        print_lines=True,
        decimal_places=3,
        comment_symbols=";",
        x_axis="A",
        y_axis="B",
        z_axis="C"
    )

    assert len(builder._writers) >= 2  # File and stdout writers
    assert builder._formatter._decimal_places == 3
    assert builder._formatter._labels == {"X": "A", "Y": "B", "Z": "C"}

# Test distance modes

def test_absolute_mode_mode(builder, mock_writer):
    builder.set_distance_mode("absolute")
    assert not builder.distance_mode.is_relative
    assert "G90" in mock_writer.written_lines

def test_relative_mode_mode(builder, mock_writer):
    builder.set_distance_mode("relative")
    assert builder.distance_mode.is_relative
    assert "G91" in mock_writer.written_lines

def test_distance_mode_switching(builder, mock_writer):
    builder.set_distance_mode("relative")
    builder.set_distance_mode("absolute")
    builder.set_distance_mode("relative")
    assert "G91" in mock_writer.written_lines[0]
    assert "G90" in mock_writer.written_lines[1]
    assert "G91" in mock_writer.written_lines[2]
    assert builder.distance_mode.is_relative

# Test position management

def test_set_axis(builder, mock_writer):
    builder.set_axis(x=10, y=20, z=30)
    assert builder.position == Point(10, 20, 30)
    assert "G92 X10 Y20 Z30" in mock_writer.written_lines
    builder.set_axis(x=50, y=20, z=30)
    assert builder.position == Point(50, 20, 30)

def test_set_axis_partial(builder, mock_writer):
    builder.set_axis(x=10)
    assert builder.position == Point(10, None, None)
    assert "G92 X10" in mock_writer.written_lines

def test_set_axis_additional_axis(builder, mock_writer):
    builder.set_axis(E=20)
    assert builder.position == Point(None, None, None)
    assert "G92 E20" in mock_writer.written_lines
    assert builder.get_parameter('E') == 20
    assert builder.get_parameter('X') == None
    assert builder.get_parameter('Y') == None
    assert builder.get_parameter('Z') == None

def test_get_parameter(builder):
    builder.move(x=10, y=20, F=1000)
    assert builder.get_parameter('F') == 1000
    assert builder.get_parameter('X') == 10
    assert builder.get_parameter('Y') == 20
    assert builder.get_parameter('Z') == None

    builder.rapid(z=15, y=5, e=100)
    assert builder.get_parameter('E') == 100
    assert builder.get_parameter('F') == 1000
    assert builder.get_parameter('X') == None
    assert builder.get_parameter('Y') == 5
    assert builder.get_parameter('Z') == 15

# Test movement commands

def test_rapid_move(builder, mock_writer):
    builder.rapid(x=10, y=20, z=30)
    assert builder.position == Point(10, 20, 30)
    assert "G0 X10 Y20 Z30" in mock_writer.written_lines[0]

    builder.rapid(Point(100, y=200, z=300))
    assert builder.position == Point(100, 200, 300)
    assert "G0 X100 Y200 Z300" in mock_writer.written_lines[1]

def test_linear_move(builder, mock_writer):
    builder.move(x=10, y=20, z=30)
    assert builder.position == Point(10, 20, 30)
    assert "G1 X10 Y20 Z30" in mock_writer.written_lines[0]

    builder.move(Point(100, y=200, z=300))
    assert builder.position == Point(100, 200, 300)
    assert "G1 X100 Y200 Z300" in mock_writer.written_lines[1]

def test_rapid_absolute(builder, mock_writer):
    builder.set_distance_mode("relative")
    builder.rapid_absolute(x=10, y=20)
    assert builder.position == Point(10, 20, None)
    assert "G90" in mock_writer.written_lines
    assert "G0 X10 Y20" in mock_writer.written_lines
    assert builder.distance_mode.is_relative

    builder.rapid_absolute(Point(z=30))
    assert builder.position == Point(10, 20, 30)
    assert "G0 Z30" in mock_writer.written_lines

def test_move_absolute(builder, mock_writer):
    builder.set_distance_mode("relative")
    builder.move_absolute(x=10, y=20)
    assert builder.position == Point(10, 20, None)
    assert "G90" in mock_writer.written_lines
    assert "G1 X10 Y20" in mock_writer.written_lines
    assert builder.distance_mode.is_relative

    builder.move_absolute(Point(z=30))
    assert builder.position == Point(10, 20, 30)
    assert "G1 Z30" in mock_writer.written_lines

def test_relative_moves(builder, mock_writer):
    builder.set_distance_mode("relative")
    builder.move(x=10, y=20)
    builder.move(x=5, y=15)
    assert "G91" in mock_writer.written_lines[0]
    assert "G1 X10 Y20" in mock_writer.written_lines[1]
    assert "G1 X5 Y15" in mock_writer.written_lines[2]
    assert builder.position == Point(15, 35, 0)

def test_absolute_moves(builder, mock_writer):
    builder.set_distance_mode("absolute")
    builder.move(x=10, y=20)
    builder.move(x=5, y=15)
    assert "G90" in mock_writer.written_lines[0]
    assert "G1 X10 Y20" in mock_writer.written_lines[1]
    assert "G1 X5 Y15" in mock_writer.written_lines[2]
    assert builder.position == Point(5, 15, 0)

def test_absolute_mode_context_manager(builder, mock_writer):
    builder.set_distance_mode("relative")
    builder.move(x=100, y=100)
    mock_writer.written_lines.clear()

    with builder.absolute_mode():
        assert not builder.distance_mode.is_relative
        builder.move(x=10, y=20, z=30)
        builder.move(x=5, y=10, z=15)

    assert builder.distance_mode.is_relative
    assert builder.position == Point(5, 10, 15)
    assert "G90" in mock_writer.written_lines[0]
    assert "G1 X10 Y20 Z30" in mock_writer.written_lines[1]
    assert "G1 X5 Y10 Z15" in mock_writer.written_lines[2]
    assert "G91" in mock_writer.written_lines[3]

def test_relative_mode_context_manager(builder, mock_writer):
    builder.set_distance_mode("absolute")
    builder.move(x=100, y=100)
    mock_writer.written_lines.clear()

    with builder.relative_mode():
        assert builder.distance_mode.is_relative
        builder.move(x=10, y=20, z=30)
        builder.move(x=5, y=10, z=15)

    assert not builder.distance_mode.is_relative
    assert builder.position == Point(115, 130, 45)
    assert "G91" in mock_writer.written_lines[0]
    assert "G1 X10 Y20 Z30" in mock_writer.written_lines[1]
    assert "G1 X5 Y10 Z15" in mock_writer.written_lines[2]
    assert "G90" in mock_writer.written_lines[3]

# Test transformations

def test_translation(builder, mock_writer):
    builder.transform.translate(10, 20, 0)
    builder.move(x=0, y=0)
    assert "G1 X10 Y20" in mock_writer.written_lines

def test_rotation(builder, mock_writer):
    builder.transform.rotate(90)  # 90 degrees
    builder.move(x=10, y=0)
    written_line = mock_writer.written_lines[-1]
    assert "G1" in written_line
    assert "Y10" in written_line
    assert "X0" in written_line

def test_scaling(builder, mock_writer):
    builder.transform.scale(2)
    builder.move(x=10, y=10)
    assert "G1 X20 Y20" in mock_writer.written_lines

def test_reflection(builder, mock_writer):
    builder.transform.reflect([1, 1, 0])
    builder.move(x=10, y=10)
    assert "G1 X-10 Y-10" in mock_writer.written_lines

def test_matrix_stack(builder, mock_writer):
    builder.transform.translate(10, 0)
    builder.transform.save_state()
    builder.transform.translate(10, 0)
    builder.move(x=0, y=0)
    builder.transform.restore_state()
    builder.move(x=0, y=0)
    assert "G1 X20 Y0" in mock_writer.written_lines
    assert "G1 X10 Y0" in mock_writer.written_lines

def test_combined_transformations(builder, mock_writer):
    builder.transform.translate(10, 0)
    builder.transform.rotate(90)
    builder.transform.scale(2)
    builder.move(x=5, y=0)
    assert builder.position == Point(5, 0, 0)
    assert "G1 X0 Y30" in mock_writer.written_lines[-1]

def test_relative_with_transformations(builder, mock_writer):
    builder.transform.translate(10, 0)
    builder.transform.scale(3)
    builder.set_distance_mode("relative")
    builder.move(x=5, y=0)
    builder.move(x=5, y=10)
    assert builder.position == Point(10, 10, 0)
    assert "G91" in mock_writer.written_lines[0]
    assert "G1 X15 Y0" in mock_writer.written_lines[1]
    assert "G1 X15 Y30" in mock_writer.written_lines[2]

def test_current_transform_context_manager(builder, mock_writer):
    t = builder.transform
    t.save_state()

    state_copy, stack_copy = t._copy_state()

    with builder.current_transform():
        t.save_state()

        t.translate(10, 0, 0)
        point1 = t.apply_transform(Point(0, 0, 0))
        assert point1 == Point(10, 0, 0)

        t.save_state()
        t.restore_state()

    # Should always revert to previous state
    point2 = t.apply_transform(Point(0, 0, 0))

    state = t._current_transform
    assert len(t._transforms_stack) == 1
    assert_array_equal(state_copy._matrix, state._matrix)
    assert_array_equal(state_copy._inverse, state._inverse)
    assert_array_equal(state_copy._pivot, state._pivot)
    assert_array_equal(state_copy._from_pivot, state._from_pivot)
    assert_array_equal(state_copy._to_pivot, state._to_pivot)
    assert point2 == Point(0, 0, 0)

# Test comments

def test_comment_writing(builder, mock_writer):
    builder.comment("Test comment")
    assert "; Test comment" in mock_writer.written_lines

def test_comment_with_args(builder, mock_writer):
    builder.comment("Position", "X:", 10, "Y:", 20)
    assert "; Position X: 10 Y: 20" in mock_writer.written_lines

# Test multiple writers

def test_multiple_writers():
    writer1 = MockWriter()
    writer2 = MockWriter()
    builder = GCodeCore()
    builder._writers = [writer1, writer2]

    builder.move(x=10)
    assert len(writer1.written_lines) == 1
    assert len(writer2.written_lines) == 1
    assert writer1.written_lines == writer2.written_lines

# Test resource management

def test_context_manager():
    mock_writer = MockWriter()

    with GCodeCore() as builder:
        builder._writers = [mock_writer]
        builder.move(x=10)

    assert not mock_writer.is_connected

def test_teardown(builder, mock_writer):
    builder.move(x=10)
    builder.teardown()
    assert not mock_writer.is_connected
