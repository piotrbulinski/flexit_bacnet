"""Replay the answers recorded from every unit under tests/fixtures/.

Each folder there holds answers recorded from one real unit with
tests/live/record_fixtures.py (see "Adding tests for your unit" in the
README). Every folder is picked up automatically: no test code is needed to
cover a new model, only the recorded files.
"""

import asyncio
import re

import pytest

from flexit_bacnet import FlexitBACnet
from flexit_bacnet.bacnet import ObjectType, ReadValue, _parse_read_property_multiple_response

from conftest import FIXTURES, Recorded

UNITS = sorted(path.name for path in FIXTURES.iterdir() if (path / "update.json").exists())


def _recorded(unit: str, name: str) -> Recorded:
    path = FIXTURES / unit / f"{name}.json"
    if not path.exists():
        pytest.skip(f"{unit} has no {name}.json")
    return Recorded(path)


class _ReplayClient:
    def __init__(self, response: bytes):
        self.response = response

    async def read_multiple(self, device_properties):
        return _parse_read_property_multiple_response(self.response)


def _device(unit: str) -> FlexitBACnet:
    response = _recorded(unit, "update").reassembled()
    device_id = next(
        instance for object_type, instance in _parse_read_property_multiple_response(response)
        if object_type == ObjectType.DEVICE
    )

    device = FlexitBACnet("127.0.0.1", device_id)
    device.bacnet = _ReplayClient(response)
    asyncio.run(device.update())

    return device


def test_fixtures_found():
    assert UNITS, "no tests/fixtures/<unit>/update.json found"


@pytest.mark.parametrize("unit", UNITS)
def test_update_answer_decodes(unit):
    recorded = _recorded(unit, "update")
    state = _parse_read_property_multiple_response(recorded.reassembled())

    assert set(state) == recorded.requested_objects()

    assert any(object_type == ObjectType.DEVICE for object_type, _ in state)


@pytest.mark.parametrize("unit", UNITS)
def test_every_reading_works(unit):
    device = _device(unit)

    assert device.serial_number, "the recorded answer has no serial number"

    for info in FlexitBACnet.readings():
        # must not raise; None means the unit does not have the object
        info.format(getattr(device, info.name))


@pytest.mark.parametrize("unit", UNITS)
def test_serial_number_is_scrubbed(unit):
    for path in sorted((FIXTURES / unit).glob("*.json")):
        for datagram in Recorded(path).responses:
            for serial in re.findall(rb"\d{6}-\d{6}", datagram):
                assert serial.endswith(b"-000000"), f"{path.name} contains serial number {serial.decode()}"


@pytest.mark.parametrize("unit", UNITS)
def test_segmented_answer_reassembles(unit):
    recorded = _recorded(unit, "segmented_present_value_and_name")

    # a unit with a bigger max-APDU may answer in one piece
    state = _parse_read_property_multiple_response(recorded.reassembled())

    assert set(state) == recorded.requested_objects()

    names = [dict(props).get(ReadValue.OBJECT_NAME) for props in state.values()]
    assert any(isinstance(name, str) for name in names)
