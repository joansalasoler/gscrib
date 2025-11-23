import pytest
from unittest.mock import Mock, patch
from gscrib.enums import DirectWrite
from gscrib.excepts import DeviceConnectionError
from gscrib.excepts import DeviceTimeoutError
from gscrib.excepts import DeviceWriteError
from gscrib.writers import HostWriter

# --------------------------------------------------------------------
# Fixtures and helper classes
# --------------------------------------------------------------------

@pytest.fixture
def mock_gcode_host():
    with patch('gscrib.writers.host_writer.GCodeHost') as mock:
        device = Mock()
        device.is_connected = Mock(return_value=True)
        device.is_busy = Mock(return_value=False)
        device.is_ready = Mock(return_value=True)
        device.has_queued_commands = Mock(return_value=False)
        mock.return_value = device
        yield mock

@pytest.fixture
def serial_writer():
    writer = HostWriter(
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
    writer = HostWriter(
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
    serial_writer._device.is_connected = Mock(return_value=False)
    assert not serial_writer.is_connected

def test_is_busy(serial_writer):
    assert not serial_writer.is_busy
    serial_writer._device = Mock(online=True, printing=True)
    assert serial_writer.is_busy
    serial_writer._device.is_busy = Mock(return_value=False)
    assert not serial_writer.is_busy

def test_connect_success(serial_writer, mock_gcode_host):
    serial_writer.connect()
    assert serial_writer.is_connected
    assert serial_writer._device is not None
    mock_gcode_host.assert_called_once()

def test_connect_already_connected(serial_writer, mock_gcode_host):
    serial_writer.connect()
    assert serial_writer.is_connected
    original_device = serial_writer._device
    serial_writer.connect() # Should not create new device
    assert serial_writer.is_connected
    assert serial_writer._device == original_device

# Test auto-connection

def test_auto_connect_on_write(serial_writer, mock_gcode_host):
    test_command = b"G1 X10 Y10\n"
    serial_writer.write(test_command)
    assert serial_writer._device is not None
    serial_writer._device.enqueue.assert_called_once_with("G1 X10 Y10")
    serial_writer.disconnect()

# Test disconnection

def test_disconnect(serial_writer, mock_gcode_host):
    serial_writer.connect()
    assert serial_writer.is_connected
    device = serial_writer._device
    serial_writer.disconnect(wait=False)
    assert not serial_writer.is_connected
    device.disconnect.assert_called_once()

# Test writing

def test_write_command(serial_writer, mock_gcode_host):
    test_command = b"G1 X10 Y10\n"
    serial_writer.write(test_command)
    serial_writer._device.enqueue.assert_called_once_with("G1 X10 Y10")

def test_write_multiple_statements(serial_writer, mock_gcode_host):
    statements = [
        b"G1 X10 Y10\n",
        b"G1 X20 Y20\n",
        b"G1 X30 Y30\n"
    ]

    for statement in statements:
        serial_writer.write(statement)

    assert serial_writer._device.enqueue.call_count == 3
    serial_writer._device.enqueue.assert_any_call("G1 X10 Y10")
    serial_writer._device.enqueue.assert_any_call("G1 X20 Y20")
    serial_writer._device.enqueue.assert_any_call("G1 X30 Y30")

def test_context_manager(serial_writer, mock_gcode_host):
    with serial_writer as writer:
        assert writer.is_connected
        assert serial_writer._device is not None
        device = serial_writer._device

    assert not serial_writer.is_connected
    device.disconnect.assert_called_once()

# Test error handling

def test_write_error(serial_writer, mock_gcode_host):
    serial_writer.connect()
    serial_writer._device.enqueue.side_effect = Exception("Write failed")

    with pytest.raises(DeviceWriteError):
        serial_writer.write(b"G1 X10 Y10\n")

    assert serial_writer._device_error is None

def test_write_connect_failure(serial_writer, mock_gcode_host):
    mock_gcode_host.side_effect = Exception("Connection failed")

    with pytest.raises(DeviceConnectionError):
        serial_writer.write(b"G1 X10 Y10\n")

    assert serial_writer._device_error is None

def test_connect_failure(serial_writer, mock_gcode_host):
    mock_gcode_host.side_effect = Exception("Connection failed")

    with pytest.raises(DeviceConnectionError):
        serial_writer.connect()

    assert not serial_writer.is_connected
    assert serial_writer._device_error is None

def test_connect_timeout(mock_gcode_host):
    serial_writer = HostWriter(
        mode=DirectWrite.SERIAL,
        host="none",
        port="/dev/ttyUSB0",
        baudrate=115200
    )

    mock_device = Mock()
    mock_device.is_connected = Mock(return_value=False)
    mock_gcode_host.return_value = mock_device
    serial_writer.set_timeout(0.1)

    with pytest.raises(DeviceConnectionError):
        serial_writer.connect()

    assert serial_writer._device_error is None
