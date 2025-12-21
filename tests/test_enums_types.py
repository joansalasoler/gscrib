import pytest
import math
from pytest import approx
from gscrib.enums import LengthUnits, TimeUnits, Direction, SpinMode


# --------------------------------------------------------------------
# Fixtures and helper classes
# --------------------------------------------------------------------

valid_angles = (
    +math.pi, +math.pi / 2, +2 * math.pi - 1e-12,
    -math.pi, -math.pi / 2, -2 * math.pi + 1e-12,
)

invalid_angles = (
    -4 * math.pi, -2 * math.pi, -2 * math.pi - 1e-12,
    +4 * math.pi, +2 * math.pi, +2 * math.pi + 1e-12,
)


# --------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------

def test_length_units_synonyms():
    assert LengthUnits("millimeters") == LengthUnits.MILLIMETERS
    assert LengthUnits("inches") == LengthUnits.INCHES
    assert LengthUnits("mm") == LengthUnits.MILLIMETERS
    assert LengthUnits("in") == LengthUnits.INCHES

def test_time_units_synonyms():
    assert TimeUnits("milliseconds") == TimeUnits.MILLISECONDS
    assert TimeUnits("seconds") == TimeUnits.SECONDS
    assert TimeUnits("ms") == TimeUnits.MILLISECONDS
    assert TimeUnits("s") == TimeUnits.SECONDS

def test_direction_synonyms():
    assert Direction("clockwise") == Direction.CLOCKWISE
    assert Direction("counter") == Direction.COUNTER
    assert Direction("cw") == Direction.CLOCKWISE
    assert Direction("ccw") == Direction.COUNTER

def test_spin_mode_synonyms():
    assert SpinMode("clockwise") == SpinMode.CLOCKWISE
    assert SpinMode("counter") == SpinMode.COUNTER
    assert SpinMode("ccw") == SpinMode.COUNTER
    assert SpinMode("cw") == SpinMode.CLOCKWISE
    assert SpinMode("off") == SpinMode.OFF

# Scaling

def test_length_units_scale_millimeters():
    units = LengthUnits.MILLIMETERS
    px_value = units.scale(1.0)
    assert px_value == approx(25.4 / 96.0)

def test_length_units_scale_inches():
    units = LengthUnits.INCHES
    px_value = units.scale(1.0)
    assert px_value == approx(1.0 / 96.0)

def test_length_units_to_pixels_millimeters():
    units = LengthUnits.MILLIMETERS
    units_value = units.to_pixels(1.0)
    assert units_value == approx(96.0 / 25.4)

def test_length_units_to_pixels_inches():
    units = LengthUnits.INCHES
    units_value = units.to_pixels(1.0)
    assert units_value == approx(96.0)

def test_time_units_scale_seconds():
    units = TimeUnits.SECONDS
    assert units.scale(10.0) == approx(10.0)
    assert units.scale(1.0) == approx(1.0)
    assert units.scale(0.5) == approx(0.5)

def test_time_units_scale_milliseconds():
    units = TimeUnits.MILLISECONDS
    assert units.scale(10.0) == approx(10000.0)
    assert units.scale(1.0) == approx(1000.0)
    assert units.scale(0.5) == approx(500.0)

# Angles

def test_direction_full_turn_clockwise():
    result = Direction.CLOCKWISE.full_turn()
    assert result == approx(-2 * math.pi)

def test_direction_full_turn_counter():
    result = Direction.COUNTER.full_turn()
    assert result == approx(2 * math.pi)

def test_direction_cw_enforce_zero():
    direction = Direction.CLOCKWISE
    assert direction.enforce(0.0) == approx(-2 * math.pi)

def test_direction_ccw_enforce_zero():
    direction = Direction.COUNTER
    assert direction.enforce(0.0) == approx(2 * math.pi)

@pytest.mark.parametrize("angle", valid_angles)
def test_direction_enforce_clockwise(angle):
    direction = Direction.CLOCKWISE
    result = direction.enforce(angle)
    assert result < 0
    assert math.isclose((result - angle) % (2 * math.pi), 0.0)
    assert direction.enforce(result) == result

@pytest.mark.parametrize("angle", valid_angles)
def test_direction_enforce_counter(angle):
    direction = Direction.COUNTER
    result = direction.enforce(angle)
    assert result > 0
    assert math.isclose((result - angle) % (2 * math.pi), 0.0)
    assert direction.enforce(result) == result

@pytest.mark.parametrize("angle", invalid_angles)
def test_direction_cw_enforce_angle_invalid(angle):
    with pytest.raises(ValueError):
        direction = Direction.CLOCKWISE
        direction.enforce(angle)

@pytest.mark.parametrize("angle", invalid_angles)
def test_direction_ccw_enforce_angle_invalid(angle):
    with pytest.raises(ValueError):
        direction = Direction.COUNTER
        direction.enforce(angle)

# Exceptions

def test_length_units_invalid():
    with pytest.raises(ValueError):
        LengthUnits("invalid")

def test_time_units_invalid():
    with pytest.raises(ValueError):
        TimeUnits("invalid")

def test_direction_invalid():
    with pytest.raises(ValueError):
        Direction("invalid")

def test_spin_mode_invalid():
    with pytest.raises(ValueError):
        SpinMode("invalid")
