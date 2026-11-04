from types import ModuleType
from typing import Any, Optional

from flexit_bacnet import bacnet
from flexit_bacnet import nordic, econordic
from flexit_bacnet.models import MODELS
from flexit_bacnet.readings import Reading, Unit, collect_readings, reading

# The name of the device
DEVICE_NAMES = {
    "HvacFnct21y_A": "Flexit Nordic",
}


class FlexitBACnet:
    def __init__(
        self,
        device_address: str,
        device_id: int,
        port: int = bacnet.DEFAULT_BACNET_PORT,
        timeout: float = bacnet.DEFAULT_TIMEOUT,
        read_retries: int = bacnet.DEFAULT_READ_RETRIES,
    ) -> None:
        """Flexit unit at device_address with BACnet device_id (2 by default on the units).

        timeout -- seconds to wait for each answer from the unit
        read_retries -- extra attempts for update() after a timeout (writes are never retried)
        """
        self.bacnet = bacnet.BACnetClient(device_address, port, timeout=timeout, read_retries=read_retries)
        self.device_id = device_id
        self._state: Optional[bacnet.DeviceState] = None

        # property mapping for the specific product line (nordic/econordic),
        # resolved by the first call to update()
        self._prop_map_module: Optional[ModuleType] = None

    @property
    def _prop_map(self) -> ModuleType:
        """Return property mapping module (nordic/econordic) for this device.

        The product line is detected from the serial number, so the mapping is
        only known after the first update(). Reading or writing before that
        would guess the object identifiers, which differ between product lines.
        """
        if self._prop_map_module is None:
            raise Exception("must run 'update()' method first")

        return self._prop_map_module

    @property
    def _device_property(self) -> bacnet.DeviceProperty:
        return bacnet.DeviceProperty(
            bacnet.ObjectType.DEVICE,
            self.device_id,
            read_values=[bacnet.ReadValue.OBJECT_NAME, bacnet.ReadValue.DESCRIPTION],
        )

    @classmethod
    def readings(cls) -> list[Reading]:
        """Return label and unit of every value property, in definition order."""
        return collect_readings(cls)

    @classmethod
    def get_reading(cls, name: str) -> Reading:
        """Return label and unit of the given property, e.g. get_reading("extract_air_humidity")."""
        for info in cls.readings():
            if info.name == name:
                return info

        raise KeyError(name)

    async def _get_property_mapping(self) -> ModuleType:
        """Return property mapping module based on product line."""
        self._state = await self.bacnet.read_multiple([self._device_property])

        if self.product_line == econordic.PRODUCT_LINE:
            return econordic

        return nordic

    async def update(self) -> None:
        """Refresh local device state.

        Must be called before any other property or method is used: the first
        call detects the product line (Nordic/EcoNordic) and selects the
        matching property mapping.
        """
        if self._prop_map_module is None:
            self._prop_map_module = await self._get_property_mapping()

        device_properties = self._prop_map.DEVICE_PROPERTIES + [self._device_property]

        self._state = await self.bacnet.read_multiple(device_properties)

    def _get_value(
        self,
        device_property: Optional[bacnet.DeviceProperty],
        value_name: Optional[bacnet.ReadValue] = None,
    ) -> Any:

        if self._state is None:
            raise Exception("must run 'update()' method first")

        # the product line has no such object at all (e.g. DHW_STATE on Nordic)
        if device_property is None:
            return None

        if value_name is None:
            value_name = bacnet.ReadValue.PRESENT_VALUE

        # an object or property the answer does not contain at all (e.g. a
        # trimmed answer from an older firmware) is unknown, like a PropertyError
        value = dict(self._state.get(device_property.object_identifier, ())).get(value_name)

        # the unit does not have this object/property (e.g. EXTRACT_AIR_HUMIDITY
        # on units without the sensor): report it as unknown rather than as a
        # reading of 0
        if value is None or isinstance(value, bacnet.PropertyError):
            return None

        return value

    def _get_float(self, device_property: Optional[bacnet.DeviceProperty], ndigits: Optional[int] = None) -> Optional[float]:
        """Return the present value as float (optionally rounded), None if the unit lacks the object."""
        value = self._get_value(device_property)
        if value is None:
            return None

        if ndigits is not None:
            value = round(value, ndigits)

        return float(value)

    def _get_int(self, device_property: Optional[bacnet.DeviceProperty], rounded: bool = False) -> Optional[int]:
        """Return the present value as int (optionally rounded), None if the unit lacks the object."""
        value = self._get_value(device_property)
        if value is None:
            return None

        return int(round(value)) if rounded else int(value)

    def _get_flag(self, device_property: Optional[bacnet.DeviceProperty], active_value: Any) -> Optional[bool]:
        """Return True if the present value equals active_value, None if the unit lacks the object."""
        value = self._get_value(device_property)
        if value is None:
            return None

        return value == active_value

    async def _set_value(self, device_property: Optional[bacnet.DeviceProperty], value: Any) -> None:
        if device_property is None:
            raise Exception(f"not available on {self.product_line} models")

        await self.bacnet.write(device_property, value)
        await self.update()

    @property
    @reading("Device name")
    def device_name(self) -> str:
        """Return device name, e.g.: Flexit Nordic"""
        device_name_from_device = self._get_value(self._device_property, bacnet.ReadValue.OBJECT_NAME)
        device_name = DEVICE_NAMES.get(device_name_from_device)

        if not isinstance(device_name, str):
            return ''

        return device_name

    @property
    @reading("Serial number")
    def serial_number(self) -> str:
        """Return device's serial number, e.g.: 800220-000000."""
        serial_number = self._get_value(self._device_property, bacnet.ReadValue.DESCRIPTION)

        if not isinstance(serial_number, str):
            return ''

        return serial_number

    @property
    @reading("Device model")
    def model(self) -> str:
        """Return device's model, e.g.: S2 REL."""
        try:
            model_id = int(self.serial_number[0:6])
        except ValueError:
            return ''

        return MODELS.get(model_id, '')

    @property
    @reading("Product line")
    def product_line(self) -> str:
        """Return product line, e.g.: Nordic or EcoNordic."""
        if self.serial_number.startswith(econordic.SERIAL_PREFIX):
            return econordic.PRODUCT_LINE

        return nordic.PRODUCT_LINE

    @property
    @reading("Outside air temperature", Unit.CELSIUS)
    def outside_air_temperature(self) -> Optional[float]:
        """Outside air temperature in degrees Celsius, e.g. 14.3."""
        return self._get_float(self._prop_map.OUTSIDE_AIR_TEMPERATURE, 1)

    @property
    @reading("Supply air temperature", Unit.CELSIUS)
    def supply_air_temperature(self) -> Optional[float]:
        """Supply air temperature in degrees Celsius, e.g. 18.9."""
        return self._get_float(self._prop_map.SUPPLY_AIR_TEMPERATURE, 1)

    @property
    @reading("Exhaust air temperature", Unit.CELSIUS)
    def exhaust_air_temperature(self) -> Optional[float]:
        """Exhaust air temperature in degrees Celsius, e.g. 14.5."""
        return self._get_float(self._prop_map.EXHAUST_AIR_TEMPERATURE, 1)

    @property
    @reading("Extract air temperature", Unit.CELSIUS)
    def extract_air_temperature(self) -> Optional[float]:
        """Extract air temperature in degrees Celsius, e.g. 14.3."""
        value = self._get_float(self._prop_map.EXTRACT_AIR_TEMPERATURE, 1)

        # as some models use different object identifier for extract air temperature
        # we need to check if the value is 0.0 (or missing) and try to read the alternative value
        if value is None or value == 0.0:
            alt_value = self._get_float(self._prop_map.EXTRACT_AIR_TEMPERATURE_ALT, 1)
            if alt_value is not None:
                value = alt_value

        return value

    @property
    @reading("Extract air humidity", Unit.PERCENT)
    def extract_air_humidity(self) -> Optional[float]:
        """Extract air relative humidity in %, e.g. 40.3."""
        return self._get_float(self._prop_map.EXTRACT_AIR_HUMIDITY, 1)

    @property
    @reading("Room temperature", Unit.CELSIUS)
    def room_temperature(self) -> Optional[float]:
        """Room temperature in degrees Celsius, e.g. 14.3.

        Temperature is read from the temperature sensor on a CI70 panel.
        """
        return self._get_float(self._prop_map.ROOM_TEMPERATURE, 1)

    @property
    @reading("Room 1 humidity", Unit.PERCENT)
    def room_1_humidity(self) -> Optional[float]:
        """Room 1 relative humidity in %, e.g. 40.3.

        RH value from CI77 - RH sensor 1.
        """
        return self._get_float(self._prop_map.ROOM_1_HUMIDITY, 1)

    @property
    @reading("Room 2 humidity", Unit.PERCENT)
    def room_2_humidity(self) -> Optional[float]:
        """Room 2 relative humidity in %, e.g. 40.3.

        RH value from CI77 - RH sensor 2.
        """
        return self._get_float(self._prop_map.ROOM_2_HUMIDITY, 1)

    @property
    @reading("Room 3 humidity", Unit.PERCENT)
    def room_3_humidity(self) -> Optional[float]:
        """Room 3 relative humidity in %, e.g. 40.3.

        RH value from CI77 - RH sensor 3.
        """
        return self._get_float(self._prop_map.ROOM_3_HUMIDITY, 1)

    @property
    @reading("Humidity setpoint (present)", Unit.PERCENT)
    def humidity_setpoint_present(self) -> Optional[float]:
        """Present humidity setpoint in %, e.g. 70.0."""
        return self._get_float(self._prop_map.HUMIDITY_SETPOINT_PRESENT, 1)

    @property
    @reading("Humidity setpoint Home", Unit.PERCENT)
    def humidity_setpoint_home(self) -> Optional[float]:
        """Humidity setpoint for Home mode in %, e.g. 70.0."""
        return self._get_float(self._prop_map.HUMIDITY_SETPOINT_HOME, 1)

    async def set_humidity_setpoint_home(self, percent: float) -> None:
        """Set humidity setpoint for Home mode.

        percent -- relative humidity in % (0 - 100)
        """
        await self._set_humidity_setpoint(self._prop_map.HUMIDITY_SETPOINT_HOME, percent)

    @property
    @reading("Humidity setpoint Away", Unit.PERCENT)
    def humidity_setpoint_away(self) -> Optional[float]:
        """Humidity setpoint for Away mode in %, e.g. 80.0."""
        return self._get_float(self._prop_map.HUMIDITY_SETPOINT_AWAY, 1)

    async def set_humidity_setpoint_away(self, percent: float) -> None:
        """Set humidity setpoint for Away mode.

        percent -- relative humidity in % (0 - 100)
        """
        await self._set_humidity_setpoint(self._prop_map.HUMIDITY_SETPOINT_AWAY, percent)

    @property
    @reading("Humidity setpoint High", Unit.PERCENT)
    def humidity_setpoint_high(self) -> Optional[float]:
        """Humidity setpoint for High mode in %, e.g. 100.0."""
        return self._get_float(self._prop_map.HUMIDITY_SETPOINT_HIGH, 1)

    async def set_humidity_setpoint_high(self, percent: float) -> None:
        """Set humidity setpoint for High mode.

        percent -- relative humidity in % (0 - 100)
        """
        await self._set_humidity_setpoint(self._prop_map.HUMIDITY_SETPOINT_HIGH, percent)

    async def _set_humidity_setpoint(self, device_property: bacnet.DeviceProperty, percent: float) -> None:
        # chained comparison also rejects NaN
        if not 0 <= percent <= 100:
            raise ValueError("humidity setpoint must be between 0 and 100 %")

        await self._set_value(device_property, float(percent))

    @property
    @reading("Dehumidification fan control", Unit.PERCENT)
    def dehumidification_fan_control(self) -> Optional[float]:
        """Fan speed request caused by humidity control in %, e.g. 0.0."""
        return self._get_float(self._prop_map.DEHUMIDIFICATION_FAN_CONTROL, 1)

    @property
    @reading("Dehumidification PID control")
    def dehumidification_pid_control(self) -> Optional[bool]:
        """True if setpoint based (PID) humidity control is enabled."""
        return self._get_flag(self._prop_map.DEHUMIDIFICATION_PID_CONTROL, self._prop_map.DEHUMIDIFICATION_PID_CONTROL_ACTIVE)

    async def enable_dehumidification_pid_control(self) -> None:
        """Enable setpoint based (PID) humidity control."""
        await self._set_value(self._prop_map.DEHUMIDIFICATION_PID_CONTROL, self._prop_map.DEHUMIDIFICATION_PID_CONTROL_ACTIVE)

    async def disable_dehumidification_pid_control(self) -> None:
        """Disable setpoint based (PID) humidity control."""
        await self._set_value(self._prop_map.DEHUMIDIFICATION_PID_CONTROL, self._prop_map.DEHUMIDIFICATION_PID_CONTROL_INACTIVE)

    @property
    @reading("Dehumidification slope control")
    def dehumidification_slope_control(self) -> Optional[int]:
        """Slope (rapid humidity rise, e.g. shower) control mode:
        1 - Disabled (DEHUMIDIFICATION_SLOPE_CONTROL_DISABLED)
        2 - Extract air humidity (DEHUMIDIFICATION_SLOPE_CONTROL_EXTRACT_AIR)
        3 - Max room humidity (DEHUMIDIFICATION_SLOPE_CONTROL_ROOM_MAX)
        """
        return self._get_int(self._prop_map.DEHUMIDIFICATION_SLOPE_CONTROL)

    async def set_dehumidification_slope_control(self, mode: int) -> None:
        """Set slope control mode to one of the values of dehumidification_slope_control."""
        if mode not in (
            self._prop_map.DEHUMIDIFICATION_SLOPE_CONTROL_DISABLED,
            self._prop_map.DEHUMIDIFICATION_SLOPE_CONTROL_EXTRACT_AIR,
            self._prop_map.DEHUMIDIFICATION_SLOPE_CONTROL_ROOM_MAX,
        ):
            raise ValueError(f"unsupported slope control mode: {mode}")

        await self._set_value(self._prop_map.DEHUMIDIFICATION_SLOPE_CONTROL, mode)

    @property
    @reading("Dehumidification slope switch-on")
    def dehumidification_slope_switch_on(self) -> Optional[float]:
        """Humidity slope above which humidity control is switched on, e.g. 1.0."""
        return self._get_float(self._prop_map.DEHUMIDIFICATION_SLOPE_SWITCH_ON, 2)

    async def set_dehumidification_slope_switch_on(self, value: float) -> None:
        """Set humidity slope above which humidity control is switched on."""
        await self._set_value(self._prop_map.DEHUMIDIFICATION_SLOPE_SWITCH_ON, float(value))

    @property
    @reading("Dehumidification slope switch-off")
    def dehumidification_slope_switch_off(self) -> Optional[float]:
        """Humidity slope below which humidity control is switched off, e.g. -0.3."""
        return self._get_float(self._prop_map.DEHUMIDIFICATION_SLOPE_SWITCH_OFF, 2)

    async def set_dehumidification_slope_switch_off(self, value: float) -> None:
        """Set humidity slope below which humidity control is switched off."""
        await self._set_value(self._prop_map.DEHUMIDIFICATION_SLOPE_SWITCH_OFF, float(value))

    @property
    @reading("Dehumidification slope")
    def dehumidification_slope(self) -> Optional[float]:
        """Current calculated humidity slope, e.g. 0.0."""
        return self._get_float(self._prop_map.DEHUMIDIFICATION_SLOPE, 2)

    @property
    @reading("Dehumidification by slope")
    def dehumidification_by_slope(self) -> Optional[bool]:
        """True if the current humidity control request is caused by the slope."""
        return self._get_flag(self._prop_map.DEHUMIDIFICATION_BY_SLOPE, self._prop_map.DEHUMIDIFICATION_BY_SLOPE_ACTIVE)

    @property
    @reading("Dehumidification slope resolution", Unit.MINUTES)
    def dehumidification_slope_resolution(self) -> Optional[int]:
        """Time base of the humidity slope calculation in minutes, e.g. 5."""
        return self._get_int(self._prop_map.DEHUMIDIFICATION_SLOPE_RESOLUTION)

    @property
    @reading("Dehumidification slope on delay", Unit.SECONDS)
    def dehumidification_slope_on_delay(self) -> Optional[int]:
        """On delay of the slope control in seconds, e.g. 600."""
        return self._get_int(self._prop_map.DEHUMIDIFICATION_SLOPE_ON_DELAY)

    async def set_dehumidification_slope_on_delay(self, seconds: int) -> None:
        """Set on delay of the slope control in seconds."""
        await self._set_value(self._prop_map.DEHUMIDIFICATION_SLOPE_ON_DELAY, seconds)

    @property
    @reading("Dehumidification switch-off delay", Unit.MINUTES)
    def dehumidification_switch_off_delay(self) -> Optional[int]:
        """Humidity control switch-off delay in minutes, e.g. 30."""
        return self._get_int(self._prop_map.DEHUMIDIFICATION_SWITCH_OFF_DELAY)

    async def set_dehumidification_switch_off_delay(self, minutes: int) -> None:
        """Set humidity control switch-off delay in minutes."""
        await self._set_value(self._prop_map.DEHUMIDIFICATION_SWITCH_OFF_DELAY, minutes)

    @property
    @reading("Dehumidification max runtime", Unit.MINUTES)
    def dehumidification_max_runtime(self) -> Optional[int]:
        """Maximum runtime of humidity control in minutes, e.g. 120."""
        return self._get_int(self._prop_map.DEHUMIDIFICATION_MAX_RUNTIME)

    async def set_dehumidification_max_runtime(self, minutes: int) -> None:
        """Set maximum runtime of humidity control in minutes."""
        await self._set_value(self._prop_map.DEHUMIDIFICATION_MAX_RUNTIME, minutes)

    @property
    @reading("Comfort button")
    def comfort_button(self) -> Optional[bool]:
        """Comfort button state, True if active."""
        return self._get_flag(self._prop_map.COMFORT_BUTTON, self._prop_map.COMFORT_BUTTON_ACTIVE)

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
    @reading("Operation mode")
    def operation_mode(self) -> Optional[int]:
        """Returns current heat exchanger operation mode, e.g. Home."""
        return self._get_value(self._prop_map.OPERATION_MODE)

    @property
    @reading("Ventilation mode")
    def ventilation_mode(self) -> Optional[int]:
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
    @reading("Air temperature setpoint Away", Unit.CELSIUS)
    def air_temp_setpoint_away(self) -> Optional[float]:
        """Return temperature setpoint for Away mode."""
        return self._get_float(self._prop_map.AIR_TEMP_SETPOINT_AWAY)

    async def set_air_temp_setpoint_away(self, temperature: float):
        """Set temperature setpoint for Away mode.

        temperature -- temperature in degrees Celsius
        """
        await self._set_value(self._prop_map.AIR_TEMP_SETPOINT_AWAY, temperature)

    @property
    @reading("Air temperature setpoint Home", Unit.CELSIUS)
    def air_temp_setpoint_home(self) -> Optional[float]:
        """Return temperature setpoint for Home mode."""
        return self._get_float(self._prop_map.AIR_TEMP_SETPOINT_HOME)

    async def set_air_temp_setpoint_home(self, temperature: float) -> None:
        """Set temperature setpoint for Home mode.

        temperature -- temperature in degrees Celsius
        """
        await self._set_value(self._prop_map.AIR_TEMP_SETPOINT_HOME, temperature)

    @property
    def _runtime_is_read_only(self) -> bool:
        """Return true if the fireplace/rapid runtime objects cannot be written.

        On EcoNordic units the runtime objects (FIREPLACE_VENTILATION_RUNTIME,
        RAPID_VENTILATION_RUNTIME) are read-only: a write is rejected by the
        unit with an Error PDU. The duration is configured in the Flexit GO app
        and the unit runs that configured duration. Verified on an EcoNordic WH4.
        """
        return self.product_line == econordic.PRODUCT_LINE

    async def start_fireplace_ventilation(self, minutes: int) -> None:
        """Set duration and trigger fireplace ventilation mode.

        minutes -- duration of fireplace ventilation in minutes (1 - 360)

        Raises on EcoNordic units, where the runtime is read-only (see
        `_runtime_is_read_only`) - use trigger_fireplace_mode() instead.
        """
        await self.set_fireplace_mode_runtime(minutes)
        await self.trigger_fireplace_mode()

    async def set_fireplace_mode_runtime(self, minutes: int) -> None:
        """Set runtime duration for the fireplace ventilation mode.

        minutes -- duration of fireplace ventilation in minutes (1 - 360)

        Raises on EcoNordic units, where the runtime is read-only.
        """
        if self._runtime_is_read_only:
            raise Exception(
                "Fireplace ventilation runtime is read-only on EcoNordic models - use trigger_fireplace_mode()"
            )

        await self._set_value(self._prop_map.FIREPLACE_VENTILATION_RUNTIME, minutes)

    @property
    @reading("Fireplace mode runtime", Unit.MINUTES)
    def fireplace_mode_runtime(self) -> Optional[int]:
        """Returns currently set runtime for the fireplace mode (in minutes)."""
        return self._get_value(self._prop_map.FIREPLACE_VENTILATION_RUNTIME)

    async def trigger_fireplace_mode(self) -> None:
        """Trigger temporary fireplace ventilation mode."""
        await self._set_value(self._prop_map.FIREPLACE_VENTILATION, self._prop_map.FIREPLACE_VENTILATION_TRIGGER)

    @property
    @reading("Fireplace ventilation")
    def fireplace_ventilation_status(self) -> Optional[bool]:
        """Return true if fireplace mode is active."""
        return self._get_flag(self._prop_map.FIREPLACE_STATE, self._prop_map.FIREPLACE_STATE_ACTIVE)

    @property
    @reading("Fireplace ventilation remaining", Unit.MINUTES)
    def fireplace_ventilation_remaining_duration(self) -> Optional[int]:
        """Return remaining duration (in minutes) of fireplace ventilation mode.

        On some units (e.g. EcoNordic WH4) this holds the full configured
        duration while the mode is idle and only counts down while it runs, so a
        non-zero value does not mean the mode is active - use
        fireplace_ventilation_status for that.
        """
        return self._get_int(self._prop_map.FIREPLACE_VENTILATION_REMAINING_DURATION)

    async def start_rapid_ventilation(self, minutes: int) -> None:
        """Set duration and trigger temporary rapid ventilation mode.

        minutes -- duration of rapid ventilation in minutes (1 - 360)

        Raises on EcoNordic units, where the runtime is read-only (see
        `_runtime_is_read_only`) - use trigger_rapid_ventilation() instead.
        """
        if self._runtime_is_read_only:
            raise Exception(
                "Rapid ventilation runtime is read-only on EcoNordic models - use trigger_rapid_ventilation()"
            )

        await self._set_value(self._prop_map.RAPID_VENTILATION_RUNTIME, minutes)
        await self.trigger_rapid_ventilation()

    async def trigger_rapid_ventilation(self) -> None:
        """Trigger temporary rapid ventilation mode (counterpart of trigger_fireplace_mode)."""
        await self._set_value(self._prop_map.RAPID_VENTILATION, self._prop_map.RAPID_VENTILATION_TRIGGER)

    @property
    @reading("Rapid ventilation remaining", Unit.MINUTES)
    def rapid_ventilation_remaining_duration(self) -> Optional[int]:
        """Return remaining duration (in minutes) of rapid ventilation mode.

        On some units (e.g. EcoNordic WH4) this holds the full configured
        duration while the mode is idle and only counts down while it runs, so a
        non-zero value does not mean the mode is active.
        """
        return self._get_int(self._prop_map.RAPID_VENTILATION_REMAINING_DURATION)

    @property
    @reading("Supply air fan control signal", Unit.PERCENT)
    def supply_air_fan_control_signal(self) -> Optional[int]:
        """Return current supply air fan control signal (in %)."""
        return self._get_int(self._prop_map.FAN_SPEED_SUPPLY_AIR)

    @property
    @reading("Supply air fan speed", Unit.RPM)
    def supply_air_fan_rpm(self) -> Optional[int]:
        """Return current supply air fan RPM."""
        return self._get_int(self._prop_map.TACHO_SUPPLY_FAN)

    @property
    @reading("Exhaust air fan control signal", Unit.PERCENT)
    def exhaust_air_fan_control_signal(self) -> Optional[int]:
        """Return current exhaust air fan control signal (in %)."""
        return self._get_int(self._prop_map.FAN_SPEED_EXHAUST_AIR)

    @property
    @reading("Exhaust air fan speed", Unit.RPM)
    def exhaust_air_fan_rpm(self) -> Optional[int]:
        """Return current exhaust air fan RPM."""
        return self._get_int(self._prop_map.TACHO_EXHAUST_FAN)

    @property
    @reading("Electric heater enabled")
    def electric_heater(self) -> Optional[bool]:
        """Return True if electric heater is enabled."""
        return self._get_flag(self._prop_map.ELECTRICAL_HEATER, self._prop_map.ELECTRICAL_HEATER_ACTIVE)

    async def enable_electric_heater(self) -> None:
        """Enables electric air heater."""
        await self._set_value(self._prop_map.ELECTRICAL_HEATER, self._prop_map.ELECTRICAL_HEATER_ACTIVE)

    async def disable_electric_heater(self) -> None:
        """Disables electric air heater."""
        await self._set_value(self._prop_map.ELECTRICAL_HEATER, self._prop_map.ELECTRICAL_HEATER_INACTIVE)

    @property
    @reading("Electric heater nominal power", Unit.KILOWATT)
    def electric_heater_nominal_power(self) -> Optional[float]:
        """Return nominal heater power in kilowatts."""
        return self._get_float(self._prop_map.ELECTRIC_HEATER_NOM_POWER, 3)

    @property
    @reading("Electric heater power", Unit.KILOWATT)
    def electric_heater_power(self) -> Optional[float]:
        """Return heater power consumption in kilowatts."""
        return self._get_float(self._prop_map.HEATING_COIL_ELECTRIC_POWER, 3)

    @property
    @reading("Cooker hood")
    def cooker_hood_status(self) -> Optional[bool]:
        """Cooker hood ventilation state, True if active."""
        return self._get_flag(self._prop_map.COOKER_HOOD, self._prop_map.COOKER_HOOD_ACTIVE)

    async def activate_cooker_hood(self) -> None:
        """Activates cooker hood mode."""
        await self._set_value(self._prop_map.COOKER_HOOD, self._prop_map.COOKER_HOOD_ACTIVE)

    async def deactivate_cooker_hood(self) -> None:
        """Deactivates cooker hood mode."""
        await self._set_value(self._prop_map.COOKER_HOOD, self._prop_map.COOKER_HOOD_INACTIVE)

    @property
    @reading("Fan setpoint supply air Home", Unit.PERCENT)
    def fan_setpoint_supply_air_home(self) -> Optional[int]:
        """Return fan setpoint for supply air HOME in percent."""
        return self._get_int(self._prop_map.LINEAR_SETPOINT_SUPPLY_AIR_HOME)

    async def set_fan_setpoint_supply_air_home(self, percent: int) -> None:
        """Set fan setpoint for supply air HOME in percent."""
        await self._set_value(self._prop_map.LINEAR_SETPOINT_SUPPLY_AIR_HOME, percent)

    @property
    @reading("Fan setpoint extract air Home", Unit.PERCENT)
    def fan_setpoint_extract_air_home(self) -> Optional[int]:
        """Return fan setpoint for extract air HOME in percent."""
        return self._get_int(self._prop_map.LINEAR_SETPOINT_EXHAUST_AIR_HOME)

    async def set_fan_setpoint_extract_air_home(self, percent: int) -> None:
        """Set fan setpoint for extract air HOME in percent."""
        await self._set_value(self._prop_map.LINEAR_SETPOINT_EXHAUST_AIR_HOME, percent)

    @property
    @reading("Fan setpoint supply air High", Unit.PERCENT)
    def fan_setpoint_supply_air_high(self) -> Optional[int]:
        """Return fan setpoint for supply air HIGH in percent."""
        return self._get_int(self._prop_map.LINEAR_SETPOINT_SUPPLY_AIR_HIGH)

    async def set_fan_setpoint_supply_air_high(self, percent: int) -> None:
        """Set fan setpoint for supply air HIGH in percent."""
        await self._set_value(self._prop_map.LINEAR_SETPOINT_SUPPLY_AIR_HIGH, percent)

    @property
    @reading("Fan setpoint extract air High", Unit.PERCENT)
    def fan_setpoint_extract_air_high(self) -> Optional[int]:
        """Return fan setpoint for extract air HIGH in percent."""
        return self._get_int(self._prop_map.LINEAR_SETPOINT_EXHAUST_AIR_HIGH)

    async def set_fan_setpoint_extract_air_high(self, percent: int) -> None:
        """Set fan setpoint for extract air HIGH in percent."""
        await self._set_value(self._prop_map.LINEAR_SETPOINT_EXHAUST_AIR_HIGH, percent)

    @property
    @reading("Fan setpoint supply air Away", Unit.PERCENT)
    def fan_setpoint_supply_air_away(self) -> Optional[int]:
        """Return fan setpoint for supply air AWAY in percent."""
        return self._get_int(self._prop_map.LINEAR_SETPOINT_SUPPLY_AIR_AWAY)

    async def set_fan_setpoint_supply_air_away(self, percent: int) -> None:
        """Set fan setpoint for supply air AWAY in percent."""
        await self._set_value(self._prop_map.LINEAR_SETPOINT_SUPPLY_AIR_AWAY, percent)

    @property
    @reading("Fan setpoint extract air Away", Unit.PERCENT)
    def fan_setpoint_extract_air_away(self) -> Optional[int]:
        """Return fan setpoint for extract air AWAY in percent."""
        return self._get_int(self._prop_map.LINEAR_SETPOINT_EXHAUST_AIR_AWAY)

    async def set_fan_setpoint_extract_air_away(self, percent: int) -> None:
        """Set fan setpoint for extract air AWAY in percent."""
        await self._set_value(self._prop_map.LINEAR_SETPOINT_EXHAUST_AIR_AWAY, percent)

    @property
    @reading("Fan setpoint supply air Cooker", Unit.PERCENT)
    def fan_setpoint_supply_air_cooker(self) -> Optional[int]:
        """Return fan setpoint for supply air COOKER in percent."""
        return self._get_int(self._prop_map.LINEAR_SETPOINT_SUPPLY_AIR_COOKER)

    async def set_fan_setpoint_supply_air_cooker(self, percent: int) -> None:
        """Set fan setpoint for supply air COOKER in percent."""
        await self._set_value(self._prop_map.LINEAR_SETPOINT_SUPPLY_AIR_COOKER, percent)

    @property
    @reading("Fan setpoint extract air Cooker", Unit.PERCENT)
    def fan_setpoint_extract_air_cooker(self) -> Optional[int]:
        """Return fan setpoint for extract air COOKER in percent."""
        return self._get_int(self._prop_map.LINEAR_SETPOINT_EXHAUST_AIR_COOKER)

    async def set_fan_setpoint_extract_air_cooker(self, percent: int) -> None:
        """Set fan setpoint for extract air COOKER in percent."""
        await self._set_value(self._prop_map.LINEAR_SETPOINT_EXHAUST_AIR_COOKER, percent)

    @property
    @reading("Fan setpoint supply air Fireplace", Unit.PERCENT)
    def fan_setpoint_supply_air_fire(self) -> Optional[int]:
        """Return fan setpoint for supply air FIRE in percent."""
        return self._get_int(self._prop_map.LINEAR_SETPOINT_SUPPLY_AIR_FIRE)

    async def set_fan_setpoint_supply_air_fire(self, percent: int):
        """Set fan setpoint for supply air FIRE in percent."""
        await self._set_value(self._prop_map.LINEAR_SETPOINT_SUPPLY_AIR_FIRE, percent)

    @property
    @reading("Fan setpoint extract air Fireplace", Unit.PERCENT)
    def fan_setpoint_extract_air_fire(self) -> Optional[int]:
        """Return fan setpoint for extract air FIRE in percent."""
        return self._get_int(self._prop_map.LINEAR_SETPOINT_EXHAUST_AIR_FIRE)

    async def set_fan_setpoint_extract_air_fire(self, percent: int) -> None:
        """Set fan setpoint for extract air FIRE in percent."""
        await self._set_value(self._prop_map.LINEAR_SETPOINT_EXHAUST_AIR_FIRE, percent)

    @property
    @reading("Air filter operating time", Unit.HOURS)
    def air_filter_operating_time(self) -> Optional[float]:
        """Return air filter operating time in hours."""
        return self._get_float(self._prop_map.AIR_FILTER_OPERATING_TIME)

    @property
    @reading("Air filter exchange interval", Unit.HOURS)
    def air_filter_exchange_interval(self) -> Optional[float]:
        """Return air filter exchange interval in hours."""
        return self._get_float(self._prop_map.AIR_FILTER_TIME_PERIOD_FOR_EXCHANGE)

    @property
    @reading("Heat exchanger efficiency", Unit.PERCENT)
    def heat_exchanger_efficiency(self) -> Optional[int]:
        """Returns heat exchanger efficiency in percent."""
        return self._get_int(self._prop_map.ROTATING_HEAT_EXCHANGER_EFFICIENCY, rounded=True)

    @property
    @reading("Heat exchanger speed", Unit.PERCENT)
    def heat_exchanger_speed(self) -> Optional[int]:
        """Returns heat exchanger speed in percent."""
        return self._get_int(self._prop_map.ROTATING_HEAT_EXCHANGER_SPEED, rounded=True)

    @property
    @reading("Air filter polluted")
    def air_filter_polluted(self) -> Optional[bool]:
        """Returns True if filter is polluted."""
        return self._get_flag(self._prop_map.AIR_FILTER_POLLUTED, self._prop_map.AIR_FILTER_POLLUTED_ACTIVE)

    async def reset_air_filter_timer(self) -> None:
        """Resets air filter replace timer."""
        await self._set_value(
            self._prop_map.AIR_FILTER_REPLACE_TIMER_RESET, self._prop_map.AIR_FILTER_REPLACE_TIMER_RESET_TRIGGER
        )

    # Domestic Hot Water (DHW), heat pump and space heating - EcoNordic only.
    # Nordic units have none of these objects: the getters read None and the
    # setters raise (see the placeholders at the end of nordic.py).

    @property
    @reading("DHW operation mode")
    def dhw_operation_mode(self) -> Optional[int]:
        """Returns current Domestic Hot Water (DHW) operation mode, e.g. 1 (Comfort)."""
        return self._get_value(self._prop_map.DHW_OPERATION_MODE)

    async def set_dhw_operation_mode(self, mode: int) -> None:
        """Set Domestic Hot Water (DHW) operation mode.

        mode -- one of the supported values:
        1 - Comfort (DHW_OPERATION_MODE_COMFORT)
        2 - Economy (DHW_OPERATION_MODE_ECONOMY)
        """
        await self._set_value(self._prop_map.DHW_OPERATION_MODE, mode)

    async def dhw_temporary_boost_start(self) -> None:
        """Activate Domestic Hot Water (DHW) temporary boost mode."""
        await self._set_value(self._prop_map.DHW_TEMPORARY_BOOST, econordic.DHW_TEMPORARY_BOOST_START)

    async def dhw_temporary_boost_stop(self) -> None:
        """Deactivate Domestic Hot Water (DHW) temporary boost mode."""
        await self._set_value(self._prop_map.DHW_TEMPORARY_BOOST, econordic.DHW_TEMPORARY_BOOST_STOP)

    async def dhw_forced_charge_start(self) -> None:
        """Start a forced charge of the Domestic Hot Water (DHW) tank.

        The heat pump charges the tank up to the tank setpoint regardless of
        the DHW operation mode. There is no stop command: the charge runs
        until the unit's own stop condition is met. Check `dhw_state ==
        DHW_STATE_FORCED_CHARGE` to see whether a forced charge is running.
        """
        await self._set_value(self._prop_map.DHW_FORCED_CHARGE, econordic.DHW_FORCED_CHARGE_START)

    @property
    @reading("DHW state")
    def dhw_state(self) -> Optional[int]:
        """Return current Domestic Hot Water (DHW) state (one of econordic.DHW_STATE_*)."""
        return self._get_int(self._prop_map.DHW_STATE)

    @property
    @reading("DHW temperature setpoint Comfort", Unit.CELSIUS)
    def dhw_temperature_setpoint_comfort(self) -> Optional[float]:
        """Return Domestic Hot Water (DHW) temperature setpoint for Comfort mode, e.g. 55.0."""
        return self._get_float(self._prop_map.DHW_TEMPERATURE_SETPOINT_COMFORT)

    async def set_dhw_temperature_setpoint_comfort(self, temperature: float) -> None:
        """Set Domestic Hot Water (DHW) temperature setpoint for Comfort mode.

        temperature -- temperature in degrees Celsius
        """
        await self._set_value(self._prop_map.DHW_TEMPERATURE_SETPOINT_COMFORT, temperature)

    @property
    @reading("DHW temperature setpoint Economy", Unit.CELSIUS)
    def dhw_temperature_setpoint_economy(self) -> Optional[float]:
        """Return Domestic Hot Water (DHW) temperature setpoint for Economy mode, e.g. 45.0."""
        return self._get_float(self._prop_map.DHW_TEMPERATURE_SETPOINT_ECONOMY)

    async def set_dhw_temperature_setpoint_economy(self, temperature: float) -> None:
        """Set Domestic Hot Water (DHW) temperature setpoint for Economy mode.

        temperature -- temperature in degrees Celsius
        """
        await self._set_value(self._prop_map.DHW_TEMPERATURE_SETPOINT_ECONOMY, temperature)

    @property
    @reading("DHW tank temperature top", Unit.CELSIUS)
    def dhw_tank_temperature_top(self) -> Optional[float]:
        """Domestic Hot Water (DHW) tank top temperature in degrees Celsius, e.g. 52.4."""
        return self._get_float(self._prop_map.DHW_TANK_TEMPERATURE_TOP, 1)

    @property
    @reading("DHW tank temperature middle", Unit.CELSIUS)
    def dhw_tank_temperature_middle(self) -> Optional[float]:
        """Domestic Hot Water (DHW) tank middle temperature in degrees Celsius, e.g. 48.1."""
        return self._get_float(self._prop_map.DHW_TANK_TEMPERATURE_MIDDLE, 1)

    @property
    @reading("DHW tank temperature bottom", Unit.CELSIUS)
    def dhw_tank_temperature_bottom(self) -> Optional[float]:
        """Domestic Hot Water (DHW) tank bottom temperature in degrees Celsius, e.g. 35.7."""
        return self._get_float(self._prop_map.DHW_TANK_TEMPERATURE_BOTTOM, 1)

    @property
    @reading("DHW electric heater", Unit.PERCENT)
    def dhw_electric_heater_status(self) -> Optional[int]:
        """Return Domestic Hot Water (DHW) electric heater status in % (0 - 100)."""
        return self._get_int(self._prop_map.DHW_ELECTRIC_HEATER_STATUS)

    @property
    @reading("Space heating setpoint", Unit.CELSIUS)
    def space_heating_setpoint(self) -> Optional[float]:
        """Return room temperature setpoint for heating circuit 1, e.g. 21.0."""
        return self._get_float(self._prop_map.HEATING_CIRCUIT_1_ROOM_TEMPERATURE_SETPOINT)

    async def set_space_heating_setpoint(self, temperature: float) -> None:
        """Set room temperature setpoint for heating circuit 1.

        temperature -- temperature in degrees Celsius
        """
        await self._set_value(self._prop_map.HEATING_CIRCUIT_1_ROOM_TEMPERATURE_SETPOINT, temperature)

    @property
    @reading("Heat pump state")
    def heat_pump_state(self) -> Optional[int]:
        """Return heat pump state (one of econordic.HEAT_PUMP_STATE_*)."""
        return self._get_int(self._prop_map.HEAT_PUMP_STATE)

    # Free cooling - see the "Free cooling" section in nordic.py / econordic.py
    # and README.md for how the function works and which settings make it run.

    @property
    @reading("Plant state")
    def plant_state(self) -> Optional[int]:
        """Return plant state (one of PLANT_STATE_*) - what the ventilation plant is doing right now.

        None on units without the plant state object (e.g. Nordic S4).
        """
        return self._get_int(self._prop_map.PLANT_STATE)

    @property
    @reading("Plant operating mode")
    def plant_operating_mode(self) -> Optional[int]:
        """Return the present plant operating mode (one of PLANT_OPERATING_MODE_*), e.g. 4 (Pre-Comfort).

        None on units without the object (not verified on EcoNordic).
        """
        return self._get_int(self._prop_map.PRESENT_PLANT_OPERATING_MODE)

    @property
    @reading("Free cooling active")
    def free_cooling_active(self) -> Optional[bool]:
        """Return true if free cooling is running right now.

        This is what explains a unit that is suddenly running in HIGH with cold
        supply air. Flexit GO does not show it; the plant state does. Units
        without the plant state object (e.g. a Nordic CL4 with application
        v2.425) report it in the present plant operating mode instead. None if
        the unit has neither.
        """
        plant_state = self.plant_state
        if plant_state is not None:
            return plant_state == self._prop_map.PLANT_STATE_FREE_COOLING

        plant_operating_mode = self.plant_operating_mode
        if plant_operating_mode is not None:
            return plant_operating_mode == nordic.PLANT_OPERATING_MODE_FREE_COOLING

        return None

    @property
    @reading("Free cooling enabled")
    def free_cooling_enabled(self) -> Optional[bool]:
        """Return true if the free cooling function is enabled (allowed to run).

        This is the on/off an end user sees in Flexit GO. Whether it is running
        right now is `free_cooling_active`.
        """
        return self._get_flag(self._prop_map.FREE_COOLING_ENABLED, self._prop_map.FREE_COOLING_ENABLED_ACTIVE)

    async def enable_free_cooling(self) -> None:
        """Enable the free cooling function (installer-level setting in Flexit GO)."""
        await self._set_value(self._prop_map.FREE_COOLING_ENABLED, self._prop_map.FREE_COOLING_ENABLED_ACTIVE)

    async def disable_free_cooling(self) -> None:
        """Disable the free cooling function (installer-level setting in Flexit GO)."""
        await self._set_value(self._prop_map.FREE_COOLING_ENABLED, self._prop_map.FREE_COOLING_ENABLED_INACTIVE)

    @property
    @reading("Free cooling extract air setpoint", Unit.CELSIUS)
    def free_cooling_extract_temp_setpoint(self) -> Optional[float]:
        """Return the extract air temperature above which free cooling may start, in degrees Celsius."""
        return self._get_float(self._prop_map.FREE_COOLING_EXTRACT_TEMP_SETPOINT)

    async def set_free_cooling_extract_temp_setpoint(self, temperature: float) -> None:
        """Set the extract air temperature above which free cooling may start.

        temperature -- degrees Celsius, 10 - 30 (Flexit GO default 22). This is
                       effectively the room temperature you want free cooling to
                       keep the house below; free cooling also stops when the
                       extract air falls below it. Installer-level in Flexit GO.
        """
        await self._set_value(self._prop_map.FREE_COOLING_EXTRACT_TEMP_SETPOINT, temperature)

    @property
    @reading("Free cooling outside air limit", Unit.CELSIUS)
    def free_cooling_outside_temp_limit(self) -> Optional[float]:
        """Return the outdoor temperature below which free cooling is not used, in degrees Celsius."""
        return self._get_float(self._prop_map.FREE_COOLING_OUTSIDE_TEMP_LIMIT)

    async def set_free_cooling_outside_temp_limit(self, temperature: float) -> None:
        """Set the outdoor temperature below which free cooling is not used.

        temperature -- degrees Celsius, 10 - 30 (Flexit GO default 18). With the
                       default, free cooling only runs on warm nights; the lower
                       end of the range (10) lets it run on most summer nights in
                       a Nordic climate. Installer-level in Flexit GO.
        """
        await self._set_value(self._prop_map.FREE_COOLING_OUTSIDE_TEMP_LIMIT, temperature)

    @property
    @reading("Free cooling start difference", Unit.KELVIN)
    def free_cooling_dt_enable_start(self) -> Optional[float]:
        """Return how much colder (K) the outdoor air must be than the extract air for free cooling to start."""
        return self._get_float(self._prop_map.FREE_COOLING_DT_ENABLE_START)

    async def set_free_cooling_dt_enable_start(self, delta: float) -> None:
        """Set how much colder the outdoor air must be than the extract air for free cooling to start.

        delta -- K, 0 - 10 (Flexit GO default 4). Must be larger than
                 `free_cooling_dt_disable`. Installer-level in Flexit GO.
        """
        await self._set_value(self._prop_map.FREE_COOLING_DT_ENABLE_START, delta)

    @property
    @reading("Free cooling stop difference", Unit.KELVIN)
    def free_cooling_dt_disable(self) -> Optional[float]:
        """Return the extract/outdoor air temperature difference (K) below which free cooling stops."""
        return self._get_float(self._prop_map.FREE_COOLING_DT_DISABLE)

    async def set_free_cooling_dt_disable(self, delta: float) -> None:
        """Set the extract/outdoor air temperature difference below which free cooling stops.

        delta -- K, 0 - 10 (Flexit GO default 1). Must be smaller than
                 `free_cooling_dt_enable_start`. Installer-level in Flexit GO.
        """
        await self._set_value(self._prop_map.FREE_COOLING_DT_DISABLE, delta)
