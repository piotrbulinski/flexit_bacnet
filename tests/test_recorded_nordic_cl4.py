"""Decode answers recorded from a real Nordic CL4 RER.

Unit: serial prefix 800220, Siemens POS3.67, firmware 03.39.03.30,
application HvacFnct21y_A v2.425, Max_APDU_Length_Accepted 1024.
"""

import asyncio

import pytest

from flexit_bacnet import FlexitBACnet, bacnet, nordic
from flexit_bacnet.bacnet import (
    BitString,
    DecodingError,
    ObjectType,
    PropertyError,
    ReadValue,
    _parse_read_property_multiple_response,
)

UNKNOWN_OBJECT = PropertyError(1, 31)
UNKNOWN_PROPERTY = PropertyError(2, 32)

# objects nordic.py reads that this unit (application v2.425) does not have
MISSING_ON_CL4 = {
    "EXTRACT_AIR_TEMPERATURE_ALT": (ObjectType.ANALOG_INPUT, 95),
    "EXTRACT_AIR_HUMIDITY": (ObjectType.ANALOG_INPUT, 96),
    "DEHUMIDIFICATION_PID_CONTROL": (ObjectType.BINARY_VALUE, 591),
    "DEHUMIDIFICATION_SLOPE_CONTROL": (ObjectType.MULTI_STATE_VALUE, 620),
    "DEHUMIDIFICATION_BY_SLOPE": (ObjectType.BINARY_VALUE, 653),
    "DEHUMIDIFICATION_SLOPE_ON_DELAY": (ObjectType.POSITIVE_INTEGER_VALUE, 1229),
}


class _ReplayClient:
    """Fake BACnetClient answering every read with a recorded datagram."""

    def __init__(self, response: bytes):
        self.response = response

    async def read_multiple(self, device_properties):
        return _parse_read_property_multiple_response(self.response)


def _device(response: bytes) -> FlexitBACnet:
    device = FlexitBACnet("127.0.0.1", 2)
    device.bacnet = _ReplayClient(response)
    asyncio.run(device.update())
    return device


def test_update_answer_decodes(cl4):
    recorded = cl4("update")
    state = _parse_read_property_multiple_response(recorded.response)

    # every requested object is in the answer
    assert len(state) == len(nordic.DEVICE_PROPERTIES) + 1

    errors = {
        oid for oid, props in state.items()
        if any(isinstance(value, PropertyError) for _, value in props)
    }
    assert errors == set(MISSING_ON_CL4.values())


def test_update_answer_fits_one_apdu(cl4):
    # 994 octets: 30 octets short of the 1024 octet max-APDU. Any additional
    # object in nordic.py makes this unit segment the answer.
    recorded = cl4("update")
    assert len(recorded.response) == 994
    assert not recorded.response[6] & bacnet.PDUFlags.SEGMENTED_REQUEST


def test_getters_on_recorded_unit(cl4):
    device = _device(cl4("update").response)

    assert device.device_name == "Flexit Nordic"
    assert device.serial_number == "800220-000000"
    assert device.model == "CL4 RER"

    assert device.outside_air_temperature == 7.9
    assert device.supply_air_temperature == 16.5
    assert device.extract_air_temperature == 21.5
    assert device.room_temperature == 21.5
    assert device.supply_air_fan_rpm == 4080
    assert device.heat_exchanger_efficiency == 49
    assert device.operation_mode == nordic.OPERATION_MODE_HOME
    assert device.comfort_button is True
    assert device.fireplace_ventilation_status is False
    assert device.air_filter_exchange_interval == 4380.0

    # float32 0.8 must not leak out as 0.800000011920929
    assert device.electric_heater_nominal_power == 0.8
    assert device.electric_heater_power == 0.0


@pytest.mark.parametrize(
    "getter",
    [
        "extract_air_humidity",
        "dehumidification_pid_control",
        "dehumidification_slope_control",
        "dehumidification_by_slope",
        "dehumidification_slope_on_delay",
    ],
)
def test_objects_missing_on_cl4_are_none(cl4, getter):
    assert getattr(_device(cl4("update").response), getter) is None


def test_every_reading_works_on_recorded_unit(cl4):
    device = _device(cl4("update").response)

    for info in FlexitBACnet.readings():
        getattr(device, info.name)


def test_segmented_answer_reassembles_to_every_object(cl4):
    recorded = cl4("segmented_present_value_and_name")
    assert len(recorded.responses) == 3

    assembler = bacnet._SegmentAssembler()
    complete = None
    for datagram in recorded.responses:
        _, complete = assembler.add(datagram, bacnet._apdu_from_response(datagram))

    state = _parse_read_property_multiple_response(complete)

    assert len(state) == len(nordic.DEVICE_PROPERTIES)
    assert dict(state[nordic.OUTSIDE_AIR_TEMPERATURE.object_identifier])[ReadValue.OBJECT_NAME] == "R(1)'TOa"
    assert dict(state[nordic.DEHUMIDIFICATION_MAX_RUNTIME.object_identifier])[ReadValue.OBJECT_NAME] == (
        "R(1)'RHvacCoo'DhuCtl'DhuMaxRunTi"
    )
    assert dict(state[nordic.EXTRACT_AIR_HUMIDITY.object_identifier])[ReadValue.OBJECT_NAME] == UNKNOWN_OBJECT


