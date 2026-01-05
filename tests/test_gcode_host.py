import pytest
from unittest.mock import MagicMock, Mock, patch

from gscrib.host.gcode_host import GCodeHost
from gscrib.host.connection import Connection
from gscrib.host.scheduler.task_priority import TaskPriority
from gscrib.host.gcode_host import StreamingMode

from gscrib.host.protocol.events import (
    DeviceOnlineEvent,
    DeviceReadyEvent,
    DeviceResendEvent,
    DeviceErrorEvent,
    DeviceFaultEvent,
    HostExceptionEvent,
)


# ============================================================================
# Fixtures and helper classes
# ============================================================================

@pytest.fixture
def mock_thread():
    with patch("threading.Thread") as thread_cls:
        yield thread_cls.return_value

@pytest.fixture
def mock_parser():
    with patch("gscrib.host.gcode_host.EventParser") as parser_cls:
        yield parser_cls.return_value

@pytest.fixture
def mock_dispatcher():
    with patch("gscrib.host.gcode_host.EventDispatcher") as dispatcher_cls:
        yield dispatcher_cls.return_value

@pytest.fixture
def mock_connection():
    mock = MagicMock(spec=Connection)
    mock.can_stream_commands.return_value = True
    return mock

@pytest.fixture
def gcode_host(mock_connection):
    return GCodeHost(mock_connection)


# --------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------

def test_initialization(mock_connection):
    host = GCodeHost(mock_connection)
    assert not host.is_online
    assert not host.sign_commands
    assert not host._was_started
    assert not host._online_signal.is_set()
    assert not host._shutdown_signal.is_set()
    assert host.streaming_mode == StreamingMode.AUTOMATIC
    assert host._connection is mock_connection

def test_start_initializes_threads(mock_thread, gcode_host):
    gcode_host.start()
    assert len(gcode_host._worker_threads) == 2
    assert gcode_host._clear_signal.is_set()

def test_stop_signals_shutdown(mock_thread, gcode_host):
    gcode_host.start()
    gcode_host.stop()
    assert gcode_host._shutdown_signal.is_set()
    assert gcode_host._clear_signal.is_set()
    assert not gcode_host.is_online

def test_stop_idempotent(mock_thread, gcode_host):
    gcode_host.start()
    gcode_host.stop()
    gcode_host.stop()  # Should not raise

def test_stop_purges_queue(mock_thread, gcode_host):
    gcode_host.start()
    gcode_host.enqueue("G1 X10")
    gcode_host.enqueue("G1 Y20")
    assert not gcode_host._send_queue.empty()
    gcode_host.stop()
    assert gcode_host._send_queue.empty()

def test_force_host_shutdown_purges_queue(gcode_host):
    gcode_host.enqueue("G1 X10")
    gcode_host.enqueue("G1 Y20")
    assert not gcode_host._send_queue.empty()
    gcode_host._force_host_shutdown()
    assert gcode_host._send_queue.empty()

def test_enqueue_valid_command(gcode_host):
    result = gcode_host.enqueue("G1 X10 Y20")
    assert not gcode_host._send_queue.empty()
    assert result is True

def test_enqueue_comment_ignored(gcode_host):
    result = gcode_host.enqueue("; just a comment")
    assert gcode_host._send_queue.empty()
    assert result is False

def test_enqueue_empty_string_ignored(gcode_host):
    result = gcode_host.enqueue("")
    assert gcode_host._send_queue.empty()
    assert result is False

def test_enqueue_priority_normal(gcode_host):
    gcode_host.enqueue("G1 X10")
    task = gcode_host._send_queue.get()
    assert task.priority == TaskPriority.NORMAL

def test_enqueue_line_reset(gcode_host):
    gcode_host._enqueue_line_reset()
    task = gcode_host._send_queue.get()
    assert "M110 N0" in task.command.instruction
    assert task.priority == TaskPriority.SYSTEM

def test_enqueue_synch(gcode_host):
    gcode_host._enqueue_synch()
    task = gcode_host._send_queue.get()
    assert "G4 P0" in task.command.instruction
    assert task.priority == TaskPriority.SYSTEM

def test_enqueue_resend_uses_system_priority(gcode_host):
    command = gcode_host._build_command("G1 X50")
    gcode_host._send_history.record(command)
    gcode_host._enqueue_resend(command.line_number)
    task = gcode_host._send_queue.get()
    assert task.priority == TaskPriority.SYSTEM

def test_build_command_increments_line_number(gcode_host):
    command1 = gcode_host._build_command("G1 X10")
    command2 = gcode_host._build_command("G1 Y20")
    assert command1.line_number == 1
    assert command2.line_number == 2

def test_build_command_with_signing_disabled(gcode_host):
    gcode_host.sign_commands = False
    command = gcode_host._build_command("G1 X10")
    assert command.signed is False

