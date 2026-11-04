"""room_humidity: the humidity Flexit GO shows, maximum over the wireless room sensors (issue #31)."""

import asyncio

import pytest

from flexit_bacnet import FlexitBACnet, econordic, nordic
from flexit_bacnet.bacnet import ObjectType, PropertyError, ReadValue

UNKNOWN_OBJECT = PropertyError(1, 31)


class _Client:
    """Fake BACnet client: answers with the given present values, unknown-object for the rest."""

    def __init__(self, serial: str, values: dict):
        self.serial = serial
        self.values = values

    async def read_multiple(self, device_properties):
        state = {}
        for p in device_properties:
            if p.object_type == ObjectType.DEVICE:
                state[p.object_identifier] = [
                    (ReadValue.OBJECT_NAME, "HvacFnct21y_A"),
                    (ReadValue.DESCRIPTION, self.serial),
                ]
            else:
                state[p.object_identifier] = [
                    (ReadValue.PRESENT_VALUE, self.values.get(p.object_identifier, UNKNOWN_OBJECT))
                ]
        return state


def _device(serial: str, values: dict) -> FlexitBACnet:
    device = FlexitBACnet("127.0.0.1", 2)
    device.bacnet = _Client(serial, values)
    asyncio.run(device.update())
    return device


@pytest.mark.parametrize("serial, module", [("800220-000000", nordic), ("800481-000000", econordic)])
def test_room_humidity_is_the_rf_maximum(serial, module):
    # values a Nordic CL4 RER answered with three CI77 sensors at 50, 62 and 38 %
    device = _device(serial, {
        module.ROOM_HUMIDITY_MAX.object_identifier: 62.0,
        module.ROOM_1_HUMIDITY.object_identifier: 50.0,
        module.ROOM_2_HUMIDITY.object_identifier: 62.0,
        module.ROOM_3_HUMIDITY.object_identifier: 38.0,
    })

    assert device.room_humidity == 62.0


def test_room_humidity_rounded():
    device = _device("800220-000000", {nordic.ROOM_HUMIDITY_MAX.object_identifier: 41.26})

    assert device.room_humidity == 41.3


def test_room_humidity_none_without_rf_sensors():
    # the unit reports 0 when no wireless humidity sensor is connected
    device = _device("800220-000000", {nordic.ROOM_HUMIDITY_MAX.object_identifier: 0.0})

    assert device.room_humidity is None


def test_room_humidity_none_when_object_missing():
    assert _device("800220-000000", {}).room_humidity is None


def test_room_humidity_reading_metadata():
    info = FlexitBACnet.get_reading("room_humidity")

    assert info.label == "Room humidity"
