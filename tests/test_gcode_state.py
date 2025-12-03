import pytest
from pytest import approx
from gscrib.excepts import ToolStateError, CoolantStateError
from gscrib import GState
from gscrib.enums import *
from gscrib.enums import *


# --------------------------------------------------------------------
# Fixtures and helper classes
# --------------------------------------------------------------------

@pytest.fixture
def state():
    return GState()


# --------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------

def test_initial_state(state):
    assert state.tool_power == 0
    assert state.tool_number == 0
    assert state.tool_swap_mode == ToolSwapMode.OFF
    assert state.spin_mode == SpinMode.OFF
    assert state.power_mode == PowerMode.OFF
    assert state.distance_mode == DistanceMode.ABSOLUTE
    assert state.extrusion_mode == ExtrusionMode.ABSOLUTE
    assert state.coolant_mode == CoolantMode.OFF
    assert state.feed_mode == FeedMode.UNITS_PER_MINUTE
    assert state.halt_mode == HaltMode.OFF
    assert state.length_units == LengthUnits.MILLIMETERS
    assert state.time_units == TimeUnits.SECONDS
    assert state.temperature_units == TemperatureUnits.CELSIUS
    assert state.plane == Plane.XY
    assert state.direction == Direction.CLOCKWISE
    assert state.resolution == approx(0.1)
    assert not state.is_tool_active
    assert not state.is_coolant_active

def test_set_length_units(state):
    state._set_length_units(LengthUnits.INCHES)
    assert state.length_units == LengthUnits.INCHES

def test_set_time_units(state):
    state._set_time_units(TimeUnits.MILLISECONDS)
    assert state.time_units == TimeUnits.MILLISECONDS

def test_set_plane(state):
    state._set_plane(Plane.XY)
    assert state.plane == Plane.XY

def test_set_direction(state):
    state._set_direction(Direction.COUNTER)
    assert state.direction == Direction.COUNTER

def test_set_tool_power(state):
    state._set_tool_power(50.0)
    assert state.tool_power == approx(50.0)

def test_set_tool_power_invalid():
    state = GState()

    with pytest.raises(ValueError):
        state._set_tool_power(-1.0)

def test_set_distance_mode(state):
    state._set_distance_mode(DistanceMode.RELATIVE)
    assert state.distance_mode == DistanceMode.RELATIVE

def test_set_coolant_mode(state):
    state._set_coolant_mode(CoolantMode.MIST)
    state._set_coolant_mode(CoolantMode.OFF)
    state._set_coolant_mode(CoolantMode.FLOOD)
    assert state.coolant_mode == CoolantMode.FLOOD
    assert state.is_coolant_active

def test_set_coolant_mode_off(state):
    state._set_coolant_mode(CoolantMode.OFF)
    assert state.coolant_mode == CoolantMode.OFF
    assert not state.is_coolant_active

def test_coolant_mode_already_active(state):
    state._set_coolant_mode(CoolantMode.FLOOD)

    with pytest.raises(CoolantStateError):
        state._set_coolant_mode(CoolantMode.MIST)

def test_set_spin_mode(state):
    state._set_spin_mode(SpinMode.COUNTER, 2000)
    state._set_spin_mode(SpinMode.OFF)
    state._set_spin_mode(SpinMode.CLOCKWISE, 1000)
    assert state.spin_mode == SpinMode.CLOCKWISE
    assert state.tool_power == 1000
    assert state.is_tool_active

def test_set_spin_mode_off(state):
    state._set_spin_mode(SpinMode.OFF)
    assert state.spin_mode == SpinMode.OFF
    assert not state.is_tool_active

def test_spin_mode_already_active(state):
    state._set_spin_mode(SpinMode.CLOCKWISE)

    with pytest.raises(ToolStateError):
        state._set_spin_mode(SpinMode.CLOCKWISE)

def test_spin_mode_off_already_active(state):
    state._set_spin_mode(SpinMode.CLOCKWISE)
    state._set_spin_mode(SpinMode.OFF)
    assert state.spin_mode == SpinMode.OFF
    assert state.tool_power == 0

def test_set_power_mode(state):
    state._set_power_mode(PowerMode.DYNAMIC, 100.0)
    state._set_power_mode(PowerMode.OFF)
    state._set_power_mode(PowerMode.CONSTANT, 75.0)
    assert state.power_mode == PowerMode.CONSTANT
    assert state.tool_power == approx(75.0)
    assert state.is_tool_active

def test_set_power_mode_off(state):
    state._set_power_mode(PowerMode.OFF)
    assert state.power_mode == PowerMode.OFF
    assert not state.is_tool_active

def test_power_mode_already_active(state):
    state._set_power_mode(PowerMode.CONSTANT, 75.0)

    with pytest.raises(ToolStateError):
        state._set_power_mode(PowerMode.DYNAMIC, 50.0)

def test_power_mode_off_already_active(state):
    state._set_power_mode(PowerMode.DYNAMIC, 50.0)
    state._set_power_mode(PowerMode.OFF)
    assert state.power_mode == PowerMode.OFF
    assert state.tool_power == 0

def test_set_tool_number(state):
    state._set_tool_number(ToolSwapMode.MANUAL, 101)
    assert state.tool_swap_mode == ToolSwapMode.MANUAL
    assert state.tool_number == 101

def test_set_tool_invalid_tool():
    state = GState()

    with pytest.raises(ValueError):
        state._set_tool_number(ToolSwapMode.MANUAL, 0)

    with pytest.raises(ValueError):
        state._set_tool_number(ToolSwapMode.MANUAL, -1)

def test_set_tool_with_active_tool(state):
    state._set_power_mode(PowerMode.CONSTANT, 75.0)

    with pytest.raises(ToolStateError):
        state._set_tool_number(ToolSwapMode.MANUAL, 1)

def test_set_tool_with_active_coolant(state):
    state._set_coolant_mode(CoolantMode.FLOOD)

    with pytest.raises(CoolantStateError):
        state._set_tool_number(ToolSwapMode.MANUAL, 1)

def test_set_halt_mode(state):
    state._set_halt_mode(HaltMode.PAUSE)
    assert state.halt_mode == HaltMode.PAUSE

def test_set_halt_mode_off(state):
    state._set_coolant_mode(CoolantMode.FLOOD)
    state._set_halt_mode(HaltMode.OFF)
    assert state.halt_mode == HaltMode.OFF

def test_set_halt_mode_with_active_tool(state):
    state._set_power_mode(PowerMode.CONSTANT, 75.0)

    with pytest.raises(ToolStateError):
        state._set_halt_mode(HaltMode.OPTIONAL_PAUSE)

def test_set_halt_mode_with_active_coolant(state):
    state._set_coolant_mode(CoolantMode.FLOOD)

    with pytest.raises(CoolantStateError):
        state._set_halt_mode(HaltMode.END_WITH_RESET)