def test_build_command_with_signing_enabled(gcode_host):
    gcode_host.sign_commands = True
    command = gcode_host._build_command("G1 X10")
    assert command.signed is True

def test_purge_send_queue(gcode_host):
    gcode_host.enqueue("G1 X10")
    gcode_host.enqueue("G1 Y20")
    gcode_host.enqueue("G1 Z5")
    assert not gcode_host._send_queue.empty()
    gcode_host._purge_send_queue()
    assert gcode_host._send_queue.empty()

def test_is_busy_false_when_shutdown(gcode_host):
    gcode_host._shutdown_signal.set()
    assert gcode_host.is_busy is False

def test_is_busy_true_with_queued_commands(gcode_host):
    gcode_host.enqueue("G1 X10")
    assert gcode_host.is_busy is True

def test_is_busy_true_with_pending_quota(gcode_host):
    gcode_host._send_quota.consume(50)
    assert gcode_host.is_busy is True

def test_is_busy_false_when_idle(gcode_host):
    assert gcode_host.is_busy is False

def test_handle_online_event(mock_parser, mock_dispatcher, gcode_host):
    gcode_host._online_signal.clear()
    gcode_host._clear_signal.clear()
    gcode_host._shutdown_signal.clear()

    event = DeviceOnlineEvent(mock_parser, "start")
    mock_parser.parse.return_value = event
    gcode_host._handle_incoming_message(event.message)

    mock_dispatcher.dispatch.assert_called_once_with(event)
    assert not gcode_host._shutdown_signal.is_set()
    assert gcode_host._clear_signal.is_set()
    assert gcode_host.is_online

def test_handle_ready_event(mock_parser, mock_dispatcher, gcode_host):
    gcode_host._online_signal.clear()
    gcode_host._clear_signal.clear()
    gcode_host._shutdown_signal.clear()

    event = DeviceReadyEvent(mock_parser, "ok")
    mock_parser.parse.return_value = event
    gcode_host._handle_incoming_message(event.message)

    mock_dispatcher.dispatch.assert_called_once_with(event)
    assert not gcode_host._shutdown_signal.is_set()
    assert gcode_host._clear_signal.is_set()
    assert gcode_host.is_online

def test_handle_error_event(mock_parser, mock_dispatcher, gcode_host):
    gcode_host._online_signal.set()
    gcode_host._clear_signal.clear()
    gcode_host._shutdown_signal.clear()

    event = DeviceErrorEvent(mock_parser, "error: something")
    mock_parser.parse.return_value = event
    gcode_host._handle_incoming_message(event.message)

    mock_dispatcher.dispatch.assert_called_once_with(event)
    assert not gcode_host._shutdown_signal.is_set()
    assert gcode_host._clear_signal.is_set()
    assert gcode_host.is_online

def test_handle_fault_event(mock_parser, mock_dispatcher, gcode_host):
    gcode_host._online_signal.set()
    gcode_host._shutdown_signal.clear()

    event = DeviceFaultEvent(mock_parser, "ALARM: something")
    mock_parser.parse.return_value = event
    gcode_host._handle_incoming_message(event.message)

    mock_dispatcher.dispatch.assert_called_once_with(event)
    assert gcode_host._shutdown_signal.is_set()
    assert not gcode_host.is_online

def test_handle_resend_event(mock_parser, mock_dispatcher, gcode_host):
    gcode_host._online_signal.set()
    gcode_host._clear_signal.clear()
    gcode_host._shutdown_signal.clear()

    gcode_host.enqueue("G1 X10")
    event = DeviceResendEvent(mock_parser, "resend:1")
    mock_parser.parse.return_value = event
    mock_parser.extract_line_number = Mock(return_value=1)

    task = gcode_host._send_queue.get()
    gcode_host._send_history.record(task.command)
    gcode_host._handle_incoming_message(event.message)

    mock_dispatcher.dispatch.assert_called_once_with(event)
    assert not gcode_host._send_queue.empty()
    assert not gcode_host._shutdown_signal.is_set()
    assert gcode_host._clear_signal.is_set()
    assert gcode_host.is_online

@pytest.mark.parametrize("mode, can_stream, signal_cleared", [
    (StreamingMode.ASYNCHRONOUS, True,  False),
    (StreamingMode.ASYNCHRONOUS, False, False),
    (StreamingMode.SYNCHRONOUS,  True,  True),
    (StreamingMode.SYNCHRONOUS,  False, True),
    (StreamingMode.AUTOMATIC,    True,  False),
    (StreamingMode.AUTOMATIC,    False, True),
])
def test_prepare_for_acknowledgment(
    mock_connection, gcode_host, mode, can_stream, signal_cleared):
    gcode_host._clear_signal.set()
    gcode_host.streaming_mode = mode
    mock_connection.can_stream_commands.return_value = can_stream
    gcode_host._prepare_for_acknowledgment()
    assert gcode_host._clear_signal.is_set() is not signal_cleared

