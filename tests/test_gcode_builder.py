import pytest
from unittest.mock import patch
from gscrib import GCodeBuilder
from gscrib.geometry import Point
from gscrib.enums import *


# --------------------------------------------------------------------
# Fixtures and helper classes
# --------------------------------------------------------------------

@pytest.fixture
def builder(mock_write):
    return GCodeBuilder()

@pytest.fixture
def mock_write():
    with patch.object(GCodeBuilder, 'write') as mock:
        mock.last_statement = None

        def side_effect(statement):
            mock.last_statement = statement

        mock.side_effect = side_effect

        yield mock


# --------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------

def test_set_length_units(builder, mock_write):
    builder.set_length_units(LengthUnits.MILLIMETERS)
    assert builder.state.length_units == LengthUnits.MILLIMETERS
    assert mock_write.last_statement.startswith('G21')

def test_set_time_units(builder):
    builder.set_time_units(TimeUnits.SECONDS)
    assert builder.state.time_units == TimeUnits.SECONDS

def test_set_plane(builder, mock_write):
    builder.set_plane(Plane.XY)
    assert builder.state.plane == Plane.XY
    assert mock_write.last_statement.startswith('G17')

def test_set_direction(builder, mock_write):
    builder.set_direction(Direction.COUNTER)
    assert builder.state.direction == Direction.COUNTER

def test_set_resolution(builder):
    builder.set_resolution(0.5)
    assert builder.state.resolution == 0.5

def test_set_axis(builder, mock_write):
    builder.set_axis(x=10, y=20, z=30)
    assert builder.position == Point(10, 20, 30)
    assert mock_write.last_statement.startswith('G92 X10 Y20 Z30')

def test_set_axis_partial(builder, mock_write):
    builder.set_axis(x=10)
    assert builder.position == Point(10, None, None)
    assert mock_write.last_statement.startswith('G92 X10')

def test_set_distance_mode_absolute(builder, mock_write):
    builder.set_distance_mode(DistanceMode.ABSOLUTE)
    assert builder.state.distance_mode == DistanceMode.ABSOLUTE
    assert builder.state.distance_mode.is_relative == False
    assert mock_write.last_statement.startswith('G90')

def test_set_distance_mode_relative(builder, mock_write):
    builder.set_distance_mode(DistanceMode.RELATIVE)
    assert builder.state.distance_mode == DistanceMode.RELATIVE
    assert builder.state.distance_mode.is_relative == True
    assert mock_write.last_statement.startswith('G91')

def test_set_tool_power(builder, mock_write):
    builder.set_tool_power(1000.0)
    assert builder.state.tool_power == 1000.0
    assert mock_write.last_statement.startswith('S1000')

def test_set_tool_power_invalid(builder):
    with pytest.raises(ValueError):
        builder.set_tool_power(-100)

def test_set_feed_rate(builder, mock_write):
    builder.set_feed_rate(1000.0)
    assert builder.state.feed_rate == 1000.0
    assert mock_write.last_statement.startswith('F1000')

def test_set_feed_rate_invalid(builder):
    with pytest.raises(ValueError):
        builder.set_feed_rate(-100)

def test_set_fan_speed(builder, mock_write):
    builder.set_fan_speed(255)
    assert mock_write.last_statement.startswith('M106 P0 S255')
    builder.set_fan_speed(0)
    assert mock_write.last_statement.startswith('M106 P0 S0')

def test_set_fan_speed_invalid(builder):
    with pytest.raises(ValueError):
        builder.set_fan_speed(256)

    with pytest.raises(ValueError):
        builder.set_fan_speed(-1)

def test_tool_on(builder, mock_write):
    builder.tool_on(SpinMode.CLOCKWISE, 1000.0)
    assert builder.state.spin_mode == SpinMode.CLOCKWISE
    assert builder.state.tool_power == 1000.0
    assert mock_write.last_statement.startswith('S1000 M03')

def test_tool_on_invalid_mode(builder):
    with pytest.raises(ValueError):
        builder.tool_on(SpinMode.OFF, 1000.0)

