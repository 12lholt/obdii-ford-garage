"""Tests for the JSON-safe serialization helpers. No OBD hardware required."""

from obd_garage.obd_client import serialize, unit_of


class FakeQuantity:
    """Stand-in for a Pint quantity (numeric sensor value)."""

    def __init__(self, magnitude, units):
        self.magnitude = magnitude
        self.units = units


def test_serialize_none():
    assert serialize(None) is None


def test_serialize_numeric_quantity():
    assert serialize(FakeQuantity(82.0, "kph")) == 82.0


def test_serialize_dtc_list():
    value = [("P0420", "Catalyst System Efficiency Below Threshold")]
    assert serialize(value) == [
        {"code": "P0420", "description": "Catalyst System Efficiency Below Threshold"}
    ]


def test_serialize_string_like_status():
    assert serialize("Not Searching") == "Not Searching"


def test_unit_of_quantity():
    assert unit_of(FakeQuantity(40, "celsius")) == "celsius"


def test_unit_of_plain():
    assert unit_of("ON") is None
    assert unit_of(None) is None