def test_enqueue_handshake_without_signing(gcode_host):
    gcode_host.sign_commands = False
    gcode_host._enqueue_handshake()

    # Should only contain the sync command (G4 P0)
    assert gcode_host._send_queue.qsize() == 1
    task = gcode_host._send_queue.get()
    assert "G4 P0" in task.command.instruction

def test_enqueue_handshake_with_signing(gcode_host):
    gcode_host.sign_commands = True
    gcode_host._enqueue_handshake()

    # Should contain M110 N0 (reset) AND G4 P0 (sync)
    assert gcode_host._send_queue.qsize() == 2
    first_task = gcode_host._send_queue.get()
    second_task = gcode_host._send_queue.get()
    assert "M110 N0" in first_task.command.instruction
    assert "G4 P0" in second_task.command.instruction

def test_enqueue_resend_success(gcode_host):
    command = gcode_host._build_command("G1 X50")
    gcode_host._send_history.record(command)
    gcode_host._enqueue_resend(command.line_number)

    task = gcode_host._send_queue.get()
    assert task.command.line_number == command.line_number
    assert task.priority == TaskPriority.SYSTEM

def test_handle_host_exception_triggers_shutdown(mock_dispatcher, gcode_host):
    gcode_host._shutdown_signal.clear()

    error = RuntimeError("Serial port lost")
    gcode_host._handle_host_exception(error)

    assert gcode_host._shutdown_signal.is_set()
    mock_dispatcher.dispatch.assert_called_once()
    event = mock_dispatcher.dispatch.call_args[0][0]
    assert isinstance(event, HostExceptionEvent)
    assert event.error == error

def test_stop_waits_for_threads(mock_thread, gcode_host):
    gcode_host.start()
    gcode_host._worker_threads = [MagicMock(), MagicMock()]
    gcode_host.stop(timeout=1.0)

    for thread in gcode_host._worker_threads:
        thread.join.assert_called_with(timeout=1.0)

def test_subscribe(mock_dispatcher, gcode_host):
    handler = lambda _: None
    gcode_host.subscribe(DeviceOnlineEvent, handler)
    mock_dispatcher.subscribe.assert_called_once_with(DeviceOnlineEvent, handler)

def test_unsubscribe(mock_dispatcher, gcode_host):
    handler = lambda _: None
    gcode_host.unsubscribe(DeviceOnlineEvent, handler)
    mock_dispatcher.unsubscribe.assert_called_once_with(DeviceOnlineEvent, handler)

@pytest.mark.parametrize("property_name", [
    "write_timeout", "online_timeout", "poll_timeout"
])
def test_timeout_setters(gcode_host, property_name):
    setattr(gcode_host, property_name, 5.0)
    assert getattr(gcode_host, property_name) == 5.0

@pytest.mark.parametrize("mode", [
    StreamingMode.AUTOMATIC,
    StreamingMode.ASYNCHRONOUS,
    StreamingMode.SYNCHRONOUS
])
def test_streaming_mode_setters(gcode_host, mode):
    setattr(gcode_host, "streaming_mode", mode)
    assert gcode_host.streaming_mode == mode

def test_stop_not_started_error(mock_connection):
    host = GCodeHost(mock_connection)

    with pytest.raises(RuntimeError):
        host.stop()

def test_start_already_start_error(mock_thread, gcode_host):
    gcode_host.start()

    with pytest.raises(RuntimeError):
        gcode_host.start()

def test_enqueue_multiline_error(gcode_host):
    with pytest.raises(RuntimeError):
        gcode_host.enqueue("G1 X10\nG1 Y10")

def test_enqueue_during_shutdown_error(gcode_host):
    gcode_host._shutdown_signal.set()

    with pytest.raises(RuntimeError):
        gcode_host.enqueue("G1 X10")

def test_enqueue_after_stop_error(mock_thread, gcode_host):
    gcode_host.start()
    gcode_host.stop()

    with pytest.raises(RuntimeError):
        gcode_host.enqueue("G1 X10")

def test_wait_for_acknowledgment_shutdown_error(gcode_host):
    gcode_host._clear_signal.clear()
    gcode_host._shutdown_signal.set()

    with pytest.raises(TimeoutError):
        gcode_host._wait_for_acknowledgment(0.01)

def test_enqueue_resend_not_found_error(gcode_host):
    with pytest.raises(KeyError):
        gcode_host._enqueue_resend(999)

@pytest.mark.parametrize("property_name", [
    "write_timeout", "online_timeout", "poll_timeout"
])
def test_timeout_setters_invalid(gcode_host, property_name):
    with pytest.raises(ValueError):
        setattr(gcode_host, property_name, 0)

    with pytest.raises(ValueError):
        setattr(gcode_host, property_name, -1.0)
