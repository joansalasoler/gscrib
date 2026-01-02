import pytest, os
from pytest import approx
from unittest.mock import Mock, patch
from gscrib.enums import DirectWrite
from gscrib.excepts import DeviceConnectionError
from gscrib.excepts import DeviceWriteError
from gscrib.excepts import DeviceError
from gscrib.excepts import GscribError
from gscrib.writers import PrintrunWriter

# --------------------------------------------------------------------
# Fixtures and helper classes
# --------------------------------------------------------------------

os.environ["UNIT_TESTING"] = "1"

@pytest.fixture
def mock_printcore():
    with patch('gscrib.writers.printrun_writer.printcore') as mock:
        device = Mock()
        device.online = True
        device.printing = False
        device.clear = True
        device.priqueue = Mock()
        device.priqueue.empty.return_value = True
        mock.return_value = device
        yield mock

@pytest.fixture
def serial_writer():
    writer = PrintrunWriter(
        mode=DirectWrite.SERIAL,
        host="none",
        port="/dev/ttyUSB0",
        baudrate=115200
    )

    writer._wait_for_acknowledgment = Mock()
    writer._wait_for_connection = Mock()

    return writer

@pytest.fixture
def scoket_writer():
    writer = PrintrunWriter(
        mode=DirectWrite.SOCKET,
        host="testhost",
        port="8888",
        baudrate=0
    )

    writer._wait_for_acknowledgment = Mock()
    writer._wait_for_connection = Mock()

    return writer


# --------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------

# Test initialization

def test_init_serial_writer(serial_writer):
    assert serial_writer._mode == DirectWrite.SERIAL
    assert serial_writer._port == "/dev/ttyUSB0"
    assert serial_writer._baudrate == 115200
    assert serial_writer._device is None
    assert serial_writer._shutdown_requested is False

def test_init_socket_writer(scoket_writer):
    assert scoket_writer._mode == DirectWrite.SOCKET
    assert scoket_writer._host == "testhost"
    assert scoket_writer._port == "8888"
    assert scoket_writer._device is None
    assert scoket_writer._shutdown_requested is False

# Test connection

def test_is_connected(serial_writer):
    assert not serial_writer.is_connected
    serial_writer._device = Mock(online=True)
    assert serial_writer.is_connected
    serial_writer._device.online = False
    assert not serial_writer.is_connected

def test_is_printing(serial_writer):
    assert not serial_writer.is_printing
    serial_writer._device = Mock(online=True, printing=True)
    assert serial_writer.is_printing
    serial_writer._device.printing = False
    assert not serial_writer.is_printing

def test_connect_success(serial_writer, mock_printcore):
    serial_writer.connect()
    assert serial_writer.is_connected
    assert serial_writer._device is not None
    mock_printcore.assert_called_once()

def test_connect_already_connected(serial_writer, mock_printcore):
    serial_writer.connect()
    assert serial_writer.is_connected
    original_device = serial_writer._device
    serial_writer.connect() # Should not create new device
    assert serial_writer.is_connected
    assert serial_writer._device == original_device

# Test auto-connection

def test_auto_connect_on_write(serial_writer, mock_printcore):
    test_command = b"G1 X10 Y10\n"
    serial_writer.write(test_command)
    assert serial_writer._device is not None
    serial_writer._device.send.assert_called_once_with("G1 X10 Y10")
    serial_writer.disconnect()

# Test disconnection

def test_disconnect(serial_writer, mock_printcore):
    serial_writer.connect()
    assert serial_writer.is_connected
    device = serial_writer._device
    serial_writer.disconnect(wait=False)
    assert not serial_writer.is_connected
    device.disconnect.assert_called_once()

# Test writing

def test_write_command(serial_writer, mock_printcore):
    test_command = b"G1 X10 Y10\n"
    serial_writer.write(test_command)
    serial_writer._device.send.assert_called_once_with("G1 X10 Y10")

def test_write_multiple_statements(serial_writer, mock_printcore):
    statements = [
        b"G1 X10 Y10\n",
        b"G1 X20 Y20\n",
        b"G1 X30 Y30\n"
    ]

    for statement in statements:
        serial_writer.write(statement)

    assert serial_writer._device.send.call_count == 3
    serial_writer._device.send.assert_any_call("G1 X10 Y10")
    serial_writer._device.send.assert_any_call("G1 X20 Y20")
    serial_writer._device.send.assert_any_call("G1 X30 Y30")

def test_context_manager(serial_writer, mock_printcore):
    with serial_writer as writer:
        assert writer.is_connected
        assert serial_writer._device is not None
        device = serial_writer._device

    assert not serial_writer.is_connected
    device.disconnect.assert_called_once()

# Test error handling

def test_write_error(serial_writer, mock_printcore):
    serial_writer.connect()
    serial_writer._device.send.side_effect = Exception("Write failed")

    with pytest.raises(DeviceWriteError):
        serial_writer.write(b"G1 X10 Y10\n")

    assert serial_writer._device_error is None

def test_write_connect_failure(serial_writer, mock_printcore):
    mock_printcore.side_effect = Exception("Connection failed")

    with pytest.raises(DeviceConnectionError):
        serial_writer.write(b"G1 X10 Y10\n")

    assert serial_writer._device_error is None

def test_connect_failure(serial_writer, mock_printcore):
    mock_printcore.side_effect = Exception("Connection failed")

    with pytest.raises(DeviceConnectionError):
        serial_writer.connect()

    assert not serial_writer.is_connected
    assert serial_writer._device_error is None

def test_connect_timeout(mock_printcore):
    serial_writer = PrintrunWriter(
        mode=DirectWrite.SERIAL,
        host="none",
        port="/dev/ttyUSB0",
        baudrate=115200
    )

    mock_device = Mock()
    mock_device.online = False
    mock_printcore.return_value = mock_device
    serial_writer.set_timeout(0.1)

    with pytest.raises(DeviceConnectionError):
        serial_writer.connect()

    assert serial_writer._device_error is None

# Test set_timeout

def test_set_timeout_valid(serial_writer):
    serial_writer.set_timeout(5.0)
    assert serial_writer._timeout == approx(5.0)

def test_set_timeout_invalid(serial_writer):
    with pytest.raises(ValueError):
        serial_writer.set_timeout(0)

    with pytest.raises(ValueError):
        serial_writer.set_timeout(-1)

# Test _send_statement

def test_send_statement(serial_writer, mock_printcore):
    serial_writer.connect()
    serial_writer._send_statement(b"G1 X10 Y20\n")
    serial_writer._device.send.assert_called_once_with("G1 X10 Y20")
    assert not serial_writer._ack_event.is_set()

# Test _abort_on_device_error

def test_abort_on_device_error_no_error(serial_writer, mock_printcore):
    serial_writer.connect()
    serial_writer._abort_on_device_error()  # Should not raise

def test_abort_on_device_error_with_error(serial_writer, mock_printcore):
    serial_writer.connect()
    serial_writer._device_error = DeviceError("Test error")

    with pytest.raises(DeviceError, match="Test error"):
        serial_writer._abort_on_device_error()

    assert serial_writer._device_error is None

# Test _parse_message

def test_parse_message_single_axis(serial_writer):
    serial_writer._parse_message("X:10.5")
    assert serial_writer._current_params["X"] == approx(10.5)

def test_parse_message_multiple_axes(serial_writer):
    serial_writer._parse_message("X:10.5 Y:20.3 Z:5.0")
    assert serial_writer._current_params["X"] == approx(10.5)
    assert serial_writer._current_params["Y"] == approx(20.3)
    assert serial_writer._current_params["Z"] == approx(5.0)

def test_parse_message_mpos(serial_writer):
    serial_writer._parse_message("MPos:10.0,20.0,30.0")
    assert serial_writer._current_params["X"] == approx(10.0)
    assert serial_writer._current_params["Y"] == approx(20.0)
    assert serial_writer._current_params["Z"] == approx(30.0)

def test_parse_message_wpos(serial_writer):
    serial_writer._parse_message("WPos:5.5,15.5,25.5")
    assert serial_writer._current_params["X"] == approx(5.5)
    assert serial_writer._current_params["Y"] == approx(15.5)
    assert serial_writer._current_params["Z"] == approx(25.5)

def test_parse_message_fs_grbl(serial_writer):
    serial_writer._parse_message("<Idle|MPos:0,0,0|FS:1500,8000>")
    assert serial_writer._current_params["F"] == approx(1500.0)
    assert serial_writer._current_params["S"] == approx(8000.0)

def test_parse_message_marlin_temp(serial_writer):
    serial_writer._parse_message("ok T:200.0 /210.0 B:60.0 /60.0")
    assert serial_writer._current_params["T"] == approx(200.0)
    assert serial_writer._current_params["B"] == approx(60.0)

def test_parse_message_multi_extruder(serial_writer):
    serial_writer._parse_message("T0:200.0 T1:190.0 T2:185.0")
    assert serial_writer._current_params["T0"] == approx(200.0)
    assert serial_writer._current_params["T1"] == approx(190.0)
    assert serial_writer._current_params["T2"] == approx(185.0)

def test_parse_message_clears_reported_params(serial_writer):
    serial_writer._parse_message("X:10.5")
    assert "X" in serial_writer._reported_params

    serial_writer._parse_message("Y:20.3")
    assert "X" not in serial_writer._reported_params
    assert "Y" in serial_writer._reported_params

# Test _on_device_message

def test_on_device_message_success(serial_writer):
    serial_writer._on_device_message("ok")
    assert serial_writer._ack_event.is_set()
    assert serial_writer._device_error is None

def test_on_device_message_error(serial_writer):
    serial_writer._on_device_message("error: Invalid command")
    assert serial_writer._ack_event.is_set()
    assert isinstance(serial_writer._device_error, DeviceError)
    assert "Invalid command" in str(serial_writer._device_error)

def test_on_device_message_alarm(serial_writer):
    serial_writer._on_device_message("ALARM: Hard limit")
    assert serial_writer._ack_event.is_set()
    assert isinstance(serial_writer._device_error, DeviceError)

def test_on_device_message_data(serial_writer):
    serial_writer._on_device_message("X:10.5 Y:20.3")
    assert serial_writer._current_params["X"] == approx(10.5)
    assert serial_writer._current_params["Y"] == approx(20.3)

def test_on_device_message_exception(serial_writer):
    with patch.object(serial_writer, '_parse_message', side_effect=Exception("Parse error")):
        serial_writer._on_device_message("invalid data")
        assert isinstance(serial_writer._device_error, GscribError)
        assert "Internal error" in str(serial_writer._device_error)
