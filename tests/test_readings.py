"""Label and unit metadata of FlexitBACnet properties."""

import pytest

from flexit_bacnet import FlexitBACnet, Reading, Unit


def test_every_public_property_has_a_reading():
    properties = [
        name for name, member in vars(FlexitBACnet).items()
        if isinstance(member, property) and not name.startswith("_")
    ]

    assert properties
    assert [info.name for info in FlexitBACnet.readings()] == properties


def test_labels_are_unique():
    labels = [info.label for info in FlexitBACnet.readings()]

    assert len(labels) == len(set(labels))


def test_get_reading():
    assert FlexitBACnet.get_reading("extract_air_humidity") == Reading(
        "extract_air_humidity", "Extract air humidity", Unit.PERCENT
    )
    assert FlexitBACnet.get_reading("outside_air_temperature").unit is Unit.CELSIUS
    assert FlexitBACnet.get_reading("comfort_button").unit is None


def test_get_reading_unknown():
    with pytest.raises(KeyError):
        FlexitBACnet.get_reading("no_such_property")


def test_decorated_getters_are_still_properties():
    assert isinstance(FlexitBACnet.extract_air_humidity, property)


@pytest.mark.parametrize(
    "unit, value, text",
    [
        (Unit.CELSIUS, 21.5, "21.5 °C"),
        (Unit.PERCENT, 0.0, "0.0 %"),
        (Unit.MINUTES, 120, "120 min"),
        (None, True, "True"),
        (Unit.PERCENT, None, "(unsupported)"),
        (None, None, "(unsupported)"),
    ],
)
def test_format(unit, value, text):
    assert Reading("x", "X", unit).format(value) == text
