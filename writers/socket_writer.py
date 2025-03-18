# -*- coding: utf-8 -*-

# G-Code generator for Vpype.
# Copyright (C) 2025 Joan Sala <contact@joansala.com>
#
# This file contains code originally written by Jack Minardi, which is
# licensed under the MIT License. See the LICENSE-MIT file in this
# project's root directory for the full text of the original license.
#
# Modifications made by Joan Sala are licensed under the GNU GPL.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import socket

from .base_writer import BaseWriter


class SocketWriter(BaseWriter):
    """Writer that sends commands through a TCP/IP socket connection.

    This class implements a G-code writer that connects to a remote machine
    or device via a TCP socket connection and sends G-code commands. It
    can optionally wait for responses from the device.

    Example:
        >>> writer = SocketWriter("localhost", 8000)
        >>> writer.write(b"G1 X10 Y10\\n")
        >>> writer.disconnect()
    """

    def __init__(self, host: str, port: int, wait_for_response: bool = True):
        """Initialize the socket writer.

        Args:
            host (str): The hostname or IP address of the remote machine.
            port (int): The TCP port number to connect to.
            wait_for_response (bool, optional): Whether to wait for
                responses from the device after each command.
        """

        self._socket = None
        self._wait_for_response = wait_for_response
        self._host = host
        self._port = port

    def connect(self) -> None:
        """Establish a TCP socket connection to the remote machine.

        Raises:
            socket.error: If the connection cannot be established.
        """

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((self._host, self._port))

    def disconnect(self, wait: bool = True) -> None:
        """Close the socket connection if it is open."""

        if self._socket is not None:
            self._socket.close()
            self._socket = None

    def write(self,
        statement: bytes, requires_response: bool = False) -> str | None:
        """Send a G-code statement through the socket connection.

        Automatically establishes the connection if not already connected.
        If configured to wait for responses, reads and validates the
        response from the device.

        Args:
            statement (bytes): The G-code statement to send.

        Returns:
            Optional[str]: If wait_for_response is True, returns the
                response from the device with

        Raises:
            RuntimeError: If the response is not valid
            socket.error: If there are communication errors.
        """

        if self._socket is None:
            self.connect()

        self._socket.send(statement)

        if self._wait_for_response:
            response = self._socket.recv(8192)
            response = response.decode("utf-8")

            if response[0] != "%":
                raise RuntimeError(response)

            return response[1:-1]

        return None
