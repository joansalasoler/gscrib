import pytest
from unittest.mock import patch
from gscrib import GCodeBuilder
from gscrib import Point
from gscrib.enums import *


# --------------------------------------------------------------------
# Fixtures and helper classes
# --------------------------------------------------------------------

@pytest.fixture
def gbuilder(mock_write):
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

def test_select_units(gbuilder, mock_write):
    gbuilder.select_units(LengthUnits.MILLIMETERS)
    assert gbuilder.state.current_length_units == LengthUnits.MILLIMETERS
    assert mock_write.last_statement.startswith('G21')

def test_select_plane(gbuilder, mock_write):
    gbuilder.select_plane(Plane.XY)
    assert gbuilder.state.current_plane == Plane.XY
    assert mock_write.last_statement.startswith('G17')

def test_set_axis_position(gbuilder, mock_write):
    gbuilder.set_axis_position(x=10, y=20, z=30)
    assert gbuilder.position == Point(10, 20, 30)
    assert mock_write.last_statement.startswith('G92 X10 Y20 Z30')

def test_set_axis_position_partial(gbuilder, mock_write):
    gbuilder.set_axis_position(x=10)
    assert gbuilder.position == Point(10, None, None)
    assert mock_write.last_statement.startswith('G92 X10')

def test_set_distance_mode_absolute(gbuilder, mock_write):
    gbuilder.set_distance_mode(DistanceMode.ABSOLUTE)
    assert gbuilder.state.current_distance_mode == DistanceMode.ABSOLUTE
    assert gbuilder.is_relative == False
    assert mock_write.last_statement.startswith('G90')

def test_set_distance_mode_relative(gbuilder, mock_write):
    gbuilder.set_distance_mode(DistanceMode.RELATIVE)
    assert gbuilder.state.current_distance_mode == DistanceMode.RELATIVE
    assert gbuilder.is_relative == True
    assert mock_write.last_statement.startswith('G91')

def test_set_tool_power(gbuilder, mock_write):
    gbuilder.set_tool_power(1000.0)
    assert gbuilder.state.current_tool_power == 1000.0
    assert mock_write.last_statement.startswith('S1000')

def test_set_tool_power_invalid(gbuilder):
    with pytest.raises(ValueError):
        gbuilder.set_tool_power(-100)

def test_set_fan_speed(gbuilder, mock_write):
    gbuilder.set_fan_speed(255)
    assert mock_write.last_statement.startswith('M106 P0 S255')
    gbuilder.set_fan_speed(0)
    assert mock_write.last_statement.startswith('M106 P0 S0')

def test_set_fan_speed_invalid(gbuilder):
    with pytest.raises(ValueError):
        gbuilder.set_fan_speed(256)

    with pytest.raises(ValueError):
        gbuilder.set_fan_speed(-1)

def test_tool_on(gbuilder, mock_write):
    gbuilder.tool_on(SpinMode.CLOCKWISE, 1000.0)
    assert gbuilder.state.current_spin_mode == SpinMode.CLOCKWISE
    assert gbuilder.state.current_tool_power == 1000.0
    assert mock_write.last_statement.startswith('S1000 M03')

def test_tool_on_invalid_mode(gbuilder):
    with pytest.raises(ValueError):
        gbuilder.tool_on(SpinMode.OFF, 1000.0)

def test_tool_off(gbuilder, mock_write):
    gbuilder.tool_on(SpinMode.CLOCKWISE, 1000.0)
    gbuilder.tool_off()
    assert gbuilder.state.current_spin_mode == SpinMode.OFF
    assert mock_write.last_statement.startswith('M05')

def test_power_on(gbuilder, mock_write):
    gbuilder.power_on(PowerMode.CONSTANT, 75.0)
    assert gbuilder.state.current_power_mode == PowerMode.CONSTANT
    assert gbuilder.state.current_tool_power == 75.0
    assert mock_write.last_statement.startswith('S75')

def test_power_off(gbuilder):
    gbuilder.power_on(PowerMode.CONSTANT, 75.0)
    gbuilder.power_off()
    assert gbuilder.state.current_power_mode == PowerMode.OFF

def test_tool_change(gbuilder, mock_write):
    tool_number = 1
    gbuilder.tool_change(ToolSwapMode.MANUAL, tool_number)
    assert gbuilder.state.current_tool_swap_mode == ToolSwapMode.MANUAL
    assert gbuilder.state.current_tool_number == tool_number
    assert mock_write.last_statement.startswith('T1')

def test_coolant_operations(gbuilder):
    gbuilder.coolant_on(CoolantMode.FLOOD)
    assert gbuilder.state.current_coolant_mode == CoolantMode.FLOOD

    gbuilder.coolant_off()
    assert gbuilder.state.current_coolant_mode == CoolantMode.OFF

def test_sleep(gbuilder, mock_write):
    gbuilder.sleep(TimeUnits.SECONDS, 1.5)
    assert mock_write.last_statement.startswith('G04 P1.5')

def test_sleep_invalid_duration(gbuilder):
    with pytest.raises(ValueError):
        gbuilder.sleep(TimeUnits.SECONDS, 0.0005)  # Less than 1ms

def test_set_bed_temperature(gbuilder, mock_write):
    gbuilder.set_bed_temperature(TemperatureUnits.CELSIUS, 60)
    assert mock_write.last_statement.startswith('M140 S60')

def test_current_axis_position(gbuilder):
    gbuilder.move(x=10, y=20, z=30)
    assert gbuilder.position.x == 10
    assert gbuilder.position.y == 20
    assert gbuilder.position.z == 30

def test_emergency_halt(gbuilder, mock_write):
    gbuilder.emergency_halt('Test emergency')
    assert mock_write.last_statement.startswith('M00')
