import pytest

from gscrib.enums import BaseEnum
from gscrib.codes.gcode_entry import GCodeEntry
from gscrib.codes.gcode_table import GCodeTable


# --------------------------------------------------------------------
# Fixtures and helper classes
# --------------------------------------------------------------------

class SampleEnum(BaseEnum):
    TEST1 = 1
    TEST2 = 2

class OtherEnum(BaseEnum):
    OTHER = 3

@pytest.fixture
def sample_entries():
    return (
        create_test_entry(SampleEnum.TEST1),
        create_test_entry(SampleEnum.TEST2),
    )

@pytest.fixture
def sample_table(sample_entries):
    return GCodeTable(sample_entries)

def create_test_entry(enum_value):
    return GCodeEntry(
        enum=enum_value,
        instruction=f'G{enum_value.value}',
        description=f'Test description for {enum_value.name}'
    )

# --------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------

def test_init_with_sample_entries(sample_entries):
    table = GCodeTable(sample_entries)
    assert len(table._entries) == 2

def test_get_entry_existing(sample_table):
    entry = sample_table.get_entry(SampleEnum.TEST1)
    assert isinstance(entry, GCodeEntry)
    assert entry.enum == SampleEnum.TEST1
    assert entry.instruction == 'G1'

def test_get_entry_non_existing(sample_table):
    with pytest.raises(KeyError):
        sample_table.get_entry(OtherEnum.OTHER)

def test_add_entry_new(sample_table):
    new_entry = create_test_entry(OtherEnum.OTHER)
    sample_table.add_entry(new_entry)
    entry = sample_table.get_entry(OtherEnum.OTHER)
    assert entry == new_entry

def test_add_entry_duplicate(sample_table):
    entry = create_test_entry(SampleEnum.TEST1)

    with pytest.raises(KeyError):
        sample_table.add_entry(entry)
