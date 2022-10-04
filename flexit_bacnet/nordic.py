"""Flexit Nordic series config.

Based on https://www.flexit.no/globalassets/catalog/documents/bacnet-nordic-basic_2963.xlsx
"""
from .device_property import DeviceProperty

# Comfort button [RW]
# 0 = Ventilation mode Away after Away delay timer duration [Pintval,318].
#     Also overrides Room operating mode PRESENT_VENTILATION_MODE.
# 1 = Ventilation mode according to Room operating mode PRESENT_VENTILATION_MODE.
COMFORT_BUTTON = DeviceProperty('binaryValue', 50, priority=13)
COMFORT_BUTTON.ACTIVE = 'active'
COMFORT_BUTTON.INACTIVE = 'inactive'

# Sets the delay time in minutes for Comfort button
COMFORT_BUTTON_DELAY = DeviceProperty('positiveIntegerValue', 318)

# Heat recovery ventilation state
OPERATION_MODE = DeviceProperty('multiStateValue', 361)
OPERATION_MODE.OFF = 1
OPERATION_MODE.AWAY = 2
OPERATION_MODE.HOME = 3
OPERATION_MODE.HIGH = 4
OPERATION_MODE.FUME_HOOD = 5
OPERATION_MODE.FIREPLACE = 6
OPERATION_MODE.TEMPORARY_HIGH = 7
OPERATION_MODES = {
    OPERATION_MODE.OFF: "Off",
    OPERATION_MODE.AWAY: "Away",
    OPERATION_MODE.HOME: "Home",
    OPERATION_MODE.HIGH: "High",
    OPERATION_MODE.FUME_HOOD: "Fume hood",
    OPERATION_MODE.FIREPLACE: "Fireplace",
    OPERATION_MODE.TEMPORARY_HIGH: "Temporary high"
}

# Ventilation mode [RW]
# Only works if COMFORT_BUTTON == 1
# If COMFORT_BUTTON == 0, this register is Away.
VENTILATION_MODE = DeviceProperty('multiStateValue', 42, priority=13)
VENTILATION_MODE.STOP = 1
VENTILATION_MODE.AWAY = 2
VENTILATION_MODE.HOME = 3
VENTILATION_MODE.HIGH = 4
VENTILATION_MODES = {
    VENTILATION_MODE.STOP: "Stop",
    VENTILATION_MODE.AWAY: "Away",
    VENTILATION_MODE.HOME: "Home",
    VENTILATION_MODE.HIGH: "High",
}

# Air temp., setpoint AWAY (e.g. 18.0 degreesCelsius)
AIR_TEMP_SETPOINT_AWAY = DeviceProperty('analogValue', 1985)

# Air temp., setpoint HOME (e.g. 19.0 degreesCelsius)
AIR_TEMP_SETPOINT_HOME = DeviceProperty('analogValue', 1994)

# Trigger temporary fireplace ventilation
FIREPLACE_VENTILATION = DeviceProperty('multiStateValue', 360)
FIREPLACE_VENTILATION.TRIGGER = 2

# Fireplace ventilation runtime (e.g. 10 minutes)
FIREPLACE_VENTILATION_RUNTIME = DeviceProperty('positiveIntegerValue', 270)

# Fireplace ventilation remaining time in minutes
FIREPLACE_VENTILATION_REMAINING_DURATION = DeviceProperty('analogValue', 2038)

# Trigger temporary rapid ventilation
RAPID_VENTILATION = DeviceProperty('multiStateValue', 357)
RAPID_VENTILATION.TRIGGER = 2

# Rapid ventilation runtime (e.g. 10 minutes)
RAPID_VENTILATION_RUNTIME = DeviceProperty('positiveIntegerValue', 293)

# Rapid ventilation remaining time in minutes
RAPID_VENTILATION_REMAINING_DURATION = DeviceProperty('analogValue', 2031)

# Outside air temperature (e.g. 10.680000305175781 degreesCelsius)
OUTSIDE_AIR_TEMPERATURE = DeviceProperty('analogInput', 1)

# Supply air temperature (e.g. 18.809999465942383 degreesCelsius)
SUPPLY_AIR_TEMPERATURE = DeviceProperty('analogInput', 4)

# Tacho, supply fan (e.g. 3120.0 revolutionsPerMinute)
TACHO_SUPPLY_FAN = DeviceProperty('analogInput', 5)

# Exhaust air temperature (e.g. 14.770000457763672 degreesCelsius)
EXHAUST_AIR_TEMPERATURE = DeviceProperty('analogInput', 11)

# Tacho, exhaust fan (e.g. 3090.0 revolutionsPerMinute)
TACHO_EXHAUST_FAN = DeviceProperty('analogInput', 12)

