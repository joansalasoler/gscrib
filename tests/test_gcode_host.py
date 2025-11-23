# This file is part of the Printrun suite.
#
# Printrun is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Printrun is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Printrun.  If not, see <http://www.gnu.org/licenses/>.

"""Test suite for `printrun/gcode_host.py`."""

import pytest
import random
import selectors
import socket
import time
import logging
from unittest import mock

import serial
from gscrib.host import GCodeHost


DEFAULT_ANSWER = 'ok:\n'
CNC_PROCESS_TIME = 0.02  # in s


def slow_printer(*args):
    """Simulate a slow processing printer"""
    time.sleep(CNC_PROCESS_TIME*random.randint(0, 90)/100)
    return DEFAULT_ANSWER.encode()


def wait_printer_cycles(cycles):
    """Wait for a slow printer to process"""
    time.sleep(CNC_PROCESS_TIME*cycles)


@pytest.fixture(autouse=True)
def mock_sttyhup():
    """Fake stty control"""
    with mock.patch("gscrib.host.serial_device.SerialDevice._configure_serial_port"):
        yield


def mock_serial(read_function=slow_printer):
    """Fake Serial device with slow response and always open"""
    class_mock = mock.create_autospec(serial.Serial)
    instance_mock = class_mock.return_value
    instance_mock.readline.side_effect = read_function
    instance_mock.is_open = True
    return mock.patch("serial.Serial", class_mock)


def mock_socket(read_function=slow_printer):
    """Fake socket with slow response"""
    class_mock = mock.create_autospec(socket.socket)
    instance_mock = class_mock.return_value
    socket_file = instance_mock.makefile.return_value
    socket_file.readline.side_effect = read_function

    socket_patcher = mock.patch("socket.socket", class_mock)

    return socket_patcher


def setup_test_command():
    """Set up a command to test"""
    command = "Random Command"
    parsed_command = f"{command}\n".encode('ascii')
    return {'raw': command, 'parsed': parsed_command}


def test_connection_events():
    """Test events on a successful connection"""
    core = GCodeHost()

    with mock_serial() as mocked_serial:
        with mock.patch.object(core, "_connect_callback") as online_cb:
            core.connect("/mocked/port", 1000)
            wait_printer_cycles(2)

            assert core.is_connected()
            assert core._read_thread is not None
            assert core._read_thread.is_alive
            assert core._send_thread is not None
            assert core._send_thread.is_alive
            online_cb.assert_called_once()

        core.disconnect()


def test_calls_socket_connect():
    """Test that socket.socket.connect() is called"""
    core = GCodeHost()

    socket_patcher = mock_socket()
    with socket_patcher as mocked_socket:
        url = ("192.168.1.200", 1234)
        core.connect(f"{url[0]}:{url[1]}", 1000)
        wait_printer_cycles(2)

        mocked_socket.return_value.connect.assert_called_once_with(url)
        mocked_socket.return_value.makefile.assert_called_once()

    core.disconnect()


def test_calls_serial_open():
    """Test that serial.Serial constructor is called"""
    core = GCodeHost()

    with mock_serial() as mocked_serial:
        core.connect("/mocked/port", 1000)
        wait_printer_cycles(2)
        mocked_serial.assert_called_once()

    core.disconnect()


def test_send_command_queue():
    """Test that a command is put into command queue"""
    core = GCodeHost()
    command = setup_test_command()['raw']

    with mock_serial():
        core.connect("/mocked/port", 1000)
        wait_printer_cycles(2)

        with mock.patch.object(core, "_command_queue") as mocked_queue:
            core.enqueue(command)
        mocked_queue.put_nowait.assert_called_once_with(command)

    core.disconnect()


def test_send_not_connected(caplog):
    """Test that an error is logged when attempting to send a
    command but printer is not online"""
    core = GCodeHost()
    with caplog.at_level(logging.ERROR):
        core.enqueue("Random Command")
    assert "Cannot send command: not connected" in caplog.text


def test_priority_command():
    """Test that commands are sent to the printer from priqueue"""
    core = GCodeHost()
    test_command = setup_test_command()
    command = test_command['raw']
    parsed_command = test_command['parsed']

    with mock_serial() as mocked_serial:
        core.connect("/mocked/port", 1000)
        wait_printer_cycles(2)

        core.enqueue(command)
        wait_printer_cycles(2)
        mocked_serial.return_value.write.assert_called_with(parsed_command)

    core.disconnect()


def test_calls_socket_write():
    """Test that socket.sendall() is called"""
    core = GCodeHost()
    test_command = setup_test_command()
    command = test_command['raw']
    parsed_command = test_command['parsed']

    socket_patcher = mock_socket()
    with socket_patcher as mocked_socket:
        core.connect("1.2.3.4:56", 1000)
        wait_printer_cycles(2)

        core.enqueue(command)
        wait_printer_cycles(2)
        mocked_socket.return_value.sendall.assert_called_with(parsed_command)

    core.disconnect()


def test_startprint_success():
    """Test successful print start"""
    core = GCodeHost()

    with mock_serial():
        core.connect("/mocked/port", 1000)
        wait_printer_cycles(2)

        result = core.start_processing()
        assert result is True
        assert core.is_busy() is True

    core.disconnect()


def test_startprint_offline():
    """Test startprint returns False if not connected"""
    core = GCodeHost()
    result = core.start_processing()
    assert result is False


def test_cancelprint():
    """Test cancel print"""
    core = GCodeHost()

    with mock_serial():
        core.connect("/mocked/port", 1000)
        wait_printer_cycles(2)

        core.start_processing()
        assert core.is_busy() is True
        core.stop_processing()
        assert core.is_busy() is False

    core.disconnect()