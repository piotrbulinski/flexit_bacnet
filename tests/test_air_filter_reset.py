"""The air filter reset object is found by its name, not by the product line (issue #19)."""

import asyncio

import pytest

from flexit_bacnet import FlexitBACnet, econordic, nordic
from flexit_bacnet.bacnet import ObjectType, PropertyError, ReadValue

UNKNOWN_OBJECT = PropertyError(1, 31)
FILTER_RESET_NAME = "R(1)'HVAC'AlmBdl'FilRpcRst"


class _Client:
    """Fake BACnet client: answers object names from `names`, unknown-object for the rest."""

    def __init__(self, serial: str, names: dict):
        self.serial = serial
        self.names = names
        self.writes = []

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
                    (value, self.names.get(p.instance_id, UNKNOWN_OBJECT) if value == ReadValue.OBJECT_NAME
                     else UNKNOWN_OBJECT)
                    for value in p.read_values
                ]
        return state

    async def write(self, device_property, value):
        self.writes.append((device_property.object_identifier, value))


def _reset(serial: str, names: dict):
    device = FlexitBACnet("127.0.0.1", 2)
    device.bacnet = _Client(serial, names)
    asyncio.run(device.update())
    asyncio.run(device.reset_air_filter_timer())

    return device.bacnet.writes


@pytest.mark.parametrize(
    "unit, serial, instance_id",
    [
        # dumps from the issue: the object does not follow the product line
        ("Nordic S3 REL", "800121-000000", 609),
        ("Nordic S4 REL", "800131-000000", 613),
        ("Nordic CL4 RER", "800220-000000", 613),
        ("EcoNordic WH4", "800481-000000", 609),
    ],
)
def test_reset_writes_to_the_object_named_filrpcrst(unit, serial, instance_id):
    writes = _reset(serial, {instance_id: FILTER_RESET_NAME})

    assert writes == [((ObjectType.MULTI_STATE_VALUE, instance_id), nordic.AIR_FILTER_REPLACE_TIMER_RESET_TRIGGER)]


def test_other_object_with_candidate_number_is_ignored():
    # what a real Nordic CL4 RER answered: 609 exists but is an alarm status,
    # so "the first candidate that exists" would write to the wrong object
    writes = _reset("800220-000000", {609: "R(1)'AlmHdl'Alm2019'AlmSta", 613: FILTER_RESET_NAME})

    assert writes[0][0] == (ObjectType.MULTI_STATE_VALUE, 613)


@pytest.mark.parametrize(
    "serial, module",
    [("800220-000000", nordic), ("800481-000000", econordic)],
)
def test_falls_back_to_product_line_default_when_no_name_matches(serial, module):
    writes = _reset(serial, {})

    assert writes == [
        (module.AIR_FILTER_REPLACE_TIMER_RESET.object_identifier, module.AIR_FILTER_REPLACE_TIMER_RESET_TRIGGER)
    ]
