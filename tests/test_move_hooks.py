import math
import pytest
from gscrib import GCodeBuilder, GState, ParamsDict
from gscrib.geometry import Point
from gscrib.enums import SpinMode


# --------------------------------------------------------------------
# Fixtures and helper classes
# --------------------------------------------------------------------


@pytest.fixture
def builder():
    return GCodeBuilder()


def noop_hook(origin, target, params, state):
    return params


# --------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------


def test_add_hook(builder):
    builder.add_hook(noop_hook)
    assert noop_hook in builder._hooks
    assert len(builder._hooks) == 1
    builder.add_hook(noop_hook)  # Should not duplicate hook
    assert len(builder._hooks) == 1


def test_remove_hook(builder):
    def hook(origin, target, params, state):
        return params

    builder.remove_hook(noop_hook)  # Should not raise exception
    assert len(builder._hooks) == 0
    builder.add_hook(noop_hook)
    assert len(builder._hooks) == 1
    builder.remove_hook(noop_hook)
    assert len(builder._hooks) == 0


def test_hook_context(builder):
    assert len(builder._hooks) == 0

    with builder.move_hook(noop_hook):
        assert noop_hook in builder._hooks
        assert len(builder._hooks) == 1

    assert len(builder._hooks) == 0


def test_hook_context_with_exception(builder):
    assert len(builder._hooks) == 0

    with pytest.raises(ValueError):
        with builder.move_hook(noop_hook):
            assert noop_hook in builder._hooks
            raise ValueError("Test exception")

    # Handler should be removed even if exception occurs
    assert len(builder._hooks) == 0


def test_prepare_move_with_hook(builder):
    processed_params = None

    def test_hook(origin, target, params, state):
        nonlocal processed_params
        processed_params = params.copy()
        params.update(F=1000)  # Modify feed rate
        return params

    builder.add_hook(test_hook)
    point = Point(10, 20, 0)
    params = ParamsDict(F=2000)
    builder._prepare_move(point, params)
    assert processed_params is not None
    assert processed_params.get("F") == 2000


def test_multiple_hooks(builder):
    results = []

    def hook1(origin, target, params, state):
        results.append(1)
        params.update(F=1000)
        return params

    def hook2(origin, target, params, state):
        results.append(2)
        params.update(F=500)
        return params

    builder.add_hook(hook1)
    builder.add_hook(hook2)

    point = Point(10, 20, 0)
    params = ParamsDict(F=2000)
    builder._prepare_move(point, params)

    assert results == [1, 2]  # Verify invokation order
    assert params.get("F") == 500  # Last hook's value


def test_practical_extrusion_hook(builder):
    def extrude_hook(origin, target, params, state):
        dt = target - origin
        length = math.hypot(dt.x, dt.y)
        params.update(E=0.1 * length)
        return params

    builder.add_hook(extrude_hook)

    # Move 10mm in X direction
    point = Point(10, 0, 0)
    params = ParamsDict()
    builder._prepare_move(point, params)
    assert params.get("E") == pytest.approx(1.0)  # 10mm * 0.1

    # Diagonal move (10mm, 10mm)
    point = Point(10, 10, 0)
    params = ParamsDict()
    builder._prepare_move(point, params)
    assert params.get("E") == pytest.approx(1.414, rel=1e-3)  # sqrt(200) * 0.1


def test_hook_state_access(builder):
    def state_checker(origin, target, params, state):
        assert isinstance(state, GState)
        params.update(F=1000 if state.is_tool_active else 2000)
        return params

    builder.add_hook(state_checker)

    # Move with tool off
    params = ParamsDict()
    point = Point(10, 0, 0)
    builder._prepare_move(point, params)
    assert params.get("F") == 2000

    # Move with tool on
    params = ParamsDict()
    builder._state._set_spin_mode(SpinMode.CLOCKWISE, 100)
    builder._prepare_move(point, params)
    assert params.get("F") == 1000


def test_hook_receives_absolute_coordinates(builder):
    received_coords = []

    def coord_checker(origin, target, params, state):
        received_coords.append({"origin": Point(*origin), "target": Point(*target)})
        return params

    builder.add_hook(coord_checker)
    builder.move(x=10, y=10)  # (10, 10)
    builder.set_distance_mode("relative")
    builder.move(x=5, y=5)  # (15, 15)
    builder.move(x=-5, y=5)  # (10, 20)

    assert len(received_coords) == 3

    assert received_coords[0]["origin"] == Point(0, 0, 0)
    assert received_coords[0]["target"] == Point(10, 10, 0)

    assert received_coords[1]["origin"] == Point(10, 10, 0)
    assert received_coords[1]["target"] == Point(15, 15, 0)

    assert received_coords[2]["origin"] == Point(15, 15, 0)
    assert received_coords[2]["target"] == Point(10, 20, 0)
