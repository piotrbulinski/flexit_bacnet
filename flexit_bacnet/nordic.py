"""Flexit Nordic series config.

Based on https://www.flexit.no/globalassets/catalog/documents/bacnet-nordic-basic_2963.xlsx
"""
from .bacnet import DeviceProperty, ObjectType

PRODUCT_LINE = "Nordic"

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
OPERATION_MODE_FUME_HOOD = 5 # Deprecated: use OPERATION_MODE_COOKER_HOOD instead
OPERATION_MODE_COOKER_HOOD = 5
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

# Fireplace status
FIREPLACE_STATE = DeviceProperty(ObjectType.BINARY_VALUE, 400)
FIREPLACE_STATE_ACTIVE = 1
FIREPLACE_STATE_INACTIVE = 0

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

# Free cooling
#
# Cools an overheated house by replacing warm indoor air with cooler outdoor air when the
# outdoor air is colder than the extract air (per the setpoints); the unit does this by
# running the ventilation in HIGH.
# The unit activates it when the extract air is above FREE_COOLING_EXTRACT_TEMP_SETPOINT,
# the outdoor air is above FREE_COOLING_OUTSIDE_TEMP_LIMIT and the outdoor air is more
# than FREE_COOLING_DT_ENABLE_START colder than the extract air; it stops when that
# difference drops below FREE_COOLING_DT_DISABLE (Flexit GO manual, "Additional functions").
# In Flexit GO the settings are installer-level; an end user only sees the enable flag.
# Same object identifiers on Nordic (seen in S3/S4/CL4 dumps) and EcoNordic (verified on a WH4).

# Free cooling enabled [RW] - whether the function is allowed to run
FREE_COOLING_ENABLED = DeviceProperty(ObjectType.BINARY_VALUE, 478, priority=13)
FREE_COOLING_ENABLED_ACTIVE = 1
FREE_COOLING_ENABLED_INACTIVE = 0

# Extract temp setpoint (e.g. 22.0 degreesCelsius, range 10 - 30)
FREE_COOLING_EXTRACT_TEMP_SETPOINT = DeviceProperty(ObjectType.ANALOG_VALUE, 2071)

# Outside temp limit - free cooling is not used below this outdoor temperature
# (e.g. 18.0 degreesCelsius, range 10 - 30)
FREE_COOLING_OUTSIDE_TEMP_LIMIT = DeviceProperty(ObjectType.ANALOG_VALUE, 1934)

# DT B3-B4: extract air (B3) minus outdoor air (B4) in K (range 0 - 10)
FREE_COOLING_DT_ENABLE_START = DeviceProperty(ObjectType.ANALOG_VALUE, 1936)
FREE_COOLING_DT_DISABLE = DeviceProperty(ObjectType.ANALOG_VALUE, 1937)

# Plant state (read-only) - what the ventilation plant is doing right now.
# PLANT_STATE_FREE_COOLING is the only way to see that free cooling is running;
# FREE_COOLING_ENABLED only says that it is allowed to.
PLANT_STATE = DeviceProperty(ObjectType.MULTI_STATE_VALUE, 623)
PLANT_STATE_NORMAL_OPERATION = 1
PLANT_STATE_DEICING_EXHAUST_TEMPERATURE = 2
PLANT_STATE_DEICING_ERC = 3
PLANT_STATE_AIR_QUALITY_CONTROL = 4
PLANT_STATE_DEHUMIDIFICATION_PID_CONTROL = 5
PLANT_STATE_DEHUMIDIFICATION_SLOPE_CONTROL = 6
PLANT_STATE_FREE_COOLING = 7
PLANT_STATE_DEICING_FAN = 8
PLANT_STATE_PLANT_SHUTDOWN = 9
PLANT_STATE_PLANT_STARTUP = 10
PLANT_STATE_MAINTENANCE_SHUTDOWN = 11
PLANT_STATE_A_ALARM_PROTECTION = 12
PLANT_STATE_FROST_WATER = 13
PLANT_STATE_POWER_UP_CONTROLLER = 14
PLANT_STATE_SMOKE_EXTRACT_SUPPLY_EXHAUST = 15
PLANT_STATE_SMOKE_EXTRACT_EXHAUST = 16
PLANT_STATE_SMOKE_EXTRACT_SUPPLY = 17
PLANT_STATE_EMERGENCY_OFF = 18

# List of all DeviceProperties defined in this file
DEVICE_PROPERTIES = [
    item for _, item in globals().items() if isinstance(item, DeviceProperty)
]
