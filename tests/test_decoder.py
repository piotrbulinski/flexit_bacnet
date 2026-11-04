"""Decoder edge cases beyond what the recorded answers contain."""

import asyncio

import pytest

from flexit_bacnet import FlexitBACnet, nordic
from flexit_bacnet.bacnet import BACnetDecoder, DecodingError, ObjectType, ReadValue


def _value(hex_value: str):
    # wrap an application-tagged value in the property-value opening/closing tags 4
    return BACnetDecoder(bytes.fromhex("4e" + hex_value + "4f")).read_value()


@pytest.mark.parametrize(
    "encoded, expected",
    [
        ("00", None),  # null
        ("10", False),  # boolean false
        ("11", True),  # boolean true
        ("2203e8", 1000),  # unsigned, 2 octets
        ("31ff", -1),  # signed
        ("55083ff8000000000000", 1.5),  # double
        ("9201f4", 500),  # enumerated, 2 octets (was read as 1 octet)
        ("c4020000 02".replace(" ", ""), (ObjectType.DEVICE, 2)),  # object identifier
        ("c4420000 08".replace(" ", ""), (264, 8)),  # proprietary object type
        ("7505" + "04" + "0041" + "00c4", "AÄ"),  # UCS-2 character string, extended length
        ("7504054142c4", "ABÄ"),  # ISO 8859-1 character string
    ],
)
def test_application_values(encoded, expected):
    assert _value(encoded) == expected


def test_extended_length_254():
    text = "x" * 300
    encoded = "75fe" + (len(text) + 1).to_bytes(2, "big").hex() + "00" + text.encode().hex()

    assert _value(encoded) == text


def test_list_of_values():
    # e.g. an object-list: several object identifiers inside one property value
    assert _value("c402000002" + "c400000001") == [(ObjectType.DEVICE, 2), (ObjectType.ANALOG_INPUT, 1)]


def test_unknown_character_set_raises_decoding_error():
    with pytest.raises(DecodingError):
        _value("720941")


def test_property_array_index_is_skipped():
    # object AV 1, property 87 (priority-array) index 16 -> real 21.5
    data = bytes.fromhex("0c00800001" + "1e" + "2957" + "3910" + "4e" + "4441ac0000" + "4f" + "1f")
    decoder = BACnetDecoder(data)

    assert decoder.parse_object_identifier() == (ObjectType.ANALOG_VALUE, 1)
    assert decoder.parse_list_of_results() == [(87, 21.5)]


def test_object_absent_from_answer_is_none():
    class _Client:
        async def read_multiple(self, device_properties):
            # an answer that leaves out EXTRACT_AIR_HUMIDITY entirely
            return {
                (ObjectType.DEVICE, 2): [(ReadValue.OBJECT_NAME, "HvacFnct21y_A")],
                nordic.OUTSIDE_AIR_TEMPERATURE.object_identifier: [(ReadValue.PRESENT_VALUE, 7.9)],
            }

    device = FlexitBACnet("127.0.0.1", 2)
    device.bacnet = _Client()
    asyncio.run(device.update())

    assert device.outside_air_temperature == 7.9
    assert device.extract_air_humidity is None
    assert device.serial_number == ""


def test_timeout_and_retries_reach_the_client():
    device = FlexitBACnet("127.0.0.1", 2, timeout=3.0, read_retries=2)

    assert device.bacnet.timeout == 3.0
    assert device.bacnet.read_retries == 2
