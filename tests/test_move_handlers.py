import math
import pytest
from gscrib import GCodeBuilder, GState
from gscrib import Point, MoveParams
from gscrib.enums import SpinMode


# --------------------------------------------------------------------
# Fixtures and helper classes
# --------------------------------------------------------------------

@pytest.fixture
def builder():
    return GCodeBuilder()

def noop_handler(origin, target, params, state):
    return params

# --------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------

def test_add_handler(builder):
    builder.add_handler(noop_handler)
    assert noop_handler in builder._handlers
    assert len(builder._handlers) == 1
    builder.add_handler(noop_handler) # Should not duplicate handler
    assert len(builder._handlers) == 1

def test_remove_handler(builder):
    def handler(origin, target, params, state):
        return params

    builder.remove_handler(noop_handler) # Should not raise exception
    assert len(builder._handlers) == 0
    builder.add_handler(noop_handler)
    assert len(builder._handlers) == 1
    builder.remove_handler(noop_handler)
    assert len(builder._handlers) == 0

def test_handler_context(builder):
    assert len(builder._handlers) == 0

    with builder.handler(noop_handler):
        assert noop_handler in builder._handlers
        assert len(builder._handlers) == 1

    assert len(builder._handlers) == 0

def test_handler_context_with_exception(builder):
    assert len(builder._handlers) == 0

    with pytest.raises(ValueError):
        with builder.handler(noop_handler):
            assert noop_handler in builder._handlers
            raise ValueError("Test exception")

    # Handler should be removed even if exception occurs
    assert len(builder._handlers) == 0

def test_write_move_with_handler(builder):
    processed_params = None

    def test_handler(origin, target, params, state):
        nonlocal processed_params
        processed_params = params.copy()
        params.update(F=1000)  # Modify feed rate
        return params

    builder.add_handler(test_handler)
    point = Point(10, 20, 0)
    params = MoveParams(F=2000)
    builder._write_move(point, params)
    assert processed_params is not None
    assert processed_params.get('F') == 2000

def test_multiple_handlers(builder):
    results = []

    def handler1(origin, target, params, state):
        results.append(1)
        params.update(F=1000)
        return params

    def handler2(origin, target, params, state):
        results.append(2)
        params.update(F=500)
        return params

    builder.add_handler(handler1)
    builder.add_handler(handler2)

    point = Point(10, 20, 0)
    params = MoveParams(F=2000)
    builder._write_move(point, params)

    assert results == [1, 2] # Verify invokation order
    assert params.get('F') == 500  # Last handler's value

def test_practical_extrusion_handler(builder):
    def extrude_handler(origin, target, params, state):
        dt = target - origin
        length = math.hypot(dt.x, dt.y)
        params.update(E=0.1 * length)
        return params

    builder.add_handler(extrude_handler)

    # Move 10mm in X direction
    point = Point(10, 0, 0)
    params = MoveParams()
    builder._write_move(point, params)
    assert params.get('E') == pytest.approx(1.0)  # 10mm * 0.1

    # Diagonal move (10mm, 10mm)
    point = Point(10, 10, 0)
    params = MoveParams()
    builder._write_move(point, params)
    assert params.get('E') == pytest.approx(1.414, rel=1e-3)  # sqrt(200) * 0.1

def test_handler_state_access(builder):
    def state_checker(origin, target, params, state):
        assert isinstance(state, GState)
        params.update(F=1000 if state.is_tool_active else 2000)
        return params

    builder.add_handler(state_checker)

    # Move with tool off
    params = MoveParams()
    point = Point(10, 0, 0)
    builder._write_move(point, params)
    assert params.get('F') == 2000

    # Move with tool on
    params = MoveParams()
    builder._state._set_spin_mode(SpinMode.CLOCKWISE, 100)
    builder._write_move(point, params)
    assert params.get('F') == 1000

def test_handler_receives_absolute_coordinates(builder):
    received_coords = []

    def coord_checker(origin, target, params, state):
        received_coords.append({
            'origin': Point(*origin),
            'target': Point(*target)
        })
        return params

    builder.add_handler(coord_checker)
    builder.move(x=10, y=10) # (10, 10)
    builder.set_distance_mode("relative")
    builder.move(x=5, y=5) # (15, 15)
    builder.move(x=-5, y=5) # (10, 20)

    assert len(received_coords) == 3

    assert received_coords[0]['origin'] == Point(0, 0, 0)
    assert received_coords[0]['target'] == Point(10, 10, 0)

    assert received_coords[1]['origin'] == Point(10, 10, 0)
    assert received_coords[1]['target'] == Point(15, 15, 0)

    assert received_coords[2]['origin'] == Point(15, 15, 0)
    assert received_coords[2]['target'] == Point(10, 20, 0)
