import io
import sys
import pytest
from io import StringIO, BytesIO
from gscrib.writers import FileWriter


# --------------------------------------------------------------------
# Fixtures and helper classes
# --------------------------------------------------------------------

@pytest.fixture
def temp_file(tmp_path):
    return str(tmp_path / "test.gcode")

@pytest.fixture
def text_stream():
    return StringIO()

@pytest.fixture
def binary_stream():
    return BytesIO()


# --------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------

# Test initialization

def test_init_with_string_path(temp_file):
    writer = FileWriter(temp_file)
    assert writer._output == temp_file
    assert writer._file is None

def test_init_with_text_stream(text_stream):
    writer = FileWriter(text_stream)
    assert writer._output == text_stream
    assert writer._file is None

def test_init_with_binary_stream(binary_stream):
    writer = FileWriter(binary_stream)
    assert writer._output == binary_stream
    assert writer._file is None

def test_init_with_std_stream():
    writer = FileWriter(sys.stdout)
    assert writer._output == sys.stdout
    assert writer._file is None

# Test connection

def test_connect_with_string_path(temp_file):
    writer = FileWriter(temp_file).connect()
    assert isinstance(writer._file, io.IOBase)
    assert not writer._file.closed
    writer.disconnect()
    assert writer._file is None

def test_connect_with_text_stream(text_stream):
    writer = FileWriter(text_stream).connect()
    assert writer._file == text_stream
    writer.disconnect()
    assert not text_stream.closed
    assert writer._file is None

def test_connect_with_binary_stream(binary_stream):
    writer = FileWriter(binary_stream).connect()
    assert writer._file == binary_stream
    writer.disconnect()
    assert not binary_stream.closed
    assert writer._file is None

def test_connect_with_std_stream():
    writer = FileWriter(sys.stderr.buffer).connect()
    assert writer._file == sys.stderr.buffer
    writer.disconnect()
    assert writer._file is None

def test_connect_already_connected(temp_file):
    writer = FileWriter(temp_file)
    writer.connect()
    open_file = writer._file
    assert open_file is not None
    writer.connect() # Should not open a new file
    assert writer._file == open_file
    writer.disconnect()

# Test auto-connection

def test_auto_connect_on_write(temp_file):
    writer = FileWriter(temp_file)
    assert writer._file is None
    writer.write(b"G1 X10 Y10\n")
    assert writer._file is not None
    writer.disconnect()

# Test writing

def test_write_to_text_stream(text_stream):
    test_line = b"G1 X10 Y10\n"
    writer = FileWriter(text_stream)
    writer.write(test_line)
    assert text_stream.getvalue() == "G1 X10 Y10\n"

def test_write_to_binary_stream(binary_stream):
    test_line = b"G1 X10 Y10\n"
    writer = FileWriter(binary_stream)
    writer.write(test_line)
    assert binary_stream.getvalue() == test_line

def test_write_to_std_stream(capsys):
    test_line = b"G1 X10 Y10\r\n"
    writer = FileWriter(sys.stdout)
    writer.write(test_line)
    captured = capsys.readouterr()
    assert captured.out == "G1 X10 Y10\r\n"

def test_write_to_binary_file(temp_file):
    test_line = b"G1 X10 Y10\n"
    writer = FileWriter(temp_file)
    writer.write(test_line)
    writer.disconnect()

    with open(temp_file, 'rb') as f:
        content = f.read()

    assert content == test_line

def test_write_multiple_statements(temp_file):
    statements = [
        b"G1 X10 Y10\n",
        b"G1 X20 Y20\n",
        b"G1 X30 Y30\n"
    ]

    writer = FileWriter(temp_file)
    writer.connect()

    for statement in statements:
        writer.write(statement)

    writer.disconnect() # Ensures content flush

    with open(temp_file, 'rb') as f:
        content = f.read()

    assert content == b"".join(statements)

def test_write_after_disconnect(temp_file):
    writer = FileWriter(temp_file)
    writer.write(b"G1 X10 Y10\n")
    writer.disconnect()

    # Should auto-reconnect

    writer.write(b"G1 X20 Y20\n")
    writer.disconnect()

    with open(temp_file, 'rb') as f:
        content = f.read()

    assert content == b"G1 X20 Y20\n"

# Test error handling

def test_write_non_utf8_bytes(temp_file):
    writer = FileWriter(temp_file)
    writer.write(b"\x80\xff")  # Invalid UTF-8 bytes
    writer.disconnect()

def test_write_mixed_encodings():
    writer = FileWriter(sys.stdout)

    with pytest.raises(UnicodeDecodeError):
        writer.write("Hello".encode('utf-16'))

def test_write_to_invalid_path():
    writer = FileWriter("/invalid/path/test.gcode")

    with pytest.raises(OSError):
        writer.write(b"G1 X10 Y10\n")
