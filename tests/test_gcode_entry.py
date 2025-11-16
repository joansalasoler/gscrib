import pytest
from gscrib.enums import BaseEnum
from gscrib.codes.gcode_entry import GCodeEntry


# --------------------------------------------------------------------
# Fixtures and helper classes
# --------------------------------------------------------------------


class SampleEnum(BaseEnum):
    TEST1 = 1
    TEST2 = 2


# --------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------


def test_gcode_entry_init():
    sample_entry = GCodeEntry(
        enum=SampleEnum.TEST1, instruction="G01", description="Linear movement"
    )

    assert sample_entry.enum == SampleEnum.TEST1
    assert sample_entry.instruction == "G01"
    assert sample_entry.description == "Linear movement"


def test_gcode_entry_empty_instruction():
    with pytest.raises(ValueError, match="Instruction cannot be empty"):
        GCodeEntry(
            enum=SampleEnum.TEST2, instruction="", description="Test description"
        )


def test_gcode_entry_empty_description():
    with pytest.raises(ValueError, match="Description cannot be empty"):
        GCodeEntry(enum=SampleEnum.TEST2, instruction="G01", description="")
