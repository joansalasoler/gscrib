import pytest
from gscrib.host.exceptions import EmptyCommand, MultipleCommands
from gscrib.host.scheduler import Command


# --------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------

def test_initialization():
    command = Command(10, "G0 X0 Y0", False)
    assert command.line_number == 10
    assert command.instruction == "G0 X0 Y0"
    assert command.signed is False

def test_format_line_unsigned():
    command = Command(1, "M105", False)
    assert command.format_line() == "M105"

def test_format_line_signed():
    line = "G1 X131.338 Y133.349 E0.0091"
    expected = "N66555 G1 X131.338 Y133.349 E0.0091*91"
    command = Command(66555, line, True)
    assert command.format_line() == expected

def test_checksum_calculation():
    line = "N66556 G1 X131.574 Y133.428 E0.0046"
    checksum = Command._xor_checksum(line)
    assert checksum == 92

@pytest.mark.parametrize("raw_gcode, expected", [
    ("M105", "M105"),
    ("G1 X10 Y10", "G1 X10 Y10"),
    ("g1 x10 y10", "G1 X10 Y10"),
    ("  G1 X10  ", "G1 X10"),
    ("\tG1 X10\t", "G1 X10"),
    ("G1 X10 ; Line comment", "G1 X10"),
    ("G1 X10 (Inline comment)", "G1 X10"),
    ("G1 (Inline) X10 ; Line", "G1  X10"),
    ("G1 X10 (Comment 1) Y10 (Comment 2)", "G1 X10  Y10"),
    ("  g1 x10 ; end (comment)  ", "G1 X10"),
])
def test_command_normalization(raw_gcode, expected):
    command = Command(1, raw_gcode, False)
    assert command.instruction == expected

@pytest.mark.parametrize("raw_gcode", [
    "",                     # Empty string
    "\n",                   # Empty lines
    "   ",                  # Whitespace only
    "; Comment only",       # Line comment only
    "(Comment only)",       # Inline comment only,
    "(first) ; second",     # Combined comments
])
def test_empty_command_validation(raw_gcode):
    with pytest.raises(EmptyCommand):
        Command(1, raw_gcode, False)

@pytest.mark.parametrize("raw_gcode", [
    "G1 X10\nG1 Y10",       # Multi-line string (newline)
    "G1 X10\rG1 Y10",       # Multi-line string (carriage return)
])
def test_multiple_command_validation(raw_gcode):
    with pytest.raises(MultipleCommands):
        Command(1, raw_gcode, False)

def test_immutability_errors(): # frozen=True
    command = Command(1, "G1", False)

    with pytest.raises(AttributeError):
        command.instruction = "G2"
