import pytest
import threading
import time
from gscrib.host.scheduler import QuotaTracker
from gscrib.host.scheduler import ConsumeQuotaTimeout


# --------------------------------------------------------------------
# Fixtures and helper classes
# --------------------------------------------------------------------

@pytest.fixture
def tracker():
    return QuotaTracker(100)


# --------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------

def test_initialization():
    tracker = QuotaTracker()
    assert tracker._free_bytes == 127  # Grbl buffer size
    assert len(tracker._in_flight) == 0

def test_consume_quota(tracker):
    tracker.consume(50)
    assert tracker._free_bytes == 50
    assert len(tracker._in_flight) == 1
    assert tracker._in_flight[0] == 50

def test_reclaim(tracker):
    tracker.consume(30)
    tracker.consume(20)
    assert tracker._free_bytes == 50

    tracker.reclaim()  # Reclaims 30 (FIFO)
    assert tracker._free_bytes == 80

    tracker.reclaim()  # Reclaims 20
    assert tracker._free_bytes == 100

def test_reclaim_empty(tracker):
    tracker.reclaim()  # Should not error
    assert tracker._free_bytes == 100

def test_flush(tracker):
    tracker.consume(50)
    tracker.flush()
    assert tracker._free_bytes == 100
    assert len(tracker._in_flight) == 0

def test_consume_blocks(tracker):
    tracker.consume(100)

    def reclaimer():
        time.sleep(0.1)
        tracker.reclaim()

    thread = threading.Thread(target=reclaimer)
    thread.start()

    tracker.consume(10, timeout=1.0)
    assert tracker._free_bytes == 90
    assert len(tracker._in_flight) == 1
    assert tracker._in_flight[0] == 10
    thread.join()

def test_join(tracker):
    tracker.consume(50)

    def reclaimer():
        time.sleep(0.1)
        tracker.reclaim()

    thread = threading.Thread(target=reclaimer)
    thread.start()

    tracker.join()
    assert tracker._free_bytes == 100
    assert len(tracker._in_flight) == 0
    thread.join()

def test_initialization_invalid_size():
    with pytest.raises(ValueError):
        QuotaTracker(0)

    with pytest.raises(ValueError):
        QuotaTracker(-1)

def test_consume_invalid_size():
    tracker = QuotaTracker(100)

    with pytest.raises(ValueError):
        tracker.consume(0)

    with pytest.raises(ValueError):
        tracker.consume(101)

def test_consume_invalid_timeout():
    tracker = QuotaTracker(100)

    with pytest.raises(ValueError):
        tracker.consume(10, timeout=0)

    with pytest.raises(ValueError):
        tracker.consume(10, timeout=-1)

def test_consume_timeout(tracker):
    tracker.consume(100)
    start = time.monotonic()

    with pytest.raises(ConsumeQuotaTimeout):
        tracker.consume(1, timeout=0.1)

    duration = time.monotonic() - start
    assert duration >= 0.1
