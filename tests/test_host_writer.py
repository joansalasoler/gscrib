import pytest
from unittest.mock import Mock, MagicMock, patch
from gscrib.writers import HostWriter

from gscrib.excepts import (
    DeviceError,
    DeviceConnectionError,
    DeviceWriteError
)

from gscrib.host.protocol import (
    DeviceErrorEvent,
    DeviceFaultEvent,
    DeviceFeedbackEvent,
)

# --------------------------------------------------------------------
# Fixtures and helper classes
# --------------------------------------------------------------------

@pytest.fixture
def mock_connection():
    with patch("gscrib.writers.host_writer.Connection") as connection_cls:
        yield connection_cls

@pytest.fixture
def mock_gcode_host():
    with patch("gscrib.writers.host_writer.GCodeHost") as host_cls:
        yield host_cls

@pytest.fixture
def host_writer(mock_connection, mock_gcode_host):
    return HostWriter("socket://testhost:8888")


# --------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------

def test_initialization(mock_connection):
    host_writer = HostWriter("COM3", baudrate=115200)
    assert host_writer._host is None
    assert host_writer._current_params is not None
    assert host_writer.sign_commands is False
    assert not host_writer._connect_signal.is_set()
    assert not host_writer._fault_signal.is_set()
    mock_connection.assert_called_once_with("COM3", 115200)

def test_get_parameter(host_writer):
    x_value = 10.5
    host_writer._current_params["X"] = x_value
    assert host_writer.get_parameter("X") == x_value

def test_get_parameter_missing(host_writer):
    assert host_writer.get_parameter("X") is None

def test_connect_success(host_writer):
    result = host_writer.connect()
    assert result is host_writer
    assert host_writer._host is not None
    assert host_writer._connect_signal.is_set()
    assert not host_writer._fault_signal.is_set()
    host_writer._connection.open.assert_called_once()
    host_writer._host.start.assert_called_once()

def test_disconnect_success(host_writer):
    host_writer.connect()
    gcode_host = host_writer._host
    host_writer.disconnect()
    assert host_writer._host is None
    assert not host_writer._connect_signal.is_set()
    gcode_host.join_queue.assert_called_once()
    gcode_host.stop.assert_called_once()

def test_disconnect_success_no_wait(host_writer):
    host_writer.connect()
    gcode_host = host_writer._host
    host_writer.disconnect(wait=False)
    gcode_host.join_queue.assert_not_called()

def test_disconnect_not_connected(host_writer):
    host_writer.disconnect()

def test_disconnect_with_fault(host_writer, mock_gcode_host):
    host_writer._host = mock_gcode_host
    host_writer._connect_signal.set()
    host_writer._fault_signal.set()
    host_writer.disconnect(wait=True)
    mock_gcode_host.join_queue.assert_not_called()

def test_connect_idempotent(host_writer):
    host_writer.connect()
    host_writer.connect()
    host_writer._connection.open.assert_called_once()
    host_writer._host.start.assert_called_once()
    assert host_writer._connect_signal.is_set()
    assert not host_writer._fault_signal.is_set()

def test_disconnect_idempotent(host_writer):
    host_writer.connect()
    assert host_writer._connect_signal.is_set()
    host_writer.disconnect()
    host_writer.disconnect()
    assert not host_writer._connect_signal.is_set()

def test_write_command(mock_gcode_host, host_writer):
    host_writer._host = mock_gcode_host
    host_writer._connect_signal.set()
    host_writer.write(b"G1 X10 Y10\n")
    host_writer._host.enqueue.assert_called_once_with("G1 X10 Y10\n")

def test_write_auto_connects(host_writer):
    assert not host_writer._connect_signal.is_set()
    host_writer.write(b"G1 X10")
    assert host_writer._host is not None
    assert host_writer._connect_signal.is_set()
    host_writer._host.enqueue.assert_called_once_with("G1 X10")

def test_sync_success(host_writer, mock_gcode_host):
    host_writer._connect_signal.set()
    host_writer._host = mock_gcode_host
    host_writer.sync()
    host_writer._host.join_queue.assert_called_once()

def test_on_device_error(host_writer):
    event = Mock(spec=DeviceErrorEvent)
    event.message = "Error: recoverable"
    host_writer._on_device_error(event)

def test_on_device_fault(host_writer):
    host_writer.connect()
    assert host_writer._connect_signal.is_set()

    gcode_host = host_writer._host
    event = MagicMock(spec=DeviceFaultEvent)
    event.message = "ALARM: hard limit"
    host_writer._on_device_fault(event)

    gcode_host.stop.assert_called_once()
    host_writer._connection.close.assert_called_once()
    assert not host_writer._connect_signal.is_set()
    assert host_writer._fault_signal.is_set()
    assert host_writer._host is None

