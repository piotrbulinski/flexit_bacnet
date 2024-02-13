"""Flexit Nordic series config.

Based on https://www.flexit.no/globalassets/catalog/documents/bacnet-nordic-basic_2963.xlsx
"""
from .bacnet import DeviceProperty, ObjectType

# Comfort button [RW]
# 0 = Ventilation mode Away after Away delay timer duration [Pintval,318].
#     Also overrides Room operating mode PRESENT_VENTILATION_MODE.
# 1 = Ventilation mode according to Room operating mode PRESENT_VENTILATION_MODE.
COMFORT_BUTTON = DeviceProperty(ObjectType.BINARY_VALUE, 50, priority=13)
COMFORT_BUTTON_ACTIVE = 1
COMFORT_BUTTON_INACTIVE = 0

# Sets the delay time in minutes for Comfort button
COMFORT_BUTTON_DELAY = DeviceProperty(ObjectType.POSITIVE_INTEGER_VALUE, 318)

# Heat recovery ventilation state
OPERATION_MODE = DeviceProperty(ObjectType.MULTI_STATE_VALUE, 361)
OPERATION_MODE_OFF = 1
OPERATION_MODE_AWAY = 2
OPERATION_MODE_HOME = 3
OPERATION_MODE_HIGH = 4
OPERATION_MODE_FUME_HOOD = 5
OPERATION_MODE_FIREPLACE = 6
OPERATION_MODE_TEMPORARY_HIGH = 7

# Ventilation mode [RW]
# Only works if COMFORT_BUTTON == 1
# If COMFORT_BUTTON == 0, this register is Away.
VENTILATION_MODE = DeviceProperty(ObjectType.MULTI_STATE_VALUE, 42, priority=13)
VENTILATION_MODE_STOP = 1
VENTILATION_MODE_AWAY = 2
VENTILATION_MODE_HOME = 3
VENTILATION_MODE_HIGH = 4

# Air temp., setpoint AWAY (e.g. 18.0 degreesCelsius)
AIR_TEMP_SETPOINT_AWAY = DeviceProperty(ObjectType.ANALOG_VALUE, 1985)

# Air temp., setpoint HOME (e.g. 19.0 degreesCelsius)
AIR_TEMP_SETPOINT_HOME = DeviceProperty(ObjectType.ANALOG_VALUE, 1994)

# Trigger temporary fireplace ventilation
FIREPLACE_VENTILATION = DeviceProperty(ObjectType.MULTI_STATE_VALUE, 360)
FIREPLACE_VENTILATION_TRIGGER = 2

# Fireplace ventilation runtime (e.g. 10 minutes)
FIREPLACE_VENTILATION_RUNTIME = DeviceProperty(ObjectType.POSITIVE_INTEGER_VALUE, 270)

# Fireplace ventilation remaining time in minutes
FIREPLACE_VENTILATION_REMAINING_DURATION = DeviceProperty(ObjectType.ANALOG_VALUE, 2038)

# Trigger temporary rapid ventilation
RAPID_VENTILATION = DeviceProperty(ObjectType.MULTI_STATE_VALUE, 357)
RAPID_VENTILATION_TRIGGER = 2

# Rapid ventilation runtime (e.g. 10 minutes)
RAPID_VENTILATION_RUNTIME = DeviceProperty(ObjectType.POSITIVE_INTEGER_VALUE, 293)

# Rapid ventilation remaining time in minutes
RAPID_VENTILATION_REMAINING_DURATION = DeviceProperty(ObjectType.ANALOG_VALUE, 2031)

# Outside air temperature (e.g. 10.680000305175781 degreesCelsius)
OUTSIDE_AIR_TEMPERATURE = DeviceProperty(ObjectType.ANALOG_INPUT, 1)

# Supply air temperature (e.g. 18.809999465942383 degreesCelsius)
SUPPLY_AIR_TEMPERATURE = DeviceProperty(ObjectType.ANALOG_INPUT, 4)

# Tacho, supply fan (e.g. 3120.0 revolutionsPerMinute)
TACHO_SUPPLY_FAN = DeviceProperty(ObjectType.ANALOG_INPUT, 5)

# Exhaust air temperature (e.g. 14.770000457763672 degreesCelsius)
EXHAUST_AIR_TEMPERATURE = DeviceProperty(ObjectType.ANALOG_INPUT, 11)

# Tacho, exhaust fan (e.g. 3090.0 revolutionsPerMinute)
TACHO_EXHAUST_FAN = DeviceProperty(ObjectType.ANALOG_INPUT, 12)

# Extract air temperature (e.g. 21.5 degreesCelsius)
EXTRACT_AIR_TEMPERATURE = DeviceProperty(ObjectType.ANALOG_INPUT, 59)
EXTRACT_AIR_TEMPERATURE_ALT = DeviceProperty(ObjectType.ANALOG_INPUT, 95)

# Room temperature (e.g. 22.200000762939453 degreesCelsius)
ROOM_TEMPERATURE = DeviceProperty(ObjectType.ANALOG_INPUT, 75)

# Fan speed, supply air (e.g. 70.0 percent)
FAN_SPEED_SUPPLY_AIR = DeviceProperty(ObjectType.ANALOG_OUTPUT, 3)

# Fan speed, exhaust air (e.g. 70.0 percent)
FAN_SPEED_EXHAUST_AIR = DeviceProperty(ObjectType.ANALOG_OUTPUT, 4)

# Rotating heat exchanger (e.g. 55.41521453857422 percent)
ROTATING_HEAT_EXCHANGER_SPEED = DeviceProperty(ObjectType.ANALOG_OUTPUT, 0)

# Rotating heat exchanger, efficiency (e.g. 61.461185455322266 percent)
ROTATING_HEAT_EXCHANGER_EFFICIENCY = DeviceProperty(ObjectType.ANALOG_VALUE, 2023)

# Electrical heater, OFF/ON (e.g. inactive)
ELECTRICAL_HEATER = DeviceProperty(ObjectType.BINARY_VALUE, 445)
ELECTRICAL_HEATER_ACTIVE = 1
ELECTRICAL_HEATER_INACTIVE = 0

# Electric heater, nom. Power (e.g. 0.800000011920929 kilowatts)
ELECTRIC_HEATER_NOM_POWER = DeviceProperty(ObjectType.ANALOG_VALUE, 190)

# Heating coil electric power (e.g. 0.0 kilowatts)
HEATING_COIL_ELECTRIC_POWER = DeviceProperty(ObjectType.ANALOG_VALUE, 194)

# Cooker hood, activate (e.g. inactive)
COOKER_HOOD = DeviceProperty(ObjectType.BINARY_VALUE, 402, priority=13)
COOKER_HOOD_ACTIVE = 1
COOKER_HOOD_INACTIVE = 0

# Linear, setpoint supply air HIGH (e.g. 100.0 percent)
LINEAR_SETPOINT_SUPPLY_AIR_HIGH = DeviceProperty(ObjectType.ANALOG_VALUE, 1835)

# Linear, setpoint supply air HOME (e.g. 70.0 percent)
LINEAR_SETPOINT_SUPPLY_AIR_HOME = DeviceProperty(ObjectType.ANALOG_VALUE, 1836)

# Linear, setpoint supply air AWAY (e.g. 50.0 percent)
LINEAR_SETPOINT_SUPPLY_AIR_AWAY = DeviceProperty(ObjectType.ANALOG_VALUE, 1837)

# Linear, setpoint supply air FIRE (e.g. 90.0 percent)
LINEAR_SETPOINT_SUPPLY_AIR_FIRE = DeviceProperty(ObjectType.ANALOG_VALUE, 1838)

# Linear, setpoint supply air COOKER (e.g. 90.0 percent)
LINEAR_SETPOINT_SUPPLY_AIR_COOKER = DeviceProperty(ObjectType.ANALOG_VALUE, 1839)

# Linear, setpoint exhaust air HIGH (e.g. 100.0 percent)
LINEAR_SETPOINT_EXHAUST_AIR_HIGH = DeviceProperty(ObjectType.ANALOG_VALUE, 1840)

# Linear, setpoint exhaust air HOME (e.g. 70.0 percent)
LINEAR_SETPOINT_EXHAUST_AIR_HOME = DeviceProperty(ObjectType.ANALOG_VALUE, 1841)

# Linear, setpoint exhaust air AWAY (e.g. 50.0 percent)
LINEAR_SETPOINT_EXHAUST_AIR_AWAY = DeviceProperty(ObjectType.ANALOG_VALUE, 1842)

# Linear, setpoint exhaust air FIRE (e.g. 50.0 percent)
LINEAR_SETPOINT_EXHAUST_AIR_FIRE = DeviceProperty(ObjectType.ANALOG_VALUE, 1843)

# Linear, setpoint exhaust air COOKER (e.g. 50.0 percent)
LINEAR_SETPOINT_EXHAUST_AIR_COOKER = DeviceProperty(ObjectType.ANALOG_VALUE, 1844)

# Air filter, operating time (e.g. 0.0 hours)
AIR_FILTER_OPERATING_TIME = DeviceProperty(ObjectType.ANALOG_VALUE, 285)

# Air filter, time period for exchange (e.g. 4380.0 hours)
AIR_FILTER_TIME_PERIOD_FOR_EXCHANGE = DeviceProperty(ObjectType.ANALOG_VALUE, 286)

# Air filter polluted (e.g. inactive)
AIR_FILTER_POLLUTED = DeviceProperty(ObjectType.BINARY_VALUE, 522)
AIR_FILTER_POLLUTED_ACTIVE = 1

# Air filter replace timer reset (e.g. 1 None)
AIR_FILTER_REPLACE_TIMER_RESET = DeviceProperty(ObjectType.MULTI_STATE_VALUE, 613)
AIR_FILTER_REPLACE_TIMER_RESET_TRIGGER = 2

# Humidity sensors
EXTRACT_AIR_HUMIDITY = DeviceProperty(ObjectType.ANALOG_INPUT, 96)  # available on some models
ROOM_1_HUMIDITY = DeviceProperty(ObjectType.ANALOG_VALUE, 2093)
ROOM_2_HUMIDITY = DeviceProperty(ObjectType.ANALOG_VALUE, 2094)
ROOM_3_HUMIDITY = DeviceProperty(ObjectType.ANALOG_VALUE, 2095)

# List of all DeviceProperties defined in this file
DEVICE_PROPERTIES = [
    item for _, item in globals().items() if isinstance(item, DeviceProperty)
]

# The first six digits in the Nordic serial number corresponds to the Nordic model.
NORDIC_MODELS = {
    800111: "S2 REL",
    800121: "S3 REL",
    800110: "S2 RER",
    800120: "S3 RER",
    800221: "CL4 REL",
    800220: "CL4 RER",
    800130: "S4 RER",
    800131: "S4 REL",
    800210: "CL2 RER",
    800211: "CL2 REL",
    800200: "CL3 RER",
    800201: "CL3 REL",
    800300: "KS3 RER",
    800301: "KS3 REL",
}

# The name of the device
DEVICE_NAMES = {
    "HvacFnct21y_A": "Flexit Nordic",
}
