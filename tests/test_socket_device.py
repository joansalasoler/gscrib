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

"""Test suite for `printrun/socket_device.py`"""

import unittest
from unittest import mock

from gscrib.host.socket_device import SocketDevice
from gscrib.host.base_device import READ_EOF
from gscrib.excepts import DeviceError


def patch_socket(function, **kwargs):
    """Patch a function of socket.socket"""
    return mock.patch(f"socket.socket.{function}", **kwargs)


def setup_socket(test):
    """Set up a SocketDevice through a mocked socket connection"""
    dev = SocketDevice()

    # Ensure cleanup even if test fails
    def cleanup():
        try:
            dev.disconnect()
        except Exception:
            pass
    test.addCleanup(cleanup)

    # Mock socket and its methods
    socket_mock = mock.MagicMock()
    socketfile_mock = mock.MagicMock()
    socket_mock.makefile.return_value = socketfile_mock

    patcher = mock.patch("socket.socket", return_value=socket_mock)
    mocked_socket_class = patcher.start()
    test.addCleanup(patcher.stop)

    dev.connect("127.0.0.1:80")

    return dev, socketfile_mock


class TestSocketConnect(unittest.TestCase):
    """Test socket connection functionality"""

    def test_error_on_no_device(self):
        """DeviceError is raised when connecting to no address"""
        dev = SocketDevice()
        self.addCleanup(dev.disconnect)
        with self.assertRaisesRegex(DeviceError, "No address specified"):
            dev.connect()
        self.assertFalse(dev.is_connected)

    def test_call_socket_connect(self):
        """socket.socket.connect is called and `is_connected` is set"""
        dev = SocketDevice()
        self.addCleanup(dev.disconnect)
        with patch_socket("connect") as mocked_connect:
            dev.connect("127.0.0.1:80")
            mocked_connect.assert_called_once()
            self.assertTrue(dev.is_connected)


class TestSocketRead(unittest.TestCase):
    """Test readline functionality on socket connections"""

    def setUp(self):
        self.dev, _ = setup_socket(self)

    def test_read_empty(self):
        """READ_EOF is returned when there's nothing to read"""
        # Mock readline to return empty bytes (EOF)
        with mock.patch.object(self.dev._socketfile, 'readline', return_value=b''):
            data = self.dev.readline()
            self.assertEqual(data, READ_EOF)
            self.assertFalse(self.dev.is_connected)

    def test_read_eof(self):
        """READ_EOF is returned when connection is terminated"""
        with mock.patch.object(self.dev._socketfile, 'readline', return_value=b''):
            data = self.dev.readline()
            self.assertEqual(data, READ_EOF)
            self.assertFalse(self.dev.is_connected)


class TestSocketWrite(unittest.TestCase):
    """Test write functionality on socket connections"""

    def setUp(self):
        self.dev, _ = setup_socket(self)

    def _fake_write(self, data, **kwargs):
        with mock.patch.object(self.dev._device, 'sendall', **kwargs) as mocked_write:
            self.dev.write(data)
            mocked_write.assert_called_once_with(data)

    def test_calls_socket_write(self):
        """socket.sendall is called"""
        self._fake_write(b"test")

    def test_write_no_device(self):
        """DeviceError is raised when device is not connected"""
        empty_dev = SocketDevice()
        with self.assertRaisesRegex(DeviceError, "Cannot write: device not connected"):
            empty_dev.write(b"test")