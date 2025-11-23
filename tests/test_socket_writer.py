import pytest
from gscrib.writers import SocketWriter
from gscrib.writers import HostWriter


# --------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------

# Test initialization

def test_init_default_state():
    writer = SocketWriter("localhost", 8000)
    assert isinstance(writer._writer_delegate, HostWriter)
