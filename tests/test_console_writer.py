import pytest
import sys, io
from gscrib.writers import ConsoleWriter


# --------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------

def test_connect_with_stdout():
    writer = ConsoleWriter().connect()
    assert writer._is_terminal is True
    assert writer._file == sys.stdout.buffer
    assert not isinstance(writer._output, str)

def test_connect_with_stderr():
    writer = ConsoleWriter(stderr=True).connect()
    assert writer._is_terminal is True
    assert writer._file == sys.stderr.buffer
    assert not isinstance(writer._output, str)

def test_connect_with_unbuffered_stdout():
    original_stdout = sys.stdout
    sys.stdout = io.StringIO()

    try:
        writer = ConsoleWriter().connect()
        assert writer._is_terminal is True
        assert writer._file == sys.stdout
        assert not isinstance(writer._output, str)
    finally:
        sys.stdout = original_stdout

def test_connect_with_unbuffered_stderr():
    original_stderr = sys.stderr
    sys.stderr = io.StringIO()

    try:
        writer = ConsoleWriter(stderr=True).connect()
        assert writer._is_terminal is True
        assert writer._file == sys.stderr
        assert not isinstance(writer._output, str)
    finally:
        sys.stderr = original_stderr

def test_write_to_stdout(capfdbinary):
    writer = ConsoleWriter().connect()
    writer.write(b"G1 X10 Y10\n")

    captured = capfdbinary.readouterr()
    assert captured.out == b"G1 X10 Y10\n"
    assert captured.err == b""

def test_write_to_stderr(capfdbinary):
    writer = ConsoleWriter(stderr=True).connect()
    writer.write(b"G1 X10 Y10\n")

    captured = capfdbinary.readouterr()
    assert captured.out == b""
    assert captured.err == b"G1 X10 Y10\n"

def test_write_to_stdout_unbuffered():
    original_stdout = sys.stdout
    sys.stdout = io.StringIO()

    try:
        writer = ConsoleWriter().connect()
        writer.write(b"G1 X10 Y10\n")
        assert sys.stdout.getvalue() == "G1 X10 Y10\n"
    finally:
        sys.stdout = original_stdout

def test_write_to_stderr_unbuffered():
    original_stderr = sys.stderr
    sys.stderr = io.StringIO()

    try:
        writer = ConsoleWriter(stderr=True).connect()
        writer.write(b"G1 X10 Y10\n")
        assert sys.stderr.getvalue() == "G1 X10 Y10\n"
    finally:
        sys.stderr = original_stderr

def test_disconnect():
    writer = ConsoleWriter().connect()
    writer.disconnect()
    assert writer._file == None