def test_on_device_feedback_updates_params(host_writer):
    x_value, y_value = 10.0, 20.0
    event = MagicMock(spec=DeviceFeedbackEvent)
    event.message = "feedback message"
    event.fields = {"X": 10.0, "Y": 20.0}
    host_writer._on_device_feedback(event)
    assert host_writer.get_parameter("X") == x_value
    assert host_writer.get_parameter("Y") == y_value

def test_subscribe_to_events(host_writer, mock_gcode_host):
    host_writer._subscribe_to_events(mock_gcode_host)
    assert mock_gcode_host.subscribe.call_count == 3

def test_unsubscribe_from_events(host_writer, mock_gcode_host):
    host_writer._unsubscribe_from_events(mock_gcode_host)
    assert mock_gcode_host.unsubscribe.call_count == 3

def test_sign_commands_getter(host_writer):
    assert host_writer.sign_commands is False
    host_writer._sign_commands = True
    assert host_writer.sign_commands is True

def test_sign_commands_setter(host_writer):
    host_writer.sign_commands = True
    assert host_writer._sign_commands is True
    host_writer.sign_commands = False
    assert host_writer._sign_commands is False

def test_sign_commands_propagates_to_host(host_writer):
    host_writer.sign_commands = True
    host_writer.connect()
    assert host_writer._host.sign_commands is True

def test_context_manager(host_writer):
    with host_writer as writer:
        assert writer is host_writer
        assert host_writer._connect_signal.is_set()

    assert host_writer._host is None
    host_writer._connection.open.assert_called_once()
    host_writer._connection.close.assert_called_once()

def test_init_invalid_url(mock_connection):
    with pytest.raises(ValueError):
        HostWriter("", 9600)

def test_init_invalid_baudrate(mock_connection):
    with pytest.raises(ValueError):
        HostWriter("COM3", -1)

def test_write_error(mock_gcode_host, host_writer):
    host_writer._connect_signal.set()
    host_writer._host = mock_gcode_host
    mock_gcode_host.enqueue.side_effect = Exception()

    with pytest.raises(DeviceWriteError):
        host_writer.write(b"G1 X10\n")

def test_write_during_fault_error(host_writer):
    host_writer._fault_signal.set()

    with pytest.raises(DeviceError):
        host_writer.write(b"G1 X10")

def test_sync_during_fault_error(host_writer):
    host_writer._fault_signal.set()

    with pytest.raises(DeviceError):
        host_writer.sync()

def test_sync_not_connected_error(host_writer):
    with pytest.raises(DeviceError):
        host_writer.sync()

def test_connect_failure(host_writer):
    host_writer._connection.open.side_effect = Exception()

    with pytest.raises(DeviceConnectionError):
        host_writer.connect()

def test_write_invalid_utf8(host_writer):
    host_writer._connect_signal.set()
    host_writer._host = MagicMock()

    with pytest.raises(DeviceWriteError):
        host_writer.write(b"\xff\xfe")

def test_on_device_error_prevents_write(host_writer):
    host_writer.connect()
    event = MagicMock(spec=DeviceErrorEvent)
    event.message = "Error: something"
    host_writer._on_device_error(event)

    with pytest.raises(DeviceError):
        host_writer.write(b"G1 X10")

def test_on_device_fault_prevents_write(host_writer):
    host_writer.connect()
    event = MagicMock(spec=DeviceFaultEvent)
    event.message = "ALARM: hard limit"
    host_writer._on_device_fault(event)

    with pytest.raises(DeviceError):
        host_writer.write(b"G1 X10")

def test_on_device_error_disconnects(host_writer):
    host_writer.connect()
    assert host_writer._connect_signal.is_set()
    assert not host_writer._fault_signal.is_set()

    gcode_host = host_writer._host
    gcode_host.stop = MagicMock()

    event = MagicMock(spec=DeviceErrorEvent)
    event.message = "Error: something"
    host_writer._on_device_error(event)

    gcode_host.stop.assert_called_once()
    host_writer._connection.close.assert_called_once()
    assert not host_writer._connect_signal.is_set()
    assert host_writer._fault_signal.is_set()
    assert host_writer._host is None

def test_on_device_fault_disconnects(host_writer):
    host_writer.connect()
    assert host_writer._connect_signal.is_set()
    assert not host_writer._fault_signal.is_set()

    gcode_host = host_writer._host
    gcode_host.stop = MagicMock()

    event = MagicMock(spec=DeviceFaultEvent)
    event.message = "ALARM: hard limit"
    host_writer._on_device_fault(event)

    gcode_host.stop.assert_called_once()
    host_writer._connection.close.assert_called_once()
    assert not host_writer._connect_signal.is_set()
    assert host_writer._fault_signal.is_set()
    assert host_writer._host is None