# Extract air temperature (e.g. 21.5 degreesCelsius)
EXTRACT_AIR_TEMPERATURE = DeviceProperty('analogInput', 59)

# Room temperature (e.g. 22.200000762939453 degreesCelsius)
ROOM_TEMPERATURE = DeviceProperty('analogInput', 75)

# Fan speed, supply air (e.g. 70.0 percent)
FAN_SPEED_SUPPLY_AIR = DeviceProperty('analogOutput', 3)

# Fan speed, exhaust air (e.g. 70.0 percent)
FAN_SPEED_EXHAUST_AIR = DeviceProperty('analogOutput', 4)

# Rotating heat exchanger (e.g. 55.41521453857422 percent)
ROTATING_HEAT_EXCHANGER_SPEED = DeviceProperty('analogOutput', 0)

# Rotating heat exchanger, efficiency (e.g. 61.461185455322266 percent)
ROTATING_HEAT_EXCHANGER_EFFICIENCY = DeviceProperty('analogValue', 2023)

# Electrical heater, OFF/ON (e.g. inactive)
ELECTRICAL_HEATER = DeviceProperty('binaryValue', 445)
ELECTRICAL_HEATER.ACTIVE = 'active'
ELECTRICAL_HEATER.INACTIVE = 'inactive'

# Electric heater, nom. Power (e.g. 0.800000011920929 kilowatts)
ELECTRIC_HEATER_NOM_POWER = DeviceProperty('analogValue', 190)

# Heating coil electric power (e.g. 0.0 kilowatts)
HEATING_COIL_ELECTRIC_POWER = DeviceProperty('analogValue', 194)

# Cooker hood, activate (e.g. inactive)
COOKER_HOOD = DeviceProperty('binaryValue', 402, priority=13)
COOKER_HOOD.ACTIVE = 'active'
COOKER_HOOD.INACTIVE = 'inactive'

# Linear, setpoint supply air HIGH (e.g. 100.0 percent)
LINEAR_SETPOINT_SUPPLY_AIR_HIGH = DeviceProperty('analogValue', 1835)

# Linear, setpoint supply air HOME (e.g. 70.0 percent)
LINEAR_SETPOINT_SUPPLY_AIR_HOME = DeviceProperty('analogValue', 1836)

# Linear, setpoint supply air AWAY (e.g. 50.0 percent)
LINEAR_SETPOINT_SUPPLY_AIR_AWAY = DeviceProperty('analogValue', 1837)

# Linear, setpoint supply air FIRE (e.g. 90.0 percent)
LINEAR_SETPOINT_SUPPLY_AIR_FIRE = DeviceProperty('analogValue', 1838)

# Linear, setpoint supply air COOKER (e.g. 90.0 percent)
LINEAR_SETPOINT_SUPPLY_AIR_COOKER = DeviceProperty('analogValue', 1839)

# Linear, setpoint exhaust air HIGH (e.g. 100.0 percent)
LINEAR_SETPOINT_EXHAUST_AIR_HIGH = DeviceProperty('analogValue', 1840)

# Linear, setpoint exhaust air HOME (e.g. 70.0 percent)
LINEAR_SETPOINT_EXHAUST_AIR_HOME = DeviceProperty('analogValue', 1841)

# Linear, setpoint exhaust air AWAY (e.g. 50.0 percent)
LINEAR_SETPOINT_EXHAUST_AIR_AWAY = DeviceProperty('analogValue', 1842)

# Linear, setpoint exhaust air FIRE (e.g. 50.0 percent)
LINEAR_SETPOINT_EXHAUST_AIR_FIRE = DeviceProperty('analogValue', 1843)

# Linear, setpoint exhaust air COOKER (e.g. 50.0 percent)
LINEAR_SETPOINT_EXHAUST_AIR_COOKER = DeviceProperty('analogValue', 1844)

# Air filter, operating time (e.g. 0.0 hours)
AIR_FILTER_OPERATING_TIME = DeviceProperty('analogValue', 285)

# Air filter, time period for exchange (e.g. 4380.0 hours)
AIR_FILTER_TIME_PERIOD_FOR_EXCHANGE = DeviceProperty('analogValue', 286)

# Air filter polluted (e.g. inactive)
AIR_FILTER_POLLUTED = DeviceProperty('binaryValue', 522)
AIR_FILTER_POLLUTED.ACTIVE = 'active'

# Air filter replace timer reset (e.g. 1 None)
AIR_FILTER_REPLACE_TIMER_RESET = DeviceProperty('multiStateValue', 613)
AIR_FILTER_REPLACE_TIMER_RESET.TRIGGER = 2

# List of all DeviceProperties defined in this file
DEVICE_PROPERTIES = [
    item
    for _, item
    in globals().items()
    if isinstance(item, DeviceProperty)
]
