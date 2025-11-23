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

"""Test suite for `printrun/serial_device.py`"""

import unittest
from unittest import mock

import serial
from gscrib.host.serial_device import SerialDevice
from gscrib.host.base_device import READ_EMPTY
from gscrib.excepts import DeviceError


def mock_sttyhup(cls):
    """Fake stty control"""
    patcher = mock.patch("gscrib.host.serial_device.SerialDevice._configure_serial_port")
    patcher.start()
    cls.addClassCleanup(patcher.stop)


def patch_serial_is_open():
    """Patch the serial.Serial class and make `is_open` always True"""
    class_mock = mock.create_autospec(serial.Serial)
    instance_mock = class_mock.return_value
    instance_mock.is_open = True
    return mock.patch("serial.Serial", class_mock)


def setup_serial(test):
    """Set up a SerialDevice through a mocked serial connection"""
    dev = SerialDevice()

    # Ensure cleanup even if test fails
    def cleanup():
        try:
            dev.disconnect()
        except Exception:
            pass
    test.addCleanup(cleanup)

    # Mock the Serial class and its instance
    serial_instance = mock.MagicMock()
    serial_instance.is_open = True
    serial_instance.readline.return_value = b''

    patcher = mock.patch("serial.Serial", return_value=serial_instance)
    mocked_serial_class = patcher.start()
    test.addCleanup(patcher.stop)

    dev.connect("/mocked/port")

    return dev, serial_instance


class TestSerialConnect(unittest.TestCase):
    """Test serial connection functionality"""

    @classmethod
    def setUpClass(cls):
        mock_sttyhup(cls)

    def test_error_on_no_device(self):
        """DeviceError is raised when connecting to no port"""
        dev = SerialDevice()
        self.addCleanup(dev.disconnect)
        with self.assertRaisesRegex(DeviceError, "No port specified"):
            dev.connect()
        self.assertFalse(dev.is_connected)

    def test_call_serial_open(self):
        """serial.Serial constructor is called and `is_connected` is set"""
        dev = SerialDevice()
        self.addCleanup(dev.disconnect)
        with patch_serial_is_open() as mocked_serial:
            dev.connect("/mocked/port")
            mocked_serial.assert_called_once()
            self.assertTrue(dev.is_connected)


class TestSerialRead(unittest.TestCase):
    """Test readline functionality on serial connections"""

    @classmethod
    def setUpClass(cls):
        mock_sttyhup(cls)

    def setUp(self):
        self.dev, _ = setup_serial(self)

    def _fake_read(self, **kargs):
        # Patch the actual device instance's readline method
        with mock.patch.object(self.dev._device, 'readline', **kargs) as mocked_read:
            data = self.dev.readline()
            mocked_read.assert_called_once()
            return data

    def test_calls_readline(self):
        """serial.Serial.readline is called"""
        self._fake_read()

    def test_read_data(self):
        """Data returned by serial.Serial.readline is passed as is"""
        data = self._fake_read(return_value=b"data\n")
        self.assertEqual(data, b"data\n")

    def test_read_empty(self):
        """READ_EMPTY is returned when there's nothing to read"""
        self.assertEqual(self._fake_read(return_value=b''), READ_EMPTY)

    def test_read_no_device(self):
        """DeviceError is raised when device is not connected"""
        empty_dev = SerialDevice()
        with self.assertRaisesRegex(DeviceError, "Cannot read: device not connected"):
            empty_dev.readline()


class TestSerialWrite(unittest.TestCase):
    """Test write functionality on serial connections"""

    @classmethod
    def setUpClass(cls):
        mock_sttyhup(cls)

    def _setup_serial_write(self, side_effect=None):
        serial_instance = mock.MagicMock()
        serial_instance.is_open = True
        if side_effect is not None:
            serial_instance.write.side_effect = side_effect

        patcher = mock.patch("serial.Serial", return_value=serial_instance)
        mocked_serial_class = patcher.start()
        self.addCleanup(patcher.stop)

        dev = SerialDevice()
        self.addCleanup(dev.disconnect)
        dev.connect("/mocked/port")

        return dev, serial_instance

    def test_write_no_device(self):
        """DeviceError is raised when device is not connected"""
        empty_dev = SerialDevice()
        with self.assertRaisesRegex(DeviceError, "Cannot write: device not connected"):
            empty_dev.write(b"test")

    def test_calls_serial_write(self):
        """serial.Serial.write is called"""
        dev, serial_instance = self._setup_serial_write()
        dev.write(b"test")
        serial_instance.write.assert_called_once_with(b"test")