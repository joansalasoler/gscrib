from gscrib.writers import SocketWriter
from gscrib.writers import PrintrunWriter


# --------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------

# Test initialization


def test_init_default_state():
    writer = SocketWriter("localhost", 8000)
    assert isinstance(writer._writer_delegate, PrintrunWriter)
