import pytest
from gscrib.writers import SerialWriter
from gscrib.writers import HostWriter


# --------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------

# Test initialization

def test_init_default_state():
    writer = SerialWriter("/dev/ttyUSB0", 115200)
    assert isinstance(writer._writer_delegate, HostWriter)
