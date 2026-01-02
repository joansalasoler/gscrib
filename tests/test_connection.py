import pytest
import serial, time
from unittest.mock import MagicMock, patch
from serial import SerialException

from gscrib.host.connection import Connection
from gscrib.host.exceptions import HostConnectError
from gscrib.host.exceptions import HostReadError, HostWriteError


# --------------------------------------------------------------------
# Fixtures and helper classes
# --------------------------------------------------------------------

@pytest.fixture
def mock_serial():
    with patch("serial.serial_for_url") as mock:
        yield mock

@pytest.fixture(autouse=True)
def no_sleep():
    with patch("time.sleep", return_value=None):
        yield

@pytest.fixture
def connection(mock_serial):
    connection = Connection("COM3", 115200)
    backend = MagicMock()
    backend.is_open = True
    mock_serial.return_value = backend
    return connection


# --------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------

def test_socket_initialization():
    connection = Connection("socket://localhost:8080")
    assert not connection.is_open
    assert connection.is_network_transport
    assert connection.can_stream_commands

def test_serial_initialization():
    connection = Connection("/dev/ttyUSB0")
    assert not connection.is_open
    assert not connection.is_network_transport
    assert not connection.can_stream_commands

def test_rfc2217_initialization():
    connection = Connection("rfc2217://localhost:2217")
    assert not connection.is_open
    assert connection.is_network_transport
    assert connection.can_stream_commands

def test_open_success(mock_serial):
    connection = Connection("/dev/ttyUSB0").open()
    assert connection.is_open
    mock_serial.assert_called_once()
    connection._backend.open.assert_called_once()

def test_read_line_complete(connection):
    connection.open()
    connection._backend.in_waiting = 5
    connection._backend.read.return_value = b"ok\n"
    line = connection.read_line()
    assert line == "ok"

def test_read_line_timeout(connection):
    connection.open()
    connection._backend.in_waiting = 0
    connection._backend.read.return_value = b""
    line = connection.read_line(timeout=0.1)
    assert connection._backend.timeout == 0.1
    assert line == ""

def test_read_line_buffering(connection):
    connection.open()
    connection._backend.in_waiting = 3

    # First read: partial data
    connection._backend.read.side_effect = [b"Hel", b"lo\n"]

    # First call returns empty string (timeout)
    line1 = connection.read_line()
    assert line1 == ""
    assert connection._rx_buffer == b"Hel"

    # Second call completes the line
    line2 = connection.read_line()
    assert line2 == "Hello"
    assert connection._rx_buffer == b""

def test_write_line_success(connection):
    connection.open()
    connection._backend.write.return_value = 3  # len("G1\n")
    connection.write_line("G1")
    connection._backend.write.assert_called_with(b"G1\n")
    connection._backend.flush.assert_called_once()

def test_read_invalid_character(connection):
    connection.open()
    connection._backend.in_waiting = 1
    connection._backend.read.return_value = b"\xff\n"
    line = connection.read_line()
    assert line == "\ufffd"

def test_close(connection):
    connection.open()
    backend = connection._backend
    connection.close()
    backend.close.assert_called_once()
    assert not connection.is_open

def test_close_idempotent(connection):
    connection.open()
    connection.close()
    connection.close()
    assert not connection.is_open

def test_flow_control_properties(connection):
    assert not connection.has_flow_control
    connection.rtscts = True
    assert connection.has_flow_control
    connection.rtscts = False
    connection.dsrdtr = True
    assert connection.has_flow_control

def test_open_configuration(mock_serial):
    conn = Connection("COM3")
    conn.rtscts = True
    conn.open()

    backend = conn._backend
    assert backend.rtscts is True
    assert backend.parity == serial.PARITY_NONE
    backend.reset_input_buffer.assert_called_once()
    backend.reset_output_buffer.assert_called_once()

def test_settings_propagation(connection):
    connection.open()
    backend = connection._backend

    connection.rtscts = True
    assert backend.rtscts is True

    connection.dsrdtr = True
    assert backend.dsrdtr is True

def test_write_line_encoding_error(connection):
    connection.open()

    with pytest.raises(UnicodeEncodeError):
        connection.write_line("G1 \u20ac")

def test_write_line_partial_error(connection):
    connection.open()

    # Simulate writing fewer bytes than expected
    connection._backend.write.return_value = 1

    with pytest.raises(HostWriteError):
        connection.write_line("G1")

def test_validate_connection_closed_error(connection):
    with pytest.raises(HostConnectError):
        connection.write_line("G1")

def test_open_already_open_error(connection):
    connection.open()

    with pytest.raises(RuntimeError):
        connection.open()

def test_open_error(mock_serial):
    mock_serial.side_effect = SerialException("Device not found")
    conn = Connection("COM3")

    with pytest.raises(HostConnectError):
        conn.open()

def test_read_error(connection):
    connection.open()
    connection._backend.in_waiting = 1
    connection._backend.read.side_effect = SerialException("Read failed")

    with pytest.raises(HostReadError):
        connection.read_line()

def test_write_error(connection):
    connection.open()
    connection._backend.write.side_effect = SerialException("Write failed")

    with pytest.raises(HostWriteError):
        connection.write_line("G1")
