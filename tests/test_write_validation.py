import asyncio
import math
import re
from pathlib import Path

import pytest

from flexit_bacnet import FlexitBACnet, econordic, nordic
from flexit_bacnet.bacnet import DeviceProperty, ObjectType, ReadValue
from flexit_bacnet.nordic import HUMIDITY_SETPOINT_HOME

UNSIGNED = DeviceProperty(ObjectType.POSITIVE_INTEGER_VALUE, 1229)


@pytest.mark.parametrize(
    "value, payload",
    [
        (0, b"\x21\x00"),
        (255, b"\x21\xff"),
        (256, b"\x22\x01\x00"),
        (600, b"\x22\x02\x58"),
        (0xFFFFFF, b"\x23\xff\xff\xff"),
        (0x1000000, b"\x24\x01\x00\x00\x00"),
        (0xFFFFFFFF, b"\x24\xff\xff\xff\xff"),
    ],
)
def test_unsigned_int_encoding(value, payload):
    # value is placed between opening (0x3e) and closing (0x3f) tag of context tag 3
    assert UNSIGNED.write_access_spec(value).split(b"\x3e")[1].split(b"\x3f")[0] == payload


@pytest.mark.parametrize("value", [-1, 0x100000000])
def test_unsigned_int_out_of_range(value):
    with pytest.raises(ValueError):
        UNSIGNED.write_access_spec(value)


@pytest.mark.parametrize("value", [-0.5, 0.5, 1.5, 255.9, math.nan, math.inf])
def test_unsigned_int_fractional_rejected(value):
    with pytest.raises(ValueError):
        UNSIGNED.write_access_spec(value)


def test_unsigned_int_integral_float_accepted():
    assert UNSIGNED.write_access_spec(600.0) == UNSIGNED.write_access_spec(600)


class _WriteRecorder:
    """Fake BACnet client: answers reads as a Nordic S3 and records writes."""

    def __init__(self):
        self.writes = []

    async def read_multiple(self, device_properties):
        return {
            (ObjectType.DEVICE, 2): [
                (ReadValue.OBJECT_NAME, "HvacFnct21y_A"),
                (ReadValue.DESCRIPTION, "800121-000001"),
            ]
        }

    async def write(self, device_property, value):
        self.writes.append((device_property, value))


def _nordic_device(recorder=None):
    device = FlexitBACnet("127.0.0.1", 2)
    device.bacnet = recorder or _WriteRecorder()
    asyncio.run(device.update())

    return device


def test_setter_requires_update_first():
    device = FlexitBACnet("127.0.0.1", 2)
    device.bacnet = _WriteRecorder()

    with pytest.raises(Exception, match="update"):
        asyncio.run(device.set_humidity_setpoint_home(65))

    assert device.bacnet.writes == []


def test_getter_requires_update_first():
    device = FlexitBACnet("127.0.0.1", 2)

    with pytest.raises(Exception, match="update"):
        device.humidity_setpoint_home


def test_property_mapping_complete():
    """Every constant device.py looks up on the mapping exists in both product lines."""
    source = (Path(__file__).parent.parent / "flexit_bacnet" / "device.py").read_text()
    names = set(re.findall(r"self\._prop_map\.([A-Z][A-Z0-9_]*)", source))

    assert names

    for module in (nordic, econordic):
        missing = sorted(name for name in names if not hasattr(module, name))
        assert missing == [], f"{module.__name__} lacks {missing}"


@pytest.mark.parametrize("percent", [-0.1, 100.1, math.nan])
def test_humidity_setpoint_rejected(percent):
    device = _nordic_device()

    with pytest.raises(ValueError):
        asyncio.run(device.set_humidity_setpoint_home(percent))

    assert device.bacnet.writes == []


def test_humidity_setpoint_accepted():
    device = _nordic_device()

    async def no_update():
        pass

    device.update = no_update
    asyncio.run(device.set_humidity_setpoint_home(65))

    assert device.bacnet.writes == [(HUMIDITY_SETPOINT_HOME, 65.0)]


class _EncodingWriteRecorder(_WriteRecorder):
    async def write(self, device_property, value):
        device_property.write_access_spec(value)
        await super().write(device_property, value)


@pytest.mark.parametrize(
    "setter",
    [
        "set_dehumidification_slope_on_delay",
        "set_dehumidification_switch_off_delay",
        "set_dehumidification_max_runtime",
    ],
)
def test_unsigned_setter_fractional_rejected(setter):
    device = _nordic_device(_EncodingWriteRecorder())

    with pytest.raises(ValueError):
        asyncio.run(getattr(device, setter)(1.5))

    assert device.bacnet.writes == []