def test_single_segment_is_rejected_cleanly(cl4):
    with pytest.raises(DecodingError):
        _parse_read_property_multiple_response(cl4("segmented_present_value_and_name").responses[0])


def test_device_object_properties(cl4):
    state = _parse_read_property_multiple_response(cl4("device_object").response)
    props = dict(state[(ObjectType.DEVICE, 2)])

    assert props[ReadValue.OBJECT_NAME] == "HvacFnct21y_A"
    assert props[ReadValue.DESCRIPTION] == "800220-000000"
    # properties the library has no name for are kept under their number
    assert props[121] == "Siemens Building Technologies"  # vendor-name
    assert props[70] == "POS3.67"  # model-name
    assert props[62] == 1024  # max-apdu-length-accepted, two octet unsigned
    assert props[107] == 0  # segmentation-supported: both
    assert props[11] == 6000  # apdu-timeout


def test_reliability_bit_string_and_boolean(cl4):
    state = _parse_read_property_multiple_response(cl4("reliability_status_flags").response)

    sensor_3 = dict(state[(ObjectType.ANALOG_INPUT, 90)])
    assert sensor_3[103] == 7  # reliability: unreliable-other
    assert sensor_3[111] == BitString((False, True, False, False))  # status-flags: fault
    assert sensor_3[81] is False  # out-of-service
    assert sensor_3[117] == 98  # units: percent

    sensor_1 = dict(state[(ObjectType.ANALOG_INPUT, 84)])
    assert sensor_1[111] == BitString((False, False, False, False))

    # binary objects have no units property
    assert dict(state[(ObjectType.BINARY_VALUE, 588)])[117] == UNKNOWN_PROPERTY


def test_object_types_without_enum_member(cl4):
    state = _parse_read_property_multiple_response(cl4("unusual_object_types").response)
    types = {object_type for object_type, _ in state}

    # binary input/output, schedule, structured view and Siemens' proprietary type 264
    assert {3, 4, 17, 29, 264} <= types
    assert all(isinstance(t, int) for t in types)


def test_wrong_device_instance(cl4):
    state = _parse_read_property_multiple_response(cl4("wrong_device_instance").response)

    assert dict(state[(ObjectType.DEVICE, 3)])[ReadValue.OBJECT_NAME] == UNKNOWN_OBJECT


def test_two_octet_property_identifier(cl4):
    state = _parse_read_property_multiple_response(cl4("unknown_property").response)
    props = dict(state[nordic.AIR_TEMP_SETPOINT_AWAY.object_identifier])

    assert props[ReadValue.PRESENT_VALUE] == 16.0
    assert props[672] == UNKNOWN_PROPERTY


@pytest.mark.parametrize(
    "name",
    [
        "abort_buffer_overflow",
        "abort_out_of_resources",
        "abort_segmentation_not_supported",
        "error_pdu_read_property",
    ],
)
def test_error_answers_raise_decoding_error(cl4, name):
    with pytest.raises(DecodingError):
        _parse_read_property_multiple_response(cl4(name).response)


@pytest.mark.parametrize("cut", [1, 5, 6, 7, 9, 20, 500, 993])
def test_truncated_answer_raises_decoding_error(cl4, cut):
    response = cl4("update").response[:cut]

    with pytest.raises(DecodingError):
        _parse_read_property_multiple_response(response)


# (cut 9 would leave a well-formed ComplexACK header with an empty result list)
@pytest.mark.parametrize("cut", [1, 5, 6, 7, 8, 10, 20, 500, 993])
def test_truncated_answer_with_fixed_length_header_raises_decoding_error(cl4, cut):
    # a datagram cut short by the network, but whose BVLC length field was fixed
    # up, must still fail as DecodingError rather than IndexError/struct.error
    response = bytearray(cl4("update").response[:cut])
    if len(response) >= 4:
        response[2:4] = len(response).to_bytes(2, "big")

    with pytest.raises(DecodingError):
        _parse_read_property_multiple_response(bytes(response))


def _all_recorded_datagrams():
    from conftest import FIXTURES, Recorded

    for path in sorted((FIXTURES / "nordic_cl4_rer").glob("*.json")):
        for index, datagram in enumerate(Recorded(path).responses):
            yield pytest.param(datagram, id=f"{path.stem}[{index}]")


def _parse_or_decoding_error(datagram: bytes):
    try:
        result = _parse_read_property_multiple_response(datagram)
    except DecodingError:
        return
    assert isinstance(result, dict)


@pytest.mark.parametrize("datagram", list(_all_recorded_datagrams()))
def test_every_truncation_fails_cleanly(datagram):
    for cut in range(len(datagram)):
        response = bytearray(datagram[:cut])
        if len(response) >= 4:
            response[2:4] = len(response).to_bytes(2, "big")
        _parse_or_decoding_error(bytes(response))


@pytest.mark.parametrize("datagram", list(_all_recorded_datagrams()))
def test_corrupted_bytes_fail_cleanly(datagram):
    import random

    rng = random.Random(datagram[:16])
    for _ in range(300):
        response = bytearray(datagram)
        for _ in range(rng.randint(1, 4)):
            response[rng.randrange(4, len(response))] = rng.randrange(256)
        _parse_or_decoding_error(bytes(response))
