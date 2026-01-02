import pytest
import logging
from io import StringIO
from gscrib.writers.log_writer import LogWriter


# --------------------------------------------------------------------
# Fixtures and helper classes
# --------------------------------------------------------------------

@pytest.fixture
def log_writer():
    return LogWriter()

@pytest.fixture
def captured_logger(log_writer):
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)

    logger = log_writer.get_logger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    yield log_stream

    logger.removeHandler(handler)
    log_stream.close()


# --------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------

def test_initialization():
    log_writer = LogWriter()
    assert isinstance(log_writer.get_logger(), logging.Logger)

def test_connect(log_writer):
    result = log_writer.connect()
    assert result is log_writer

def test_disconnect(log_writer):
    log_writer.disconnect()
    log_writer.disconnect(wait=False)

def test_flush(log_writer):
    log_writer.flush()

def test_set_level_with_string(log_writer):
    log_writer.set_level("debug")
    assert log_writer._level == logging.DEBUG

def test_set_level_with_integer(log_writer):
    log_writer.set_level(logging.WARNING)
    assert log_writer._level == logging.WARNING

def test_write(log_writer, captured_logger):
    test_gcode = b"G1 X10 Y10\n"
    log_writer.write(test_gcode)
    assert captured_logger.getvalue().strip() == "G1 X10 Y10"

@pytest.mark.parametrize("invalid_input", [b"", b"\n", b"   \n",])
def test_write_edge_cases(log_writer, captured_logger, invalid_input):
    log_writer.write(invalid_input)
    assert len(captured_logger.getvalue().strip()) == 0

def test_context_manager(log_writer, captured_logger):
    with log_writer as writer:
        assert writer is log_writer
        writer.write(b"G1 X10\n")

    assert "G1 X10" in captured_logger.getvalue()

def test_set_level_invalid_string(log_writer):
    with pytest.raises(ValueError):
        log_writer.set_level("invalid_level")
