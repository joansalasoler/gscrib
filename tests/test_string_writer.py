import pytest
from io import StringIO
from gscrib.writers import StringWriter


# --------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------

def test_init_default_state():
    writer = StringWriter()
    assert isinstance(writer._output, StringIO)
    assert writer._file is not None
    assert writer._file == writer._output

def test_to_string_empty():
    writer = StringWriter()
    assert writer.to_string() == ""

def test_str_method():
    writer = StringWriter()
    writer.write(b"G1 X10 Y10\n")
    assert str(writer) == "G1 X10 Y10\n"

def test_write_single_statement():
    writer = StringWriter()
    writer.write(b"G1 X10 Y10\n")
    assert writer.to_string() == "G1 X10 Y10\n"

def test_write_multiple_statements():
    writer = StringWriter()
    writer.write(b"G1 X10 Y10\n")
    writer.write(b"G1 X20 Y20\n")
    writer.write(b"G1 X30 Y30\n")
    expected = "G1 X10 Y10\nG1 X20 Y20\nG1 X30 Y30\n"
    assert writer.to_string() == expected

def test_to_string_auto_reconnect():
    writer = StringWriter()
    writer.write(b"G1 X10 Y10\n")
    writer.disconnect()
    writer.write(b"M30\n")
    writer.disconnect()
    assert writer.to_string() == "G1 X10 Y10\nM30\n"