def test_tool_off(builder, mock_write):
    builder.tool_on(SpinMode.CLOCKWISE, 1000.0)
    builder.tool_off()
    assert builder.state.spin_mode == SpinMode.OFF
    assert mock_write.last_statement.startswith('M05')

def test_power_on(builder, mock_write):
    builder.power_on(PowerMode.CONSTANT, 75.0)
    assert builder.state.power_mode == PowerMode.CONSTANT
    assert builder.state.tool_power == 75.0
    assert mock_write.last_statement.startswith('S75')

def test_power_off(builder):
    builder.power_on(PowerMode.CONSTANT, 75.0)
    builder.power_off()
    assert builder.state.power_mode == PowerMode.OFF

def test_tool_change(builder, mock_write):
    tool_number = 1
    builder.tool_change(ToolSwapMode.MANUAL, tool_number)
    assert builder.state.tool_swap_mode == ToolSwapMode.MANUAL
    assert builder.state.tool_number == tool_number
    assert mock_write.last_statement.startswith('T1')

def test_coolant_operations(builder):
    builder.coolant_on(CoolantMode.FLOOD)
    assert builder.state.coolant_mode == CoolantMode.FLOOD

    builder.coolant_off()
    assert builder.state.coolant_mode == CoolantMode.OFF

def test_sleep(builder, mock_write):
    builder.sleep(1.5)
    assert mock_write.last_statement.startswith('G04 P1.5')

    builder.set_time_units(TimeUnits.MILLISECONDS)
    builder.sleep(1500)
    assert mock_write.last_statement.startswith('G04 P1500')

def test_sleep_invalid_duration(builder):
    with pytest.raises(ValueError):
        builder.sleep(0.0005)  # Less than 1ms

    builder.set_time_units(TimeUnits.MILLISECONDS)

    with pytest.raises(ValueError):
        builder.sleep(0)  # Less than 1ms

def test_set_bed_temperature(builder, mock_write):
    builder.set_bed_temperature(60)
    assert mock_write.last_statement.startswith('M140 S60')

def test_set_hotend_temperature(builder, mock_write):
    builder.set_hotend_temperature(60)
    assert mock_write.last_statement.startswith('M104 S60')

def test_set_chamber_temperature(builder, mock_write):
    builder.set_chamber_temperature(60)
    assert mock_write.last_statement.startswith('M141 S60')

def test_pause_forced(builder, mock_write):
    builder.pause()
    assert mock_write.last_statement.startswith('M00')

def test_pause_optional(builder, mock_write):
    builder.pause(optional=True)
    assert mock_write.last_statement.startswith('M01')

def test_stop_without_reset(builder, mock_write):
    builder.stop()
    assert mock_write.last_statement.startswith('M02')

def test_stop_with_reset(builder, mock_write):
    builder.stop(reset=True)
    assert mock_write.last_statement.startswith('M30')

def test_wait(builder, mock_write):
    builder.wait()
    assert mock_write.last_statement.startswith('M400')

def test_current_axis_position(builder):
    builder.move(x=10, y=20, z=30)
    assert builder.position.x == 10
    assert builder.position.y == 20
    assert builder.position.z == 30

def test_emergency_halt(builder, mock_write):
    builder.emergency_halt('Test emergency')
    assert mock_write.last_statement.startswith('M00')

@pytest.mark.parametrize("mode,code", [
    ("towards", "G38.2"),
    ("away", "G38.4"),
    ("towards-no-error", "G38.3"),
    ("away-no-error", "G38.5"),
])
def test_probe_modes(mode, code, builder, mock_write):
    builder.move(x=10, y=20, z=30)

    builder.probe(mode, x=10, F=100)
    assert builder.position == Point(None, 20, 30)
    assert mock_write.last_statement.startswith(code)
    assert builder.state.feed_rate == 100

    builder.probe(mode, [100, 200])
    assert builder.position == Point(None, None, 30)
    assert mock_write.last_statement.startswith(code)
