import pytest
from types import SimpleNamespace
from gscrib.config import GConfig


# --------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------

def test_from_object_with_dict():
    config_dict = {
        "output": "test.gcode",
        "decimal_places": 3,
        "comment_symbols": "#",
        "unknown_key": "value",
    }

    config = GConfig.from_object(config_dict)
    assert config.output == "test.gcode"
    assert config.decimal_places == 3
    assert config.comment_symbols == "#"
    assert config.host == "localhost"  # Default value

def test_from_object_with_namespace():
    namespace = SimpleNamespace(
        output="output.gcode",
        port=9000,
        unknown_key="value"
    )

    config = GConfig.from_object(namespace)
    assert config.output == "output.gcode"
    assert config.port == 9000
    assert config.host == "localhost"  # Default value
