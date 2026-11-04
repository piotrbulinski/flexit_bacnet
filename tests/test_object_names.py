"""Objects are found by name when they are not where the mapping expects them (issue #19 and alike)."""

import asyncio

import pytest

from flexit_bacnet import FlexitBACnet, econordic, nordic
from flexit_bacnet.bacnet import BACnetError, DeviceProperty, ObjectType, PropertyError, ReadValue

UNKNOWN_OBJECT = PropertyError(1, 31)

AI = ObjectType.ANALOG_INPUT
MSV = ObjectType.MULTI_STATE_VALUE

FILTER_RESET = "R(1)'HVAC'AlmBdl'FilRpcRst"
ALARM_STATUS = "R(1)'AlmHdl'Alm2019'AlmSta"


class FakeUnit:
    """A unit with the given objects: answers object-name, present-value and the device's object-list."""

    def __init__(self, serial: str, objects: dict, object_list_error: bool = False):
        self.serial = serial
        self.objects = objects  # identifier -> (name, present value)
        self.object_list_error = object_list_error
        self.requests = []
        self.writes = []

    async def read_multiple(self, device_properties):
        self.requests.append([(p.object_identifier, tuple(p.read_values)) for p in device_properties])
        state = {}

        for p in device_properties:
            if p.object_type == ObjectType.DEVICE:
                if ReadValue.OBJECT_LIST in p.read_values and self.object_list_error:
                    raise BACnetError("abort", "segmentation-not-supported")

                answers = {
                    ReadValue.OBJECT_NAME: "HvacFnct21y_A",
                    ReadValue.DESCRIPTION: self.serial,
                    ReadValue.OBJECT_LIST: [p.object_identifier] + list(self.objects),
                }
            else:
                name, value = self.objects.get(p.object_identifier, (UNKNOWN_OBJECT, UNKNOWN_OBJECT))
                answers = {ReadValue.OBJECT_NAME: name, ReadValue.PRESENT_VALUE: value}

            state[p.object_identifier] = [(rv, answers[rv]) for rv in p.read_values]

        return state

    async def write(self, device_property, value):
        self.writes.append((device_property.object_identifier, value))

    def name_scan_types(self):
        """Object types whose names were read after the object-list (the search)."""
        types = set()
        searching = False
        for request in self.requests:
            if any(read_values == (ReadValue.OBJECT_LIST,) for _, read_values in request):
                searching = True
                continue
            if searching:
                types |= {identifier[0] for identifier, read_values in request if read_values == (ReadValue.OBJECT_NAME,)}
        return types

    def read_object_list(self):
        return any(read_values == (ReadValue.OBJECT_LIST,) for request in self.requests for _, read_values in request)


def _all_named(module, value=1):
    """Every named object of the mapping, at its expected identifier."""
    return {
        p.object_identifier: (p.object_name, value)
        for p in vars(module).values()
        if isinstance(p, DeviceProperty) and p.object_name
    }


def _cl4():
    # objects a Nordic CL4 RER (application v2.425) does not have
    objects = _all_named(nordic)
    for identifier in [(AI, 96), (MSV, 620), (MSV, 623)]:
        del objects[identifier]
    objects[(MSV, 609)] = (ALARM_STATUS, 1)
    return FakeUnit("800220-000000", objects)


def _s3():
    # Nordic S3 REL dump: extract air temperature and filter reset are elsewhere
    objects = _all_named(nordic)
    del objects[(AI, 59)]
    del objects[(MSV, 613)]
    objects[(AI, 95)] = ("R(1)'TEx", 21.4)
    objects[(MSV, 609)] = (FILTER_RESET, 1)
    objects[(MSV, 622)] = (ALARM_STATUS, 1)
    return FakeUnit("800121-000000", objects)


def _device(unit) -> FlexitBACnet:
    device = FlexitBACnet("127.0.0.1", 2)
    device.bacnet = unit
    asyncio.run(device.update())
    return device


def _reset(device):
    asyncio.run(device.reset_air_filter_timer())
    return device.bacnet.writes


