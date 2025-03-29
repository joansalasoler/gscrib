import pytest
import numpy as np
from typeguard import TypeCheckError
from gscrib.formatters import DefaultFormatter


# --------------------------------------------------------------------
# Fixtures and helper classes
# --------------------------------------------------------------------

@pytest.fixture
def formatter():
    return DefaultFormatter()


# --------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------

# Test initialization

def test_default_initialization(formatter):
    assert formatter._decimal_places == 5
    assert formatter._labels == {"X": "X", "Y": "Y", "Z": "Z"}
    assert formatter._comment_template == "; {}"

# Test axis label settings

def test_set_axis_label_valid(formatter):
    formatter.set_axis_label("x", "A")
    assert formatter._labels["X"] == "A"
    formatter.set_axis_label("X", "B")
    assert formatter._labels["X"] == "B"

def test_set_axis_label_invalid_axis(formatter):
    with pytest.raises(ValueError):
        formatter.set_axis_label("w", "A")

def test_set_axis_label_empty(formatter):
    with pytest.raises(ValueError):
        formatter.set_axis_label("x", "  ")

# Test comment symbols

def test_set_comment_symbols_standard(formatter):
    formatter.set_comment_symbols(";")
    assert formatter._comment_template == "; {}"

def test_set_comment_symbols_parentheses(formatter):
    formatter.set_comment_symbols("(")
    assert formatter._comment_template == "( {} )"

def test_set_comment_symbols_empty(formatter):
    with pytest.raises(ValueError):
        formatter.set_comment_symbols("  ")

# Test decimal places

def test_set_decimal_places_valid(formatter):
    formatter.set_decimal_places(3)
    assert formatter._decimal_places == 3

def test_set_decimal_places_zero(formatter):
    formatter.set_decimal_places(0)
    assert formatter._decimal_places == 0

def test_set_decimal_places_negative(formatter):
    with pytest.raises(ValueError):
        formatter.set_decimal_places(-1)

# Test comment formatting

def test_format_comment_default(formatter):
    assert formatter.comment("Test") == "; Test"

def test_format_comment_empty(formatter):
    formatter.set_comment_symbols("[")
    assert formatter.comment("") == "[  ]"

# Test number formatting

def test_format_number_comprehensive(formatter):
    assert formatter.number(42) == "42"
    assert formatter.number(3.14159) == "3.14159"
    assert formatter.number(-42.123) == "-42.123"
    assert formatter.number(0) == "0"
    assert formatter.number(-0) == "0"
    assert formatter.number(0.0) == "0"
    assert formatter.number(1e-4) == "0.0001"
    assert formatter.number(1.2e1) == "12"
    assert formatter.number(np.int32(42)) == "42"
    assert formatter.number(np.float64(-0.9)) == "-0.9"

def test_format_number_decimal_edge_cases(formatter):
    formatter.set_decimal_places(3)
    assert formatter.number(0.1234) == "0.123"
    assert formatter.number(0.999) == "0.999"
    assert formatter.number(0.9999) == "1"
    assert formatter.number(-0.9999) == "-1"
    assert formatter.number(0.001) == "0.001"
    assert formatter.number(-0.001) == "-0.001"
    assert formatter.number(0.0001) == "0"

def test_format_number_trailing_zeros(formatter):
    formatter.set_decimal_places(3)
    assert formatter.number(1.100) == "1.1"
    assert formatter.number(1.000) == "1"
    assert formatter.number(10.10) == "10.1"

def test_format_number_leading_zeros(formatter):
    assert formatter.number(.5) == "0.5"
    assert formatter.number(-.5) == "-0.5"

def test_format_number_invalid_types(formatter):
    with pytest.raises(ValueError):
        formatter.number(float("inf"))

    with pytest.raises(ValueError):
        formatter.number(float("-inf"))

    with pytest.raises(ValueError):
        formatter.number(float("nan"))

    with pytest.raises(TypeError):
        formatter.number(1 + 2j)

    with pytest.raises(TypeError):
        formatter.number(complex(1, 2))

    with pytest.raises(TypeCheckError):
        formatter.number("123")

    with pytest.raises(TypeCheckError):
        formatter.number(None)

# Test parameters formatting

def test_format_parameters_empty(formatter):
    assert formatter.parameters({}) == ""

def test_format_parameters_axes(formatter):
    params = {"x": 10.123, "y": 20.459, "z": 0}
    formatter.set_decimal_places(2)
    assert formatter.parameters(params) == "X10.12 Y20.46 Z0"

def test_format_parameters_custom(formatter):
    params = {"x": 10, "F": 1000, "comment": "test"}
    assert formatter.parameters(params) == "X10 F1000 COMMENTtest"

# Test command formatting

def test_format_command_no_params(formatter):
    assert formatter.command("G0") == "G0"

def test_format_command_with_params(formatter):
    params = {"x": 10, "y": 20}
    assert formatter.command("G1", params) == "G1 X10 Y20"

def test_format_command_with_mixed_params(formatter):
    params = {"x": 10, "F": 1000, "T": "0102"}
    assert formatter.command("G1", params) == "G1 X10 F1000 T0102"

# Test line formatting

def test_format_line_simple(formatter):
    result = formatter.line("G1 X0 Y0")
    assert result.endswith(formatter._line_endings)
    assert result.rstrip() == "G1 X0 Y0"

def test_format_line_with_trailing_spaces(formatter):
    result = formatter.line("G1 X0 Y0   ")
    assert result.rstrip() == "G1 X0 Y0"

def test_format_line_endings(formatter):
    formatter.set_line_endings("!")
    result = formatter.line("G1 X0 Y0  ")
    assert result.endswith(formatter._line_endings)
    assert result == "G1 X0 Y0!"

# Test complex scenarios

def test_full_gcode_line(formatter):
    params = {"x": 10.1231, "y": 20.45609, "F": 1000}
    formatter.set_decimal_places(3)
    command = formatter.command("G1", params)
    line = formatter.line(command)
    assert line.rstrip() == "G1 X10.123 Y20.456 F1000"

def test_custom_axis_labels_affect_formatting(formatter):
    params = {"x": 10, "y": 20, "z": 30}
    formatter.set_axis_label("x", "A")
    formatter.set_axis_label("y", "B")
    formatter.set_axis_label("z", "C")
    assert formatter.command("G1", params) == "G1 A10 B20 C30"
