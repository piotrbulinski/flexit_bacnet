from typing import Any, Optional

from flexit_bacnet import bacnet
from flexit_bacnet import econordic, nordic


class FlexitBACnet:
    def __init__(
        self,
        device_address: str,
        device_id: int,
        port: int = bacnet.DEFAULT_BACNET_PORT,
    ) -> None:
        self.bacnet = bacnet.BACnetClient(device_address, port)
        self.device_id = device_id
        self._state: Optional[bacnet.DeviceState] = None

        # property mapping for the specific product line (nordic/econordic)
        self._prop_map: Optional[Any] = None

    @property
    def _device_property(self) -> bacnet.DeviceProperty:
        return bacnet.DeviceProperty(
            bacnet.ObjectType.DEVICE,
            self.device_id,
            read_values=[bacnet.ReadValue.OBJECT_NAME, bacnet.ReadValue.DESCRIPTION],
        )

    async def _get_property_mapping(self) -> Any:
        """
        Return the property mapping module based on the device model ID.

        The model ID is derived from the serial number:
        - If the model exists in econordic.MODELS, the econordic module is returned.
        - If the model exists in nordic.MODELS, the nordic module is returned.
        - Otherwise a ValueError is raised.
        """
        self._state = await self.bacnet.read_multiple([self._device_property])

        model_id = int(self.serial_number[0:6])

        if model_id in econordic.MODELS:
            return econordic

        if model_id in nordic.MODELS:
            return nordic

        raise ValueError(f"Unsupported model id: {model_id}")

    async def update(self) -> None:
        """Refresh local device state."""
        if self._prop_map is None:
            self._prop_map = await self._get_property_mapping()

            # Dynamically add constants from the property map to the device object
            for name in dir(self._prop_map):
                if name.isupper():  # only consider constants (uppercase names)
                    setattr(self, name, getattr(self._prop_map, name))

        device_properties = self._prop_map.DEVICE_PROPERTIES + [self._device_property]

        self._state = await self.bacnet.read_multiple(device_properties)

    def _get_value(
        self,
        device_property: bacnet.DeviceProperty,
        value_name: Optional[bacnet.ReadValue] = None,
    ) -> Any:

        if self._state is None:
            raise Exception("must run 'update()' method first")

        if value_name is None:
            value_name = bacnet.ReadValue.PRESENT_VALUE

        return dict(self._state[device_property.object_identifier])[value_name]

    async def _set_value(self, device_property: bacnet.DeviceProperty, value: Any) -> None:
        await self.bacnet.write(device_property, value)
        await self.update()

    @property
    def product_line(self) -> str:
        """Return product line, e.g.: Nordic or EcoNordic."""
        return self._prop_map.PRODUCT_LINE

    @property
    def device_name(self) -> str:
        """Return device name, e.g.: Flexit Nordic"""
        device_name_from_device = self._get_value(self._device_property, bacnet.ReadValue.OBJECT_NAME)
        device_name = self._prop_map.DEVICE_NAMES.get(device_name_from_device)

        if not isinstance(device_name, str):
            return ''

        return device_name

    @property
    def serial_number(self) -> str:
        """Return device's serial number, e.g.: 800220-000000."""
        serial_number = self._get_value(self._device_property, bacnet.ReadValue.DESCRIPTION)

        if not isinstance(serial_number, str):
            return ''

        return serial_number

    @property
    def model(self) -> str:
        """Return device's model, e.g.: S2 REL."""
        try:
            model_id = int(self.serial_number[0:6])
        except ValueError:
            return ''

        return self._prop_map.MODELS.get(model_id, '')

    @property
    def outside_air_temperature(self) -> float:
        """Outside air temperature in degrees Celsius, e.g. 14.3."""
        return float(round(self._get_value(self._prop_map.OUTSIDE_AIR_TEMPERATURE), 1))

    @property
    def supply_air_temperature(self) -> float:
        """Supply air temperature in degrees Celsius, e.g. 18.9."""
        return float(round(self._get_value(self._prop_map.SUPPLY_AIR_TEMPERATURE), 1))

    @property
    def exhaust_air_temperature(self) -> float:
        """Exhaust air temperature in degrees Celsius, e.g. 14.5."""
        return float(round(self._get_value(self._prop_map.EXHAUST_AIR_TEMPERATURE), 1))

    @property
    def extract_air_temperature(self) -> float:
        """Extract air temperature in degrees Celsius, e.g. 14.3."""
        value = float(round(self._get_value(self._prop_map.EXTRACT_AIR_TEMPERATURE), 1))

        # as some models use different object identifier for extract air temperature
        # we need to check if the value is 0.0 and try to read the alternative value
        if value == 0.0:
            value = float(round(self._get_value(self._prop_map.EXTRACT_AIR_TEMPERATURE_ALT), 1))

        return value

    @property
    def extract_air_humidity(self) -> float:
        """Extract air relative humidity in %, e.g. 40.3."""
        return float(round(self._get_value(self._prop_map.EXTRACT_AIR_HUMIDITY), 1))

    @property
    def room_temperature(self) -> float:
        """Room temperature in degrees Celsius, e.g. 14.3.

        Temperature is read from the temperature sensor on a CI70 panel.
        """
        return float(round(self._get_value(self._prop_map.ROOM_TEMPERATURE), 1))

    @property
    def room_1_humidity(self) -> float:
        """Room 1 relative humidity in %, e.g. 40.3.

        RH value from CI77 - RH sensor 1.
        """
        return float(round(self._get_value(self._prop_map.ROOM_1_HUMIDITY), 1))

    @property
    def room_2_humidity(self) -> float:
        """Room 2 relative humidity in %, e.g. 40.3.

        RH value from CI77 - RH sensor 2.
        """
        return float(round(self._get_value(self._prop_map.ROOM_2_HUMIDITY), 1))

    @property
    def room_3_humidity(self) -> float:
        """Room 3 relative humidity in %, e.g. 40.3.

        RH value from CI77 - RH sensor 3.
        """
        return float(round(self._get_value(self._prop_map.ROOM_3_HUMIDITY), 1))

    @property
    def comfort_button(self) -> bool:
        """Comfort button state, True if active."""
        return self._get_value(self._prop_map.COMFORT_BUTTON) == self._prop_map.COMFORT_BUTTON_ACTIVE

    async def activate_comfort_button(self) -> None:
        """Activate comfort button."""
        await self._set_value(self._prop_map.COMFORT_BUTTON, self._prop_map.COMFORT_BUTTON_ACTIVE)

    async def deactivate_comfort_button(self, delay: int = 0) -> None:
        """Deactivate comfort button with optional delay (in minutes)."""
        if delay < 0 or delay > 600:
            raise ValueError("delay must be between 0 and 600 minutes")

        await self._set_value(self._prop_map.COMFORT_BUTTON_DELAY, delay)
        await self._set_value(self._prop_map.COMFORT_BUTTON, self._prop_map.COMFORT_BUTTON_INACTIVE)

    @property
    def operation_mode(self) -> int:
        """Returns current heat exchanger operation mode, e.g. Home."""
        return self._get_value(self._prop_map.OPERATION_MODE)

    @property
    def ventilation_mode(self) -> int:
        """Returns current ventilation mode, e.g. Home.

        This setting only works when comfort_button is active.
        When inactive, this will always return VENTILATION_MODE_AWAY.
        """
        return self._get_value(self._prop_map.VENTILATION_MODE)

    async def set_ventilation_mode(self, mode: int) -> None:
        """Set ventilation mode to one of the supported values:
        1 - Stop (VENTILATION_MODE_STOP)
        2 - Away (VENTILATION_MODE_AWAY)
        3 - Home (VENTILATION_MODE_HOME)
        4 - High (VENTILATION_MODE_HIGH)
        """
        await self._set_value(self._prop_map.VENTILATION_MODE, mode)

    @property
    def air_temp_setpoint_away(self) -> float:
        """Return temperature setpoint for Away mode."""
        return float(self._get_value(self._prop_map.AIR_TEMP_SETPOINT_AWAY))

    async def set_air_temp_setpoint_away(self, temperature: float):
        """Set temperature setpoint for Away mode.

        temperature -- temperature in degrees Celsius
        """
        await self._set_value(self._prop_map.AIR_TEMP_SETPOINT_AWAY, temperature)

    @property
    def air_temp_setpoint_home(self) -> float:
        """Return temperature setpoint for Home mode."""
        return float(self._get_value(self._prop_map.AIR_TEMP_SETPOINT_HOME))

    async def set_air_temp_setpoint_home(self, temperature: float) -> None:
        """Set temperature setpoint for Home mode.

        temperature -- temperature in degrees Celsius
        """
        await self._set_value(self._prop_map.AIR_TEMP_SETPOINT_HOME, temperature)

    async def start_fireplace_ventilation(self, minutes: int) -> None:
        """Set duration and trigger fireplace ventilation mode.

        minutes -- duration of fireplace ventilation in minutes (1 - 360)
        """
        await self.set_fireplace_mode_runtime(minutes)
        await self.trigger_fireplace_mode()

    async def set_fireplace_mode_runtime(self, minutes: int) -> None:
        """Set runtime duration for the fireplace ventilation mode.

        minutes -- duration of fireplace ventilation in minutes (1 - 360)
        """
        await self._set_value(self._prop_map.FIREPLACE_VENTILATION_RUNTIME, minutes)

    @property
    def fireplace_mode_runtime(self) -> int:
        """Returns currently set runtime for the fireplace mode (in minutes)."""
        return self._get_value(self._prop_map.FIREPLACE_VENTILATION_RUNTIME)

    async def trigger_fireplace_mode(self) -> None:
        """Trigger temporary fireplace ventilation mode."""
        await self._set_value(self._prop_map.FIREPLACE_VENTILATION, self._prop_map.FIREPLACE_VENTILATION_TRIGGER)

    @property
    def fireplace_ventilation_status(self) -> bool:
        """Return true if fireplace mode is active."""
        return self._get_value(self._prop_map.FIREPLACE_STATE) == self._prop_map.FIREPLACE_STATE_ACTIVE

    @property
    def fireplace_ventilation_remaining_duration(self) -> int:
        """Return remaining duration (in minutes) of fireplace ventilation mode."""
        return int(self._get_value(self._prop_map.FIREPLACE_VENTILATION_REMAINING_DURATION))

    async def start_rapid_ventilation(self, minutes: int) -> None:
        """Trigger temporary rapid ventilation mode.

        minutes -- duration of rapid ventilation in minutes (1 - 360)
        """
        await self._set_value(self._prop_map.RAPID_VENTILATION_RUNTIME, minutes)
        await self._set_value(self._prop_map.RAPID_VENTILATION, self._prop_map.RAPID_VENTILATION_TRIGGER)

    @property
    def rapid_ventilation_remaining_duration(self) -> int:
        """Return remaining duration (in minutes) of fireplace ventilation mode."""
        return int(self._get_value(self._prop_map.RAPID_VENTILATION_REMAINING_DURATION))

    @property
    def supply_air_fan_control_signal(self) -> int:
        """Return current supply air fan control signal (in %)."""
        return int(self._get_value(self._prop_map.FAN_SPEED_SUPPLY_AIR))

    @property
    def supply_air_fan_rpm(self) -> int:
        """Return current supply air fan RPM."""
        return int(self._get_value(self._prop_map.TACHO_SUPPLY_FAN))

    @property
    def exhaust_air_fan_control_signal(self) -> int:
        """Return current exhaust air fan control signal (in %)."""
        return int(self._get_value(self._prop_map.FAN_SPEED_EXHAUST_AIR))

    @property
    def exhaust_air_fan_rpm(self) -> int:
        """Return current exhaust air fan RPM."""
        return int(self._get_value(self._prop_map.TACHO_EXHAUST_FAN))

    @property
    def electric_heater(self) -> bool:
        """Return True if electric heater is enabled."""
        return bool(self._get_value(self._prop_map.ELECTRICAL_HEATER) == self._prop_map.ELECTRICAL_HEATER_ACTIVE)

    async def enable_electric_heater(self) -> None:
        """Enables electric air heater."""
        await self._set_value(self._prop_map.ELECTRICAL_HEATER, self._prop_map.ELECTRICAL_HEATER_ACTIVE)

    async def disable_electric_heater(self) -> None:
        """Disables electric air heater."""
        await self._set_value(self._prop_map.ELECTRICAL_HEATER, self._prop_map.ELECTRICAL_HEATER_INACTIVE)

    @property
    def electric_heater_nominal_power(self) -> float:
        """Return nominal heater power in kilowatts."""
        return float(self._get_value(self._prop_map.ELECTRIC_HEATER_NOM_POWER))

    @property
    def electric_heater_power(self) -> float:
        """Return heater power consumption in kilowatts."""
        return float(self._get_value(self._prop_map.HEATING_COIL_ELECTRIC_POWER))

    @property
    def cooker_hood_status(self) -> bool:
        """Cooker hood ventilation state, True if active."""
        return self._get_value(self._prop_map.COOKER_HOOD) == self._prop_map.COOKER_HOOD_ACTIVE

    async def activate_cooker_hood(self) -> None:
        """Activates cooker hood mode."""
        await self._set_value(self._prop_map.COOKER_HOOD, self._prop_map.COOKER_HOOD_ACTIVE)

    async def deactivate_cooker_hood(self) -> None:
        """Deactivates cooker hood mode."""
        await self._set_value(self._prop_map.COOKER_HOOD, self._prop_map.COOKER_HOOD_INACTIVE)

    @property
    def fan_setpoint_supply_air_home(self) -> int:
        """Return fan setpoint for supply air HOME in percent."""
        return int(self._get_value(self._prop_map.LINEAR_SETPOINT_SUPPLY_AIR_HOME))

    async def set_fan_setpoint_supply_air_home(self, percent: int) -> None:
        """Set fan setpoint for supply air HOME in percent."""
        await self._set_value(self._prop_map.LINEAR_SETPOINT_SUPPLY_AIR_HOME, percent)

    @property
    def fan_setpoint_extract_air_home(self) -> int:
        """Return fan setpoint for extract air HOME in percent."""
        return int(self._get_value(self._prop_map.LINEAR_SETPOINT_EXHAUST_AIR_HOME))

    async def set_fan_setpoint_extract_air_home(self, percent: int) -> None:
        """Set fan setpoint for extract air HOME in percent."""
        await self._set_value(self._prop_map.LINEAR_SETPOINT_EXHAUST_AIR_HOME, percent)

    @property
    def fan_setpoint_supply_air_high(self) -> int:
        """Return fan setpoint for supply air HIGH in percent."""
        return int(self._get_value(self._prop_map.LINEAR_SETPOINT_SUPPLY_AIR_HIGH))

    async def set_fan_setpoint_supply_air_high(self, percent: int) -> None:
        """Set fan setpoint for supply air HIGH in percent."""
        await self._set_value(self._prop_map.LINEAR_SETPOINT_SUPPLY_AIR_HIGH, percent)

    @property
    def fan_setpoint_extract_air_high(self) -> int:
        """Return fan setpoint for extract air HIGH in percent."""
        return int(self._get_value(self._prop_map.LINEAR_SETPOINT_EXHAUST_AIR_HIGH))

    async def set_fan_setpoint_extract_air_high(self, percent: int) -> None:
        """Set fan setpoint for extract air HIGH in percent."""
        await self._set_value(self._prop_map.LINEAR_SETPOINT_EXHAUST_AIR_HIGH, percent)

    @property
    def fan_setpoint_supply_air_away(self) -> int:
        """Return fan setpoint for supply air AWAY in percent."""
        return int(self._get_value(self._prop_map.LINEAR_SETPOINT_SUPPLY_AIR_AWAY))

    async def set_fan_setpoint_supply_air_away(self, percent: int) -> None:
        """Set fan setpoint for supply air AWAY in percent."""
        await self._set_value(self._prop_map.LINEAR_SETPOINT_SUPPLY_AIR_AWAY, percent)

    @property
    def fan_setpoint_extract_air_away(self) -> int:
        """Return fan setpoint for extract air AWAY in percent."""
        return int(self._get_value(self._prop_map.LINEAR_SETPOINT_EXHAUST_AIR_AWAY))

    async def set_fan_setpoint_extract_air_away(self, percent: int) -> None:
        """Set fan setpoint for extract air AWAY in percent."""
        await self._set_value(self._prop_map.LINEAR_SETPOINT_EXHAUST_AIR_AWAY, percent)

    @property
    def fan_setpoint_supply_air_cooker(self) -> int:
        """Return fan setpoint for supply air COOKER in percent."""
        return int(self._get_value(self._prop_map.LINEAR_SETPOINT_SUPPLY_AIR_COOKER))

    async def set_fan_setpoint_supply_air_cooker(self, percent: int) -> None:
        """Set fan setpoint for supply air COOKER in percent."""
        await self._set_value(self._prop_map.LINEAR_SETPOINT_SUPPLY_AIR_COOKER, percent)

    @property
    def fan_setpoint_extract_air_cooker(self) -> int:
        """Return fan setpoint for extract air COOKER in percent."""
        return int(self._get_value(self._prop_map.LINEAR_SETPOINT_EXHAUST_AIR_COOKER))

    async def set_fan_setpoint_extract_air_cooker(self, percent: int) -> None:
        """Set fan setpoint for extract air COOKER in percent."""
        await self._set_value(self._prop_map.LINEAR_SETPOINT_EXHAUST_AIR_COOKER, percent)

    @property
    def fan_setpoint_supply_air_fire(self) -> int:
        """Return fan setpoint for supply air FIRE in percent."""
        return int(self._get_value(self._prop_map.LINEAR_SETPOINT_SUPPLY_AIR_FIRE))

    async def set_fan_setpoint_supply_air_fire(self, percent: int):
        """Set fan setpoint for supply air FIRE in percent."""
        await self._set_value(self._prop_map.LINEAR_SETPOINT_SUPPLY_AIR_FIRE, percent)

    @property
    def fan_setpoint_extract_air_fire(self) -> int:
        """Return fan setpoint for extract air FIRE in percent."""
        return int(self._get_value(self._prop_map.LINEAR_SETPOINT_EXHAUST_AIR_FIRE))

    async def set_fan_setpoint_extract_air_fire(self, percent: int) -> None:
        """Set fan setpoint for extract air FIRE in percent."""
        await self._set_value(self._prop_map.LINEAR_SETPOINT_EXHAUST_AIR_FIRE, percent)

    @property
    def air_filter_operating_time(self) -> float:
        """Return air filter operating time in hours."""
        return float(self._get_value(self._prop_map.AIR_FILTER_OPERATING_TIME))

    @property
    def air_filter_exchange_interval(self) -> float:
        """Return air filter exchange interval in hours."""
        return float(self._get_value(self._prop_map.AIR_FILTER_TIME_PERIOD_FOR_EXCHANGE))

    @property
    def heat_exchanger_efficiency(self) -> int:
        """Returns heat exchanger efficiency in percent."""
        return int(round(self._get_value(self._prop_map.ROTATING_HEAT_EXCHANGER_EFFICIENCY)))

    @property
    def heat_exchanger_speed(self) -> int:
        """Returns heat exchanger speed in percent."""
        return int(round(self._get_value(self._prop_map.ROTATING_HEAT_EXCHANGER_SPEED)))

    @property
    def air_filter_polluted(self) -> bool:
        """Returns True if filter is polluted."""
        return bool(self._get_value(self._prop_map.AIR_FILTER_POLLUTED) == self._prop_map.AIR_FILTER_POLLUTED_ACTIVE)

    async def reset_air_filter_timer(self) -> None:
        """Resets air filter replace timer."""
        await self._set_value(
            self._prop_map.AIR_FILTER_REPLACE_TIMER_RESET, self._prop_map.AIR_FILTER_REPLACE_TIMER_RESET_TRIGGER
        )

    @property
    def dhw_operation_mode(self) -> int:
        """Returns current Domestic Hot Water (DHW) operation mode."""

        if self.product_line != econordic.PRODUCT_LINE:
            raise Exception("DHW operation mode is only available on EcoNordic models") 

        return self._get_value(econordic.DHW_OPERATION_MODE)
    
    async def set_dhw_operation_mode(self, mode: int) -> None:
        """Set Domestic Hot Water (DHW) operation mode.

        mode -- one of the supported values:
        1 - Comfort (DHW_OPERATION_MODE_COMFORT)
        2 - Economy (DHW_OPERATION_MODE_ECONOMY)
        """

        if self.product_line != econordic.PRODUCT_LINE:
            raise Exception("DHW operation mode is only available on EcoNordic models")

        await self._set_value(econordic.DHW_OPERATION_MODE, mode)

    async def dhw_temporary_boost_start(self) -> None:
        """Activate Domestic Hot Water (DHW) temporary boost mode."""

        if self.product_line != econordic.PRODUCT_LINE:
            raise Exception("DHW temporary boost is only available on EcoNordic models")

        await self._set_value(econordic.DHW_TEMPORARY_BOOST, econordic.DHW_TEMPORARY_BOOST_START)

    async def dhw_temporary_boost_stop(self) -> None:
        """Deactivate Domestic Hot Water (DHW) temporary boost mode."""

        if self.product_line != econordic.PRODUCT_LINE:
            raise Exception("DHW temporary boost is only available on EcoNordic models")

        await self._set_value(econordic.DHW_TEMPORARY_BOOST, econordic.DHW_TEMPORARY_BOOST_STOP)

    @property
    def dhw_temperature_setpoint_comfort(self) -> float:
        """Return Domestic Hot Water (DHW) temperature setpoint for Comfort mode."""

        if self.product_line != econordic.PRODUCT_LINE:
            raise Exception("DHW temperature setpoint is only available on EcoNordic models")

        return float(self._get_value(econordic.DHW_TEMPERATURE_SETPOINT_COMFORT))

    async def set_dhw_temperature_setpoint_comfort(self, temperature: float) -> None:
        """Set Domestic Hot Water (DHW) temperature setpoint for Comfort mode.

        temperature -- temperature in degrees Celsius
        """

        if self.product_line != econordic.PRODUCT_LINE:
            raise Exception("DHW temperature setpoint is only available on EcoNordic models")

        await self._set_value(econordic.DHW_TEMPERATURE_SETPOINT_COMFORT, temperature)

    @property
    def dhw_temperature_setpoint_economy(self) -> float:
        """Return Domestic Hot Water (DHW) temperature setpoint for Economy mode."""

        if self.product_line != econordic.PRODUCT_LINE:
            raise Exception("DHW temperature setpoint is only available on EcoNordic models")

        return float(self._get_value(econordic.DHW_TEMPERATURE_SETPOINT_ECONOMY))

    async def set_dhw_temperature_setpoint_economy(self, temperature: float) -> None:
        """Set Domestic Hot Water (DHW) temperature setpoint for Economy mode.

        temperature -- temperature in degrees Celsius
        """

        if self.product_line != econordic.PRODUCT_LINE:
            raise Exception("DHW temperature setpoint is only available on EcoNordic models")

        await self._set_value(econordic.DHW_TEMPERATURE_SETPOINT_ECONOMY, temperature)

    @property
    def dhw_tank_temperature_top(self) -> float:
        """Return Domestic Hot Water (DHW) tank top temperature."""

        if self.product_line != econordic.PRODUCT_LINE:
            raise Exception("DHW tank temperature is only available on EcoNordic models")

        return float(self._get_value(econordic.DHW_TANK_TEMPERATURE_TOP))

    @property
    def dhw_tank_temperature_middle(self) -> float:
        """Return Domestic Hot Water (DHW) tank middle temperature."""

        if self.product_line != econordic.PRODUCT_LINE:
            raise Exception("DHW tank temperature is only available on EcoNordic models")

        return float(self._get_value(econordic.DHW_TANK_TEMPERATURE_MIDDLE))

    @property
    def dhw_tank_temperature_bottom(self) -> float:
        """Return Domestic Hot Water (DHW) tank bottom temperature."""

        if self.product_line != econordic.PRODUCT_LINE:
            raise Exception("DHW tank temperature is only available on EcoNordic models")

        return float(self._get_value(econordic.DHW_TANK_TEMPERATURE_BOTTOM))

    @property
    def dhw_electric_heater_status(self) -> int:
        """Return Domestic Hot Water (DHW) electric heater status (0 - 100%)."""

        if self.product_line != econordic.PRODUCT_LINE:
            raise Exception("DHW electric heater status is only available on EcoNordic models")

        return int(self._get_value(econordic.DHW_ELECTRIC_HEATER_STATUS))

    @property
    def space_heating_setpoint(self) -> float:
        """Return room temperature setpoint for heating circuit 1."""

        if self.product_line != econordic.PRODUCT_LINE:
            raise Exception("Space heating setpoint is only available on EcoNordic models")

        return float(self._get_value(econordic.HEATING_CIRCUIT_1_ROOM_TEMPERATURE_SETPOINT))

    async def set_space_heating_setpoint(self, temperature: float) -> None:
        """Set room temperature setpoint for heating circuit 1.

        temperature -- temperature in degrees Celsius
        """

        if self.product_line != econordic.PRODUCT_LINE:
            raise Exception("Space heating setpoint is only available on EcoNordic models")

        await self._set_value(econordic.HEATING_CIRCUIT_1_ROOM_TEMPERATURE_SETPOINT, temperature)

    @property
    def heat_pump_state(self) -> int:
        """Return heat pump state."""

        if self.product_line != econordic.PRODUCT_LINE:
            raise Exception("Heat pump state is only available on EcoNordic models")

        return int(self._get_value(econordic.HEAT_PUMP_STATE))
