from typing import Any

from flexit_bacnet import bacnet
from flexit_bacnet.device_property import PRESENT_VALUE
from flexit_bacnet.nordic import *
from flexit_bacnet.typing import DeviceState


class FlexitBACnet:
    def __init__(self, device_address: str, device_id: int):
        self.device_address = device_address
        self.device_id = device_id
        self._state: DeviceState | None = None

    def is_valid(self) -> bool:
        """Return True if device address and device ID point to a valid BACnet peer."""
        try:
            return self.serial_number is not None
        except ConnectionError:
            return False

    @property
    def _device_property(self) -> DeviceProperty:
        return DeviceProperty('device', self.device_id, read_values=['objectName', 'description'])

    def refresh(self):
        """Refresh local device state."""
        device_properties = DEVICE_PROPERTIES + [self._device_property]

        self._state = bacnet.read_multiple(self.device_address, device_properties)

    def _get_value(self, device_property: DeviceProperty, value_name: str | None = None) -> Any:
        if self._state is None:
            self.refresh()

        if value_name is None:
            value_name = PRESENT_VALUE

        return dict(self._state[device_property.object_identifier])[value_name]

    def _set_value(self, device_property: DeviceProperty, value: Any):
        bacnet.write(self.device_address, device_property, value)
        self.refresh()

    @property
    def device_name(self) -> str:
        """Return device name, e.g.: HvacFnct21y_A."""
        return self._get_value(self._device_property, 'objectName')

    @property
    def serial_number(self) -> str:
        """Return device's serial number, e.g.: 800220-000000."""
        return self._get_value(self._device_property, 'description')

    @property
    def outside_air_temperature(self) -> float:
        """Outside air temperature in degrees Celsius, e.g. 14.3."""
        return round(self._get_value(OUTSIDE_AIR_TEMPERATURE), 1)

    @property
    def supply_air_temperature(self) -> float:
        """Supply air temperature in degrees Celsius, e.g. 18.9."""
        return round(self._get_value(SUPPLY_AIR_TEMPERATURE), 1)

    @property
    def exhaust_air_temperature(self) -> float:
        """Exhaust air temperature in degrees Celsius, e.g. 14.5."""
        return round(self._get_value(EXHAUST_AIR_TEMPERATURE), 1)

    @property
    def extract_air_temperature(self) -> float:
        """Extract air temperature in degrees Celsius, e.g. 14.3."""
        return round(self._get_value(EXTRACT_AIR_TEMPERATURE), 1)

    @property
    def room_temperature(self) -> float:
        """Room temperature in degrees Celsius, e.g. 14.3.

        Temperature is read from the temperature sensor on a CI70 panel.
        """
        return round(self._get_value(ROOM_TEMPERATURE), 1)

    @property
    def comfort_button(self) -> str:
        """Comfort button state, e.g. active."""
        return self._get_value(COMFORT_BUTTON)

    def activate_comfort_button(self):
        """Activate comfort button."""
        self._set_value(COMFORT_BUTTON, COMFORT_BUTTON.ACTIVE)

    def deactivate_comfort_button(self, delay: int = 0):
        """Deactivate comfort button with optional delay (in minutes)."""
        if delay < 0 or delay > 600:
            raise ValueError('delay must be between 0 and 600 minutes')

        self._set_value(COMFORT_BUTTON_DELAY, delay)
        self._set_value(COMFORT_BUTTON, COMFORT_BUTTON.INACTIVE)

    @property
    def operation_mode(self) -> str:
        """Returns current heat exchanger operation mode, e.g. Home."""
        return OPERATION_MODES[self._get_value(OPERATION_MODE)]

    @property
    def ventilation_mode(self) -> str:
        """Returns current ventilation mode, e.g. Home.

        This setting only works when comfort_button is active.
        When inactive, this will always return "Away".
        """
        return VENTILATION_MODES[self._get_value(VENTILATION_MODE)]

    def set_ventilation_mode(self, mode: int):
        """Set ventilation mode to one of the supported values:
         1 - Stop (VENTILATION_MODE.STOP)
         2 - Away (VENTILATION_MODE.AWAY)
         3 - Home (VENTILATION_MODE.HOME)
         4 - High (VENTILATION_MODE.HIGH)
        """
        self._set_value(VENTILATION_MODE, mode)

    @property
    def air_temp_setpoint_away(self) -> float:
        """Return temperature setpoint for Away mode."""
        return self._get_value(AIR_TEMP_SETPOINT_AWAY)

    def set_air_temp_setpoint_away(self, temperature: float):
        """Set temperature setpoint for Away mode.

        temperature -- temperature in degrees Celsius
        """
        self._set_value(AIR_TEMP_SETPOINT_AWAY, temperature)

    @property
    def air_temp_setpoint_home(self) -> float:
        """Return temperature setpoint for Home mode."""
        return self._get_value(AIR_TEMP_SETPOINT_HOME)

    def set_air_temp_setpoint_home(self, temperature: float):
        """Set temperature setpoint for Home mode.

        temperature -- temperature in degrees Celsius
        """
        self._set_value(AIR_TEMP_SETPOINT_HOME, temperature)

    def start_fireplace_ventilation(self, minutes: int):
        """Trigger temporary fireplace ventilation mode.

        minutes -- duration of fireplace ventilation in minutes (1 - 360)
        """
        self._set_value(FIREPLACE_VENTILATION_RUNTIME, minutes)
        self._set_value(FIREPLACE_VENTILATION, FIREPLACE_VENTILATION.TRIGGER)

    @property
    def fireplace_ventilation_remaining_duration(self) -> int:
        """Return remaining duration (in minutes) of fireplace ventilation mode."""
        return self._get_value(FIREPLACE_VENTILATION_REMAINING_DURATION)

    def start_rapid_ventilation(self, minutes: int):
        """Trigger temporary rapid ventilation mode.

        minutes -- duration of rapid ventilation in minutes (1 - 360)
        """
        self._set_value(RAPID_VENTILATION_RUNTIME, minutes)
        self._set_value(RAPID_VENTILATION, RAPID_VENTILATION.TRIGGER)

    @property
    def rapid_ventilation_remaining_duration(self) -> int:
        """Return remaining duration (in minutes) of fireplace ventilation mode."""
        return self._get_value(RAPID_VENTILATION_REMAINING_DURATION)

    @property
    def supply_air_fan_control_signal(self) -> int:
        """Return current supply air fan control signal (in %)."""
        return int(self._get_value(FAN_SPEED_SUPPLY_AIR))

    @property
    def supply_air_fan_rpm(self) -> int:
        """Return current supply air fan RPM."""
        return int(self._get_value(TACHO_SUPPLY_FAN))

    @property
    def exhaust_air_fan_control_signal(self) -> int:
        """Return current exhaust air fan control signal (in %)."""
        return int(self._get_value(FAN_SPEED_EXHAUST_AIR))

    @property
    def exhaust_air_fan_rpm(self) -> int:
        """Return current exhaust air fan RPM."""
        return int(self._get_value(TACHO_EXHAUST_FAN))

    @property
    def electric_heater(self) -> bool:
        """Return True if electric heater is enabled."""
        return self._get_value(ELECTRICAL_HEATER) == ELECTRICAL_HEATER.ACTIVE

    def enable_electric_heater(self):
        """Enables electric air heater."""
        self._set_value(ELECTRICAL_HEATER, ELECTRICAL_HEATER.ACTIVE)

    def disable_electric_heater(self):
        """Disables electric air heater."""
        self._set_value(ELECTRICAL_HEATER, ELECTRICAL_HEATER.INACTIVE)

    @property
    def electric_heater_nominal_power(self) -> float:
        """Return nominal heater power in kilowatts."""
        return self._get_value(ELECTRIC_HEATER_NOM_POWER)

    @property
    def electric_heater_power(self) -> float:
        """Return heater power consumption in kilowatts."""
        return self._get_value(HEATING_COIL_ELECTRIC_POWER)

    def activate_cooker_hood(self):
        """Activates cooker hood mode."""
        self._set_value(COOKER_HOOD, COOKER_HOOD.ACTIVE)

    def deactivate_cooker_hood(self):
        """Deactivates cooker hood mode."""
        self._set_value(COOKER_HOOD, COOKER_HOOD.INACTIVE)

    @property
    def fan_setpoint_supply_air_home(self) -> int:
        """Return fan setpoint for supply air HOME in percent."""
        return int(self._get_value(LINEAR_SETPOINT_SUPPLY_AIR_HOME))

    def set_fan_setpoint_supply_air_home(self, percent: int):
        """Set fan setpoint for supply air HOME in percent."""
        self._set_value(LINEAR_SETPOINT_SUPPLY_AIR_HOME, percent)

    @property
    def fan_setpoint_extract_air_home(self) -> int:
        """Return fan setpoint for extract air HOME in percent."""
        return int(self._get_value(LINEAR_SETPOINT_EXHAUST_AIR_HOME))

    def set_fan_setpoint_extract_air_home(self, percent: int):
        """Set fan setpoint for extract air HOME in percent."""
        self._set_value(LINEAR_SETPOINT_EXHAUST_AIR_HOME, percent)

    @property
    def fan_setpoint_supply_air_high(self) -> int:
        """Return fan setpoint for supply air HIGH in percent."""
        return int(self._get_value(LINEAR_SETPOINT_SUPPLY_AIR_HIGH))

    def set_fan_setpoint_supply_air_high(self, percent: int):
        """Set fan setpoint for supply air HIGH in percent."""
        self._set_value(LINEAR_SETPOINT_SUPPLY_AIR_HIGH, percent)

    @property
    def fan_setpoint_extract_air_high(self) -> int:
        """Return fan setpoint for extract air HIGH in percent."""
        return int(self._get_value(LINEAR_SETPOINT_EXHAUST_AIR_HIGH))

    def set_fan_setpoint_extract_air_high(self, percent: int):
        """Set fan setpoint for extract air HIGH in percent."""
        self._set_value(LINEAR_SETPOINT_EXHAUST_AIR_HIGH, percent)

    @property
    def fan_setpoint_supply_air_away(self) -> int:
        """Return fan setpoint for supply air AWAY in percent."""
        return int(self._get_value(LINEAR_SETPOINT_SUPPLY_AIR_AWAY))

    def set_fan_setpoint_supply_air_away(self, percent: int):
        """Set fan setpoint for supply air AWAY in percent."""
        self._set_value(LINEAR_SETPOINT_SUPPLY_AIR_AWAY, percent)

    @property
    def fan_setpoint_extract_air_away(self) -> int:
        """Return fan setpoint for extract air AWAY in percent."""
        return int(self._get_value(LINEAR_SETPOINT_EXHAUST_AIR_AWAY))

    def set_fan_setpoint_extract_air_away(self, percent: int):
        """Set fan setpoint for extract air AWAY in percent."""
        self._set_value(LINEAR_SETPOINT_EXHAUST_AIR_AWAY, percent)

    @property
    def fan_setpoint_supply_air_cooker(self) -> int:
        """Return fan setpoint for supply air COOKER in percent."""
        return int(self._get_value(LINEAR_SETPOINT_SUPPLY_AIR_COOKER))

    def set_fan_setpoint_supply_air_cooker(self, percent: int):
        """Set fan setpoint for supply air COOKER in percent."""
        self._set_value(LINEAR_SETPOINT_SUPPLY_AIR_COOKER, percent)

    @property
    def fan_setpoint_extract_air_cooker(self) -> int:
        """Return fan setpoint for extract air COOKER in percent."""
        return int(self._get_value(LINEAR_SETPOINT_EXHAUST_AIR_COOKER))

    def set_fan_setpoint_extract_air_cooker(self, percent: int):
        """Set fan setpoint for extract air COOKER in percent."""
        self._set_value(LINEAR_SETPOINT_EXHAUST_AIR_COOKER, percent)

    @property
    def fan_setpoint_supply_air_fire(self) -> int:
        """Return fan setpoint for supply air FIRE in percent."""
        return int(self._get_value(LINEAR_SETPOINT_SUPPLY_AIR_FIRE))

    def set_fan_setpoint_supply_air_fire(self, percent: int):
        """Set fan setpoint for supply air FIRE in percent."""
        self._set_value(LINEAR_SETPOINT_SUPPLY_AIR_FIRE, percent)

    @property
    def fan_setpoint_extract_air_fire(self) -> int:
        """Return fan setpoint for extract air FIRE in percent."""
        return int(self._get_value(LINEAR_SETPOINT_EXHAUST_AIR_FIRE))

    def set_fan_setpoint_extract_air_fire(self, percent: int):
        """Set fan setpoint for extract air FIRE in percent."""
        self._set_value(LINEAR_SETPOINT_EXHAUST_AIR_FIRE, percent)

    @property
    def air_filter_operating_time(self) -> float:
        """Return air filter operating time in hours."""
        return self._get_value(AIR_FILTER_OPERATING_TIME)

    @property
    def air_filter_exchange_interval(self) -> float:
        return self._get_value(AIR_FILTER_TIME_PERIOD_FOR_EXCHANGE)

    @property
    def heat_exchanger_efficiency(self) -> int:
        """Returns heat exchanger efficiency in percent."""
        return round(self._get_value(ROTATING_HEAT_EXCHANGER_EFFICIENCY))

    @property
    def heat_exchanger_speed(self) -> int:
        """Returns heat exchanger speed in percent."""
        return round(self._get_value(ROTATING_HEAT_EXCHANGER_SPEED))

    @property
    def air_filter_polluted(self) -> bool:
        """Returns True if filter is polluted."""
        return self._get_value(AIR_FILTER_POLLUTED) == AIR_FILTER_POLLUTED.ACTIVE

    def reset_air_filter_timer(self):
        """Resets air filter replace timer."""
        self._set_value(AIR_FILTER_REPLACE_TIMER_RESET, AIR_FILTER_REPLACE_TIMER_RESET.TRIGGER)
