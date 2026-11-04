"""Objects a unit does not have are reported as None, not as a reading of 0."""

import asyncio

import pytest

from flexit_bacnet import FlexitBACnet, nordic
from flexit_bacnet.bacnet import BACnetDecoder, ObjectType, PropertyError, ReadValue

# property access error answered by a Nordic S4 for a missing object:
# error class object (1), error code unknown-object (31)
S4_UNKNOWN_OBJECT_ERROR = bytes.fromhex("5e9101911f5f")

MISSING = PropertyError(1, 31)


def test_decoder_keeps_property_access_error():
    assert BACnetDecoder(S4_UNKNOWN_OBJECT_ERROR).read_value() == MISSING


def test_decoder_reads_present_value():
    # opening tag 4, real 21.5, closing tag 4
    assert BACnetDecoder(bytes.fromhex("4e4441ac00004f")).read_value() == 21.5


class _StateClient:
    """Fake BACnet client: answers reads as a Nordic S4 with the given object values."""

    def __init__(self, values):
        self.values = values

    async def read_multiple(self, device_properties):
        state = {
            (ObjectType.DEVICE, 2): [
                (ReadValue.OBJECT_NAME, "HvacFnct21y_A"),
                (ReadValue.DESCRIPTION, "800130-000001"),
            ]
        }

        for device_property in device_properties:
            if device_property.object_type == ObjectType.DEVICE:
                continue

            value = self.values.get(device_property.object_identifier, 0)
            state[device_property.object_identifier] = [(ReadValue.PRESENT_VALUE, value)]

        return state


def _device(values):
    device = FlexitBACnet("127.0.0.1", 2)
    device.bacnet = _StateClient(values)
    asyncio.run(device.update())

    return device


@pytest.mark.parametrize(
    "getter, device_property",
    [
        ("extract_air_humidity", nordic.EXTRACT_AIR_HUMIDITY),
        ("dehumidification_fan_control", nordic.DEHUMIDIFICATION_FAN_CONTROL),
        ("fireplace_mode_runtime", nordic.FIREPLACE_VENTILATION_RUNTIME),
        ("comfort_button", nordic.COMFORT_BUTTON),
        ("heat_exchanger_efficiency", nordic.ROTATING_HEAT_EXCHANGER_EFFICIENCY),
        ("ventilation_mode", nordic.VENTILATION_MODE),
    ],
)
def test_missing_object_is_none(getter, device_property):
    device = _device({device_property.object_identifier: MISSING})

    assert getattr(device, getter) is None


def test_present_zero_is_still_zero():
    device = _device({})

    assert device.extract_air_humidity == 0.0
    assert device.dehumidification_fan_control == 0.0
    assert device.comfort_button is False


def test_every_getter_handles_missing_objects():
    device = FlexitBACnet("127.0.0.1", 2)
    client = _StateClient({})
    device.bacnet = client
    client.values = {p.object_identifier: MISSING for p in nordic.DEVICE_PROPERTIES}
    asyncio.run(device.update())

    identity = {"device_name", "serial_number", "model"}
    getters = [
        name for name, value in vars(FlexitBACnet).items()
        if isinstance(value, property) and not name.startswith("_") and name not in identity
    ]

    assert getters
    assert {name: getattr(device, name) for name in getters if getattr(device, name) is not None} == {}


def test_extract_air_temperature_falls_back_when_primary_missing():
    device = _device({
        nordic.EXTRACT_AIR_TEMPERATURE.object_identifier: MISSING,
        nordic.EXTRACT_AIR_TEMPERATURE_ALT.object_identifier: 21.94,
    })

    assert device.extract_air_temperature == 21.9


def test_extract_air_temperature_keeps_primary_when_alt_missing():
    device = _device({
        nordic.EXTRACT_AIR_TEMPERATURE.object_identifier: 22.0,
        nordic.EXTRACT_AIR_TEMPERATURE_ALT.object_identifier: MISSING,
    })

    assert device.extract_air_temperature == 22.0
