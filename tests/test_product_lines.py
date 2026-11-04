"""Product-line maps, EcoNordic-only values and the free cooling running state."""

import asyncio

import pytest

from flexit_bacnet import FlexitBACnet, econordic, nordic
from flexit_bacnet.bacnet import DeviceProperty, ObjectType, PropertyError, ReadValue, _parse_read_property_multiple_response

from conftest import load_recorded

UNKNOWN_OBJECT = PropertyError(1, 31)


def _objects(module) -> set:
    return {
        name for name, value in vars(module).items()
        if name.isupper() and (isinstance(value, DeviceProperty) or value is None)
    }


def test_product_line_maps_declare_the_same_objects():
    # getters use self._prop_map.<NAME> for both product lines; an object a
    # product line lacks must be declared as None there, not left out
    assert _objects(nordic) == _objects(econordic)


class _Client:
    """Fake BACnetClient: answers with the given values, unknown-object for the rest."""

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


def _nordic(values=None):
    return _device("800220-000000", values or {})


def _econordic(values=None):
    # 80048x is the EcoNordic WH4 serial prefix
    return _device("800481-000000", values or {})


ECONORDIC_ONLY = [
    "dhw_operation_mode",
    "dhw_state",
    "dhw_temperature_setpoint_comfort",
    "dhw_temperature_setpoint_economy",
    "dhw_tank_temperature_top",
    "dhw_tank_temperature_middle",
    "dhw_tank_temperature_bottom",
    "dhw_electric_heater_status",
    "space_heating_setpoint",
    "heat_pump_state",
]


def test_econordic_fixture_serial_is_econordic():
    assert _econordic().product_line == econordic.PRODUCT_LINE
    assert _nordic().product_line == nordic.PRODUCT_LINE


@pytest.mark.parametrize("getter", ECONORDIC_ONLY)
def test_econordic_only_values_are_none_on_nordic(getter):
    assert getattr(_nordic(), getter) is None


@pytest.mark.parametrize(
    "setter, args",
    [
        ("set_dhw_operation_mode", (1,)),
        ("dhw_temporary_boost_start", ()),
        ("dhw_temporary_boost_stop", ()),
        ("dhw_forced_charge_start", ()),
        ("set_dhw_temperature_setpoint_comfort", (55.0,)),
        ("set_dhw_temperature_setpoint_economy", (45.0,)),
        ("set_space_heating_setpoint", (21.0,)),
    ],
)
def test_econordic_only_setters_raise_on_nordic_without_writing(setter, args):
    device = _nordic()

    async def no_write(*_):
        raise AssertionError("must not write to the unit")

    device.bacnet.write = no_write

    with pytest.raises(Exception, match="not available on Nordic models"):
        asyncio.run(getattr(device, setter)(*args))


def test_econordic_values_follow_the_common_conventions():
    device = _econordic({
        econordic.DHW_TANK_TEMPERATURE_TOP.object_identifier: 52.4400634765625,
        econordic.DHW_STATE.object_identifier: econordic.DHW_STATE_FORCED_CHARGE,
        econordic.DHW_ELECTRIC_HEATER_STATUS.object_identifier: 33.0,
        econordic.HEAT_PUMP_STATE.object_identifier: econordic.HEAT_PUMP_STATE_NORMAL_OPERATION,
    })

    # temperatures rounded like the other temperature sensors
    assert device.dhw_tank_temperature_top == 52.4
    assert device.dhw_state == econordic.DHW_STATE_FORCED_CHARGE
    assert device.dhw_electric_heater_status == 33
    assert device.heat_pump_state == econordic.HEAT_PUMP_STATE_NORMAL_OPERATION
    # missing on the unit -> None, like any other getter
    assert device.dhw_tank_temperature_bottom is None


def test_recorded_plant_operating_mode_states_match_constants():
    recorded = load_recorded("nordic_cl4_rer", "plant_operating_mode")
    state = _parse_read_property_multiple_response(recorded.response)

    present = dict(state[nordic.PRESENT_PLANT_OPERATING_MODE.object_identifier])
    assert present[ReadValue.OBJECT_NAME] == "R(1)'HVAC'PrPltOpMod"
    state_text = present[110]

    constants = {
        name: value for name, value in vars(nordic).items()
        if name.startswith("PLANT_OPERATING_MODE_")
    }
    assert len(constants) == present[74] == len(state_text) == 17
    assert state_text[nordic.PLANT_OPERATING_MODE_FREE_COOLING - 1] == "Free cooling"
    assert state_text[nordic.PLANT_OPERATING_MODE_COMFORT - 1] == "Comfort"
    assert state_text[nordic.PLANT_OPERATING_MODE_PURGE - 1] == "Purge"

    # this unit has no plant state object
    assert dict(state[nordic.PLANT_STATE.object_identifier])[ReadValue.OBJECT_NAME] == UNKNOWN_OBJECT


def test_free_cooling_active_from_plant_operating_mode_when_plant_state_missing():
    mode = nordic.PRESENT_PLANT_OPERATING_MODE.object_identifier

    running = _nordic({mode: nordic.PLANT_OPERATING_MODE_FREE_COOLING})
    assert running.plant_state is None
    assert running.plant_operating_mode == nordic.PLANT_OPERATING_MODE_FREE_COOLING
    assert running.free_cooling_active is True

    assert _nordic({mode: nordic.PLANT_OPERATING_MODE_PRE_COMFORT}).free_cooling_active is False


def test_free_cooling_active_prefers_plant_state():
    device = _nordic({
        nordic.PLANT_STATE.object_identifier: nordic.PLANT_STATE_FREE_COOLING,
        nordic.PRESENT_PLANT_OPERATING_MODE.object_identifier: nordic.PLANT_OPERATING_MODE_COMFORT,
    })

    assert device.free_cooling_active is True


def test_free_cooling_active_unknown_without_either_object():
    assert _nordic().free_cooling_active is None
    # EcoNordic has no plant operating mode mapping; without plant state it is unknown
    assert _econordic().free_cooling_active is None
    assert _econordic({
        econordic.PLANT_STATE.object_identifier: econordic.PLANT_STATE_FREE_COOLING,
    }).free_cooling_active is True
