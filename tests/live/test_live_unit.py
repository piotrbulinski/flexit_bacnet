"""Read-only checks against a real Flexit unit.

Skipped by default (pyproject ignores tests/live). Run with:

    FLEXIT_HOST=192.168.1.50 python -m pytest tests/live -p no:cacheprovider --override-ini addopts=

Optional: FLEXIT_PORT (47808), FLEXIT_DEVICE_ID (2).

Nothing here writes to the unit: only readPropertyMultiple requests are sent.
"""

import asyncio
import os
import time

import pytest

from flexit_bacnet import FlexitBACnet, bacnet, nordic
from flexit_bacnet.bacnet import BACnetClient, DeviceProperty, ObjectType, PropertyError, ReadValue

HOST = os.getenv("FLEXIT_HOST")
PORT = int(os.getenv("FLEXIT_PORT", bacnet.DEFAULT_BACNET_PORT))
DEVICE_ID = int(os.getenv("FLEXIT_DEVICE_ID", 2))

pytestmark = pytest.mark.skipif(not HOST, reason="set FLEXIT_HOST to run against a real unit")


def _device() -> FlexitBACnet:
    return FlexitBACnet(HOST, DEVICE_ID, port=PORT)


def test_identify_and_every_reading():
    async def run():
        device = _device()
        await device.update()
        return device

    device = asyncio.run(run())

    assert device.serial_number, "unit did not report a serial number"
    print(f"\n{device.device_name} {device.model} ({device.serial_number[:6]})")

    for info in FlexitBACnet.readings():
        print(f"  {info.label}: {info.format(getattr(device, info.name))}")


def test_repeated_updates_are_stable():
    async def run():
        device = _device()

        # the first update() also finds moved objects by name (a few more
        # requests, once); only the updates after it are the steady state
        started = time.perf_counter()
        await device.update()
        first = time.perf_counter() - started

        durations = []
        for _ in range(20):
            started = time.perf_counter()
            await device.update()
            durations.append(time.perf_counter() - started)
        return first, durations

    first, durations = asyncio.run(run())

    print(f"\nfirst update(): {first * 1000:.0f} ms")
    print(f"update(): median {sorted(durations)[10] * 1000:.0f} ms, max {max(durations) * 1000:.0f} ms")
    assert first < 10
    assert max(durations) < bacnet.DEFAULT_TIMEOUT


def test_concurrent_updates_on_one_client():
    async def run():
        device = _device()
        await asyncio.gather(*(device.update() for _ in range(15)))

    asyncio.run(run())


def test_segmented_answer():
    # present-value + object-name of every object is ~2.9 kB: the unit segments it
    properties = [
        DeviceProperty(p.object_type, p.instance_id, read_values=[ReadValue.PRESENT_VALUE, ReadValue.OBJECT_NAME])
        for p in nordic.DEVICE_PROPERTIES
    ]

    state = asyncio.run(BACnetClient(HOST, PORT).read_multiple(properties))

    assert len(state) == len(properties)
    names = {
        oid: dict(props)[ReadValue.OBJECT_NAME]
        for oid, props in state.items()
        if not isinstance(dict(props)[ReadValue.OBJECT_NAME], PropertyError)
    }
    assert names[nordic.OUTSIDE_AIR_TEMPERATURE.object_identifier] == "R(1)'TOa"


def test_device_object():
    device = DeviceProperty(ObjectType.DEVICE, DEVICE_ID, read_values=[77, 28, 121, 70, 44, 12, 62, 107, 11])

    state = asyncio.run(BACnetClient(HOST, PORT).read_multiple([device]))
    props = dict(state[(ObjectType.DEVICE, DEVICE_ID)])

    print(f"\nmodel {props[70]}, firmware {props[44]}, application {props[12]}, max-APDU {props[62]}")
    assert props[62] >= 480


def test_room_humidity_is_maximum_of_room_sensors():
    """room_humidity (AI 81) is the highest of the wireless room sensors that report one."""
    async def run():
        device = _device()
        await device.update()
        return device

    device = asyncio.run(run())

    rooms = [h for h in (device.room_1_humidity, device.room_2_humidity, device.room_3_humidity) if h]
    if not rooms:
        assert device.room_humidity is None
    else:
        # the sensors update independently of AI 81, so allow a small drift
        assert device.room_humidity == pytest.approx(max(rooms), abs=2)


def test_every_named_object_resolves_to_its_name():
    """After the first update(), each named object is either at an object with that name or missing."""
    async def run():
        device = _device()
        await device.update()

        named = [
            (constant, p) for constant, p in vars(device._prop_map).items()
            if isinstance(p, DeviceProperty) and p.object_name
        ]
        state = await device.bacnet.read_multiple([p.reading(ReadValue.OBJECT_NAME) for _, p in named])
        return named, state, device.relocated_objects()

    named, state, relocated = asyncio.run(run())
    print("relocated:", relocated)

    wrong = {}
    for constant, p in named:
        actual = dict(state[p.object_identifier])[ReadValue.OBJECT_NAME]
        if not isinstance(actual, PropertyError) and actual != p.object_name:
            wrong[constant] = (p.object_identifier, actual)

    assert wrong == {}
