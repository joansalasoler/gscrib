import pytest
from unittest.mock import Mock
from gscrib.host.scheduler import CommandTracker
from gscrib.host.scheduler import Command


# --------------------------------------------------------------------
# Fixtures and helper classes
# --------------------------------------------------------------------

@pytest.fixture
def tracker():
    return CommandTracker(limit=3)

@pytest.fixture
def large_tracker():
    return CommandTracker(limit=1000)

def make_command(line_number):
    command = Mock(spec=Command)
    command.line_number = line_number
    return command


# --------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------

def test_initialization_with_default_limit():
    tracker = CommandTracker()
    assert len(tracker._entries) == 0
    assert tracker._limit == 127

def test_initialization_with_custom_limit():
    tracker = CommandTracker(limit=50)
    assert len(tracker._entries) == 0
    assert tracker._limit == 50

def test_record_and_fetch_single_command(tracker):
    command = make_command(1)
    tracker.record(command)
    assert tracker.fetch(1) == command

def test_fifo_eviction(tracker):
    commands = [make_command(i) for i in range(1, 10)]

    for command in commands:
        tracker.record(command)

    assert len(tracker._entries) == 3
    assert tracker.fetch(7).line_number == 7
    assert tracker.fetch(8).line_number == 8
    assert tracker.fetch(9).line_number == 9

def test_replace_mantains_insertion_order(tracker):
    commands = [make_command(i) for i in range(1, 4)]

    for command in commands:
        tracker.record(command)

    assert len(tracker._entries) == 3
    entries_old = list(tracker._entries.values())

    command1_new = make_command(1)
    tracker.record(command1_new)

    entries_old[0] = command1_new
    entries_new = list(tracker._entries.values())
    assert entries_new == entries_old

def test_fetch_nonexistent_command(tracker):
    with pytest.raises(KeyError):
        tracker.fetch(99)

def test_fetch_evicted_command(tracker):
    command = make_command(1)
    tracker.record(command)
    assert tracker.fetch(1) == command

    # Evict it by recording new commands
    tracker.record(make_command(2))
    tracker.record(make_command(3))
    tracker.record(make_command(4))

    with pytest.raises(KeyError):
        tracker.fetch(1)
