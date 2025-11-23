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

"""Test suite for `printrun/base_device.py`"""

import unittest

from gscrib.host.base_device import BaseDevice
from gscrib.host.serial_device import SerialDevice
from gscrib.host.socket_device import SocketDevice


class TestBaseDeviceFactory(unittest.TestCase):
    """Test BaseDevice factory functionality"""

    def test_factory_creates_serial(self):
        """Check factory creates SerialDevice for serial ports"""
        dev = BaseDevice.create("/any/port")
        self.assertIsInstance(dev, SerialDevice)

    def test_factory_creates_socket(self):
        """Check factory creates SocketDevice for network addresses"""
        dev = BaseDevice.create("127.0.0.1:80")
        self.assertIsInstance(dev, SocketDevice)

    def test_invalid_network_address_creates_serial(self):
        """Check invalid network addresses create SerialDevice"""
        # No port number
        dev1 = BaseDevice.create("127.0.0.1")
        self.assertIsInstance(dev1, SerialDevice)

        # Invalid format
        dev2 = BaseDevice.create("invalid:format:test")
        self.assertIsInstance(dev2, SerialDevice)

        # Port out of range
        dev3 = BaseDevice.create("127.0.0.1:99999")
        self.assertIsInstance(dev3, SerialDevice)