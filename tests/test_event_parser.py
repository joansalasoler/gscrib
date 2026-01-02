import pytest
from gscrib.host.protocol.event_parser import EventParser
from gscrib.host.protocol.events import (
    DeviceEvent,
    DeviceReadyEvent,
    DeviceOnlineEvent,
    DeviceErrorEvent,
    DeviceFaultEvent
)


# --------------------------------------------------------------------
# Fixtures and helper classes
# --------------------------------------------------------------------

@pytest.fixture
def parser():
    return EventParser()


# --------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------

def test_parse_ok(parser):
    event = parser.parse("ok")
    assert isinstance(event, DeviceReadyEvent)
    assert event.message == "ok"

def test_parse_error(parser):
    event = parser.parse("error: 20")
    assert isinstance(event, DeviceErrorEvent)

def test_parse_reprap_start(parser):
    event = parser.parse("start")
    assert isinstance(event, DeviceOnlineEvent)

def test_parse_grbl_start(parser):
    event = parser.parse("Grbl 1.1h ['$' for help]")
    assert isinstance(event, DeviceOnlineEvent)

def test_parse_alarm(parser):
    event = parser.parse("ALARM: Hard limit")
    assert isinstance(event, DeviceFaultEvent)

def test_parse_unknown(parser):
    event = parser.parse("Some unknown message")
    assert isinstance(event, DeviceEvent)
    assert type(event) is DeviceEvent

def test_extract_line_number(parser):
    assert parser.extract_line_number("Resend: 10") == 10
    assert parser.extract_line_number("Resend:N10") == 10
    assert parser.extract_line_number("rs:5") == 5
    assert parser.extract_line_number("invalid") == -1

def test_extract_grbl_fields_mpos(parser):
    msg = "<Idle|MPos:10.000,20.000,30.000|FS:0,0>"
    fields = parser.extract_fields(msg)
    assert fields["X"] == 10.0
    assert fields["Y"] == 20.0
    assert fields["Z"] == 30.0

def test_extract_grbl_fields_wpos(parser):
    msg = "<Idle|WPos:5.5,6.6,7.7>"
    fields = parser.extract_fields(msg)
    assert fields["X"] == 5.5
    assert fields["Y"] == 6.6
    assert fields["Z"] == 7.7

def test_extract_grbl_fields_fs(parser):
    msg = "<Run|FS:500,12000>"
    fields = parser.extract_fields(msg)
    assert fields["F"] == 500.0
    assert fields["S"] == 12000.0

def test_extract_grbl_fields_generic(parser):
    msg = "<...|Buf:15|...>"
    fields = parser.extract_fields(msg)
    assert fields["Buf"] == 15.0

def test_extract_reprap_M114_report_simple(parser):
    msg = "ok C: X:0.00 Y:1.00 Z:2.00 E:3.00"
    fields = parser.extract_fields(msg)
    assert fields["X"] == 0.0
    assert fields["Y"] == 1.0
    assert fields["Z"] == 2.0
    assert fields["E"] == 3.0

def test_extract_reprap_M114_report_complex(parser):
    msg = "X:0.00 Y:127.00 Z:-145.00 E:0.00 Count X: 0 Y:10160 Z:116000"
    fields = parser.extract_fields(msg)
    assert fields["X"] == 0.0
    assert fields["Y"] == 127.0
    assert fields["Z"] == -145.0
    assert fields["E"] == 0.0

def test_extract_reprap_M105_report_simple(parser):
    msg = "ok T:201 B:117"
    fields = parser.extract_fields(msg)
    assert fields["T"] == 201.0
    assert fields["B"] == 117.0

def test_extract_reprap_M105_report_with_targets(parser):
    msg = "ok T:201 /202 B:117 /120"
    fields = parser.extract_fields(msg)
    assert fields["T"] == 201.0
    assert fields["B"] == 117.0

def test_extract_reprap_M105_report_complex(parser):
    msg = "ok T:20.2 /0.0 B:19.1 /0.0 T0:20.2 /0.0 @:0 B@:0 P:19.8 A:26.4"
    fields = parser.extract_fields(msg)
    assert fields["T"] == 20.2
    assert fields["B"] == 19.1
    assert fields["T0"] == 20.2
    assert fields["@"] == 0.0
    assert fields["B@"] == 0.0
    assert fields["P"] == 19.8
    assert fields["A"] == 26.4

def test_extract_fields_malformed(parser):
    with pytest.raises(ValueError):
        parser.extract_fields("MPos:10,,20")

    with pytest.raises(ValueError):
        parser.extract_fields("<...|FS:10>")