def test_unit_matching_the_mapping_is_not_searched():
    unit = FakeUnit("800220-000000", _all_named(nordic))
    device = _device(unit)

    assert device.relocated_objects() == {}
    assert not unit.read_object_list()


def test_s3_objects_are_found_by_name():
    device = _device(_s3())

    assert device.relocated_objects() == {
        "EXTRACT_AIR_TEMPERATURE": ((AI, 59), (AI, 95)),
        "AIR_FILTER_REPLACE_TIMER_RESET": ((MSV, 613), (MSV, 609)),
    }
    assert device.extract_air_temperature == 21.4


def test_s3_filter_reset_writes_to_609():
    assert _reset(_device(_s3())) == [((MSV, 609), nordic.AIR_FILTER_REPLACE_TIMER_RESET_TRIGGER)]


def test_cl4_filter_reset_writes_to_613_not_to_the_alarm_at_609():
    device = _device(_cl4())

    assert "AIR_FILTER_REPLACE_TIMER_RESET" not in device.relocated_objects()
    assert _reset(device) == [((MSV, 613), nordic.AIR_FILTER_REPLACE_TIMER_RESET_TRIGGER)]


def test_econordic_filter_reset_stays_at_609():
    objects = _all_named(econordic)
    unit = FakeUnit("800481-000000", objects)

    assert _reset(_device(unit)) == [((MSV, 609), econordic.AIR_FILTER_REPLACE_TIMER_RESET_TRIGGER)]


def test_object_missing_everywhere_keeps_its_identifier_and_reads_none():
    device = _device(_cl4())

    assert device.relocated_objects() == {}
    assert device._prop_map.EXTRACT_AIR_HUMIDITY.object_identifier == (AI, 96)
    assert device.extract_air_humidity is None


def test_search_reads_only_the_types_of_the_missing_objects():
    unit = _cl4()
    _device(unit)

    # missing on a CL4: AI 96 (extract air humidity), MSV 620 and 623
    assert unit.name_scan_types() == {AI, MSV}


def test_unreadable_object_list_keeps_the_mapping():
    unit = _s3()
    unit.object_list_error = True
    device = _device(unit)

    assert device.relocated_objects() == {}
    assert device._prop_map.AIR_FILTER_REPLACE_TIMER_RESET.object_identifier == (MSV, 613)


def test_moved_objects_are_read_on_every_update():
    unit = _s3()
    device = _device(unit)
    unit.requests.clear()
    asyncio.run(device.update())

    read = {identifier for request in unit.requests for identifier, _ in request}
    assert {(AI, 95), (MSV, 609)} <= read
    assert (MSV, 613) not in read


def test_resolution_does_not_change_the_shared_mapping():
    s3 = _device(_s3())
    cl4 = _device(_cl4())

    assert nordic.AIR_FILTER_REPLACE_TIMER_RESET.object_identifier == (MSV, 613)
    assert s3._prop_map.AIR_FILTER_REPLACE_TIMER_RESET.object_identifier == (MSV, 609)
    assert cl4._prop_map.AIR_FILTER_REPLACE_TIMER_RESET.object_identifier == (MSV, 613)


def test_moved_object_keeps_write_priority_and_name():
    moved = nordic.COMFORT_BUTTON.moved_to(ObjectType.BINARY_VALUE, 51)

    assert moved.object_identifier == (ObjectType.BINARY_VALUE, 51)
    assert moved.priority == nordic.COMFORT_BUTTON.priority == 13
    assert moved.object_name == nordic.COMFORT_BUTTON.object_name


@pytest.mark.parametrize("module", [nordic, econordic])
def test_object_names_are_unique_per_mapping(module):
    # BACnet object names are unique within a device; two constants with one
    # name are only allowed when they are the same object
    seen = {}
    for constant, p in vars(module).items():
        if isinstance(p, DeviceProperty) and p.object_name:
            if p.object_name in seen:
                assert seen[p.object_name] == p.object_identifier, constant
            seen[p.object_name] = p.object_identifier
