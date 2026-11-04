"""Flexit Nordic series config.

Based on https://www.flexit.no/globalassets/catalog/documents/bacnet-nordic-basic_2963.xlsx
"""
from .bacnet import DeviceProperty, ObjectType

PRODUCT_LINE = "Nordic"

# Comfort button [RW]
# 0 = Ventilation mode Away after Away delay timer duration [Pintval,318].
#     Also overrides Room operating mode PRESENT_VENTILATION_MODE.
# 1 = Ventilation mode according to Room operating mode PRESENT_VENTILATION_MODE.
COMFORT_BUTTON = DeviceProperty(ObjectType.BINARY_VALUE, 50, priority=13, object_name="R(1)'ROpModDtr'CmfBtn")
COMFORT_BUTTON_ACTIVE = 1
COMFORT_BUTTON_INACTIVE = 0

# Sets the delay time in minutes for Comfort button
COMFORT_BUTTON_DELAY = DeviceProperty(ObjectType.POSITIVE_INTEGER_VALUE, 318, object_name="R(1)'ROpModDtr'DlyOnAway")

# Heat recovery ventilation state
OPERATION_MODE = DeviceProperty(ObjectType.MULTI_STATE_VALUE, 361, object_name="R(1)'ROpModDtr'HrvSta")
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
VENTILATION_MODE = DeviceProperty(ObjectType.MULTI_STATE_VALUE, 42, priority=13, object_name="R(1)'ROpModDtr'ROpMod")
VENTILATION_MODE_STOP = 1
VENTILATION_MODE_AWAY = 2
VENTILATION_MODE_HOME = 3
VENTILATION_MODE_HIGH = 4

# Air temp., setpoint AWAY (e.g. 18.0 degreesCelsius)
AIR_TEMP_SETPOINT_AWAY = DeviceProperty(ObjectType.ANALOG_VALUE, 1985, object_name="R(1)'RHvacCoo'TCtlH'SpTAway")

# Air temp., setpoint HOME (e.g. 19.0 degreesCelsius)
AIR_TEMP_SETPOINT_HOME = DeviceProperty(ObjectType.ANALOG_VALUE, 1994, object_name="R(1)'RHvacCoo'TCtlH'SpTHome")

# Trigger temporary fireplace ventilation
FIREPLACE_VENTILATION = DeviceProperty(ObjectType.MULTI_STATE_VALUE, 360, object_name="R(1)'RHvacCoo'FplcVntOp'TmpFplcVntTrg")
FIREPLACE_VENTILATION_TRIGGER = 2

# Fireplace ventilation runtime (e.g. 10 minutes)
FIREPLACE_VENTILATION_RUNTIME = DeviceProperty(ObjectType.POSITIVE_INTEGER_VALUE, 270, object_name="R(1)'RHvacCoo'FplcVntOp'TiRnFplcVnt")

# Fireplace ventilation remaining time in minutes
FIREPLACE_VENTILATION_REMAINING_DURATION = DeviceProperty(ObjectType.ANALOG_VALUE, 2038, object_name="R(1)'RHvacCoo'FplcVntOp'TiRmgFplcVnt")

# Fireplace status
FIREPLACE_STATE = DeviceProperty(ObjectType.BINARY_VALUE, 400, object_name="R(1)'RHvacCoo'FplcVntOp'FplcVnt")
FIREPLACE_STATE_ACTIVE = 1
FIREPLACE_STATE_INACTIVE = 0

# Trigger temporary rapid ventilation
RAPID_VENTILATION = DeviceProperty(ObjectType.MULTI_STATE_VALUE, 357, object_name="R(1)'RHvacCoo'RpdVntOp'TmpRpdVntTrg")
RAPID_VENTILATION_TRIGGER = 2

# Rapid ventilation runtime (e.g. 10 minutes)
RAPID_VENTILATION_RUNTIME = DeviceProperty(ObjectType.POSITIVE_INTEGER_VALUE, 293, object_name="R(1)'RHvacCoo'RpdVntOp'TiRnRpdVnt")

# Rapid ventilation remaining time in minutes
RAPID_VENTILATION_REMAINING_DURATION = DeviceProperty(ObjectType.ANALOG_VALUE, 2031, object_name="R(1)'RHvacCoo'RpdVntOp'TiRmgRpdVnt")

# Outside air temperature (e.g. 10.680000305175781 degreesCelsius)
OUTSIDE_AIR_TEMPERATURE = DeviceProperty(ObjectType.ANALOG_INPUT, 1, object_name="R(1)'TOa")

# Supply air temperature (e.g. 18.809999465942383 degreesCelsius)
SUPPLY_AIR_TEMPERATURE = DeviceProperty(ObjectType.ANALOG_INPUT, 4, object_name="R(1)'TSu")

# Tacho, supply fan (e.g. 3120.0 revolutionsPerMinute)
TACHO_SUPPLY_FAN = DeviceProperty(ObjectType.ANALOG_INPUT, 5, object_name="R(1)'FanSuSpdFb")

# Exhaust air temperature (e.g. 14.770000457763672 degreesCelsius)
EXHAUST_AIR_TEMPERATURE = DeviceProperty(ObjectType.ANALOG_INPUT, 11, object_name="R(1)'TEh")

# Tacho, exhaust fan (e.g. 3090.0 revolutionsPerMinute)
TACHO_EXHAUST_FAN = DeviceProperty(ObjectType.ANALOG_INPUT, 12, object_name="R(1)'FanEhSpdFb")

# Extract air temperature (e.g. 21.5 degreesCelsius)
EXTRACT_AIR_TEMPERATURE = DeviceProperty(ObjectType.ANALOG_INPUT, 59, object_name="R(1)'TEx")
EXTRACT_AIR_TEMPERATURE_ALT = DeviceProperty(ObjectType.ANALOG_INPUT, 95)

# Room temperature (e.g. 22.200000762939453 degreesCelsius)
ROOM_TEMPERATURE = DeviceProperty(ObjectType.ANALOG_INPUT, 75, object_name="R(1)'ROpUnDev'TR")

# Fan speed, supply air (e.g. 70.0 percent)
FAN_SPEED_SUPPLY_AIR = DeviceProperty(ObjectType.ANALOG_OUTPUT, 3, object_name="R(1)'FanSuSpd")

# Fan speed, exhaust air (e.g. 70.0 percent)
FAN_SPEED_EXHAUST_AIR = DeviceProperty(ObjectType.ANALOG_OUTPUT, 4, object_name="R(1)'FanEhSpd")

# Rotating heat exchanger (e.g. 55.41521453857422 percent)
ROTATING_HEAT_EXCHANGER_SPEED = DeviceProperty(ObjectType.ANALOG_OUTPUT, 0, object_name="R(1)'RotHExgSpd")

# Rotating heat exchanger, efficiency (e.g. 61.461185455322266 percent)
ROTATING_HEAT_EXCHANGER_EFFICIENCY = DeviceProperty(ObjectType.ANALOG_VALUE, 2023, object_name="R(1)'HVAC'Erc'PrHExgEfcy")

# Electrical heater, OFF/ON (e.g. inactive)
ELECTRICAL_HEATER = DeviceProperty(ObjectType.BINARY_VALUE, 445, object_name="R(1)'HVAC'Hcl'EnHclEl")
ELECTRICAL_HEATER_ACTIVE = 1
ELECTRICAL_HEATER_INACTIVE = 0

# Electric heater, nom. Power (e.g. 0.800000011920929 kilowatts)
ELECTRIC_HEATER_NOM_POWER = DeviceProperty(ObjectType.ANALOG_VALUE, 190, object_name="R(1)'HVAC'Hcl'NomElPwr")

# Heating coil electric power (e.g. 0.0 kilowatts)
HEATING_COIL_ELECTRIC_POWER = DeviceProperty(ObjectType.ANALOG_VALUE, 194, object_name="R(1)'HVAC'Hcl'HclElPwr")

# Cooker hood, activate (e.g. inactive)
COOKER_HOOD = DeviceProperty(ObjectType.BINARY_VALUE, 402, priority=13, object_name="R(1)'RHvacCoo'FhVntOp'FhVnt")
COOKER_HOOD_ACTIVE = 1
COOKER_HOOD_INACTIVE = 0

# Linear, setpoint supply air HIGH (e.g. 100.0 percent)
LINEAR_SETPOINT_SUPPLY_AIR_HIGH = DeviceProperty(ObjectType.ANALOG_VALUE, 1835, object_name="R(1)'RHvacCoo'VntCtl'SpFanSuSpdHi")

# Linear, setpoint supply air HOME (e.g. 70.0 percent)
LINEAR_SETPOINT_SUPPLY_AIR_HOME = DeviceProperty(ObjectType.ANALOG_VALUE, 1836, object_name="R(1)'RHvacCoo'VntCtl'SpFanSuSpdHome")

# Linear, setpoint supply air AWAY (e.g. 50.0 percent)
LINEAR_SETPOINT_SUPPLY_AIR_AWAY = DeviceProperty(ObjectType.ANALOG_VALUE, 1837, object_name="R(1)'RHvacCoo'VntCtl'SpFanSuSpdAway")

# Linear, setpoint supply air FIRE (e.g. 90.0 percent)
LINEAR_SETPOINT_SUPPLY_AIR_FIRE = DeviceProperty(ObjectType.ANALOG_VALUE, 1838, object_name="R(1)'RHvacCoo'VntCtl'SpFanSuSpdFplc")

# Linear, setpoint supply air COOKER (e.g. 90.0 percent)
LINEAR_SETPOINT_SUPPLY_AIR_COOKER = DeviceProperty(ObjectType.ANALOG_VALUE, 1839, object_name="R(1)'RHvacCoo'VntCtl'SpFanSuSpdCkr")

# Linear, setpoint exhaust air HIGH (e.g. 100.0 percent)
LINEAR_SETPOINT_EXHAUST_AIR_HIGH = DeviceProperty(ObjectType.ANALOG_VALUE, 1840, object_name="R(1)'RHvacCoo'VntCtl'SpFanEhSpdHi")

# Linear, setpoint exhaust air HOME (e.g. 70.0 percent)
LINEAR_SETPOINT_EXHAUST_AIR_HOME = DeviceProperty(ObjectType.ANALOG_VALUE, 1841, object_name="R(1)'RHvacCoo'VntCtl'SpFanEhSpdHome")

# Linear, setpoint exhaust air AWAY (e.g. 50.0 percent)
LINEAR_SETPOINT_EXHAUST_AIR_AWAY = DeviceProperty(ObjectType.ANALOG_VALUE, 1842, object_name="R(1)'RHvacCoo'VntCtl'SpFanEhSpdAway")

# Linear, setpoint exhaust air FIRE (e.g. 50.0 percent)
LINEAR_SETPOINT_EXHAUST_AIR_FIRE = DeviceProperty(ObjectType.ANALOG_VALUE, 1843, object_name="R(1)'RHvacCoo'VntCtl'SpFanEhSpdFplc")

# Linear, setpoint exhaust air COOKER (e.g. 50.0 percent)
LINEAR_SETPOINT_EXHAUST_AIR_COOKER = DeviceProperty(ObjectType.ANALOG_VALUE, 1844, object_name="R(1)'RHvacCoo'VntCtl'SpFanEhSpdCkr")

# Air filter, operating time (e.g. 0.0 hours)
AIR_FILTER_OPERATING_TIME = DeviceProperty(ObjectType.ANALOG_VALUE, 285, object_name="R(1)'HVAC'AlmBdl'TiOpFil")

# Air filter, time period for exchange (e.g. 4380.0 hours)
AIR_FILTER_TIME_PERIOD_FOR_EXCHANGE = DeviceProperty(ObjectType.ANALOG_VALUE, 286, object_name="R(1)'HVAC'AlmBdl'TiOpFilRpc")

# Air filter polluted (e.g. inactive)
AIR_FILTER_POLLUTED = DeviceProperty(ObjectType.BINARY_VALUE, 522, object_name="R(1)'HVAC'AlmBdl'Alm1020")
AIR_FILTER_POLLUTED_ACTIVE = 1

# Air filter replace timer reset (e.g. 1 None)
AIR_FILTER_REPLACE_TIMER_RESET = DeviceProperty(ObjectType.MULTI_STATE_VALUE, 613, object_name="R(1)'HVAC'AlmBdl'FilRpcRst")
AIR_FILTER_REPLACE_TIMER_RESET_TRIGGER = 2

# Humidity sensors
EXTRACT_AIR_HUMIDITY = DeviceProperty(ObjectType.ANALOG_INPUT, 96, object_name="R(1)'HuRelEx")  # available on some models
ROOM_1_HUMIDITY = DeviceProperty(ObjectType.ANALOG_VALUE, 2093, object_name="R(1)'Modbus'RfqSysFnct'HuR1")
ROOM_2_HUMIDITY = DeviceProperty(ObjectType.ANALOG_VALUE, 2094, object_name="R(1)'Modbus'RfqSysFnct'HuR2")
ROOM_3_HUMIDITY = DeviceProperty(ObjectType.ANALOG_VALUE, 2095, object_name="R(1)'Modbus'RfqSysFnct'HuR3")

# Maximum room air humidity over the wireless (RF) room sensors - the humidity
# Flexit GO shows on its home screen (e.g. 62.0 percent, 0.0 without RF sensors)
ROOM_HUMIDITY_MAX = DeviceProperty(ObjectType.ANALOG_INPUT, 81, object_name="R(1)'FanNodeDev'HuRMaxRfqs")

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
FREE_COOLING_ENABLED = DeviceProperty(ObjectType.BINARY_VALUE, 478, priority=13, object_name="R(1)'RHvacCoo'FreeCDtr'EnFreeC")
FREE_COOLING_ENABLED_ACTIVE = 1
FREE_COOLING_ENABLED_INACTIVE = 0

# Extract temp setpoint (e.g. 22.0 degreesCelsius, range 10 - 30)
FREE_COOLING_EXTRACT_TEMP_SETPOINT = DeviceProperty(ObjectType.ANALOG_VALUE, 2071, object_name="R(1)'RHvacCoo'TCtlH'SpTRFreeC")

# Outside temp limit - free cooling is not used below this outdoor temperature
# (e.g. 18.0 degreesCelsius, range 10 - 30)
FREE_COOLING_OUTSIDE_TEMP_LIMIT = DeviceProperty(ObjectType.ANALOG_VALUE, 1934, object_name="R(1)'RHvacCoo'FreeCDtr'TOaLm")

# DT B3-B4: extract air (B3) minus outdoor air (B4) in K (range 0 - 10)
FREE_COOLING_DT_ENABLE_START = DeviceProperty(ObjectType.ANALOG_VALUE, 1936, object_name="R(1)'RHvacCoo'FreeCDtr'DiffTRTOaSwiOn")
FREE_COOLING_DT_DISABLE = DeviceProperty(ObjectType.ANALOG_VALUE, 1937, object_name="R(1)'RHvacCoo'FreeCDtr'DiffTRTOaSwiOf")

# Plant state (read-only) - what the ventilation plant is doing right now.
# PLANT_STATE_FREE_COOLING is the only way to see that free cooling is running;
# FREE_COOLING_ENABLED only says that it is allowed to.
# Not present on every unit: a Nordic S4 and a CL4 (HvacFnct21y_A v2.425) answer
# unknown-object; free_cooling_active then uses PRESENT_PLANT_OPERATING_MODE below.
PLANT_STATE = DeviceProperty(ObjectType.MULTI_STATE_VALUE, 623, object_name="R(1)'HVAC'PltSta")
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

# Present plant operating mode (read-only) - the Siemens plant mode in effect
# (R(1)'HVAC'PrPltOpMod). Units without PLANT_STATE (e.g. a Nordic CL4 with
# HvacFnct21y_A v2.425) report running free cooling here instead.
PRESENT_PLANT_OPERATING_MODE = DeviceProperty(ObjectType.MULTI_STATE_VALUE, 19, object_name="R(1)'HVAC'PrPltOpMod")
PLANT_OPERATING_MODE_OFF = 1
PLANT_OPERATING_MODE_PROTECTION = 2
PLANT_OPERATING_MODE_ECONOMY = 3
PLANT_OPERATING_MODE_PRE_COMFORT = 4
PLANT_OPERATING_MODE_COMFORT = 5
PLANT_OPERATING_MODE_WARM_UP = 6
PLANT_OPERATING_MODE_COOL_DOWN = 7
PLANT_OPERATING_MODE_ROOM_LOW_TEMPERATURE_PROTECTION = 8
PLANT_OPERATING_MODE_CONDENSATION_OVERFLOW_PROTECTION = 9
PLANT_OPERATING_MODE_FREE_COOLING = 10
PLANT_OPERATING_MODE_NIGHT_COOLING = 11
PLANT_OPERATING_MODE_VENTILATION = 12
PLANT_OPERATING_MODE_EQUIPMENT_TEMPERATURE_PROTECTION = 13
PLANT_OPERATING_MODE_AIR_VOLUME_FLOW_OFF = 14
PLANT_OPERATING_MODE_SMOKE_EXTRACTION_POSITIVE_PRESSURE = 15
PLANT_OPERATING_MODE_SMOKE_EXTRACTION_NEGATIVE_PRESSURE = 16
PLANT_OPERATING_MODE_PURGE = 17

# EcoNordic-only objects (domestic hot water, heat pump, space heating): Nordic
# units have none of them, so their getters read None and writing raises.
DHW_OPERATION_MODE = None
DHW_TEMPORARY_BOOST = None
DHW_FORCED_CHARGE = None
DHW_STATE = None
DHW_TEMPERATURE_SETPOINT_COMFORT = None
DHW_TEMPERATURE_SETPOINT_ECONOMY = None
DHW_TANK_TEMPERATURE_BOTTOM = None
DHW_TANK_TEMPERATURE_MIDDLE = None
DHW_TANK_TEMPERATURE_TOP = None
DHW_ELECTRIC_HEATER_STATUS = None
HEATING_CIRCUIT_1_ROOM_TEMPERATURE_SETPOINT = None
HEAT_PUMP_STATE = None

# Humidity (dehumidification) control - increases fan speed on high or rapidly rising humidity.
# Objects verified on Nordic S7 (POS3.67, application HvacFnct21y_A v2.438).

# Humidity, present setpoint (e.g. 70.0 percent)
HUMIDITY_SETPOINT_PRESENT = DeviceProperty(ObjectType.ANALOG_VALUE, 60, object_name="R(1)'RHvacCoo'DhuCtl'PrSpDhu")

# Humidity, setpoint HIGH (e.g. 100.0 percent)
HUMIDITY_SETPOINT_HIGH = DeviceProperty(ObjectType.ANALOG_VALUE, 61, object_name="R(1)'RHvacCoo'DhuCtl'SpHuRelRCmf")

# Humidity, setpoint HOME (e.g. 70.0 percent)
HUMIDITY_SETPOINT_HOME = DeviceProperty(ObjectType.ANALOG_VALUE, 62, object_name="R(1)'RHvacCoo'DhuCtl'SpHuRelRPcf")

# Humidity, setpoint AWAY (e.g. 80.0 percent)
HUMIDITY_SETPOINT_AWAY = DeviceProperty(ObjectType.ANALOG_VALUE, 63, object_name="R(1)'RHvacCoo'DhuCtl'SpHuRelREco")

# Humidity, present fan control - fan speed request caused by humidity (e.g. 0.0 percent)
DEHUMIDIFICATION_FAN_CONTROL = DeviceProperty(ObjectType.ANALOG_VALUE, 1870, object_name="R(1)'HVAC'FanSu'FanDhuReq")

# Dehumidification enable PID control (setpoint based) (e.g. active)
DEHUMIDIFICATION_PID_CONTROL = DeviceProperty(ObjectType.BINARY_VALUE, 591)
DEHUMIDIFICATION_PID_CONTROL_ACTIVE = 1
DEHUMIDIFICATION_PID_CONTROL_INACTIVE = 0

# Dehumidification enable slope control - reacts to rapidly rising humidity, e.g. a shower (e.g. 2)
DEHUMIDIFICATION_SLOPE_CONTROL = DeviceProperty(ObjectType.MULTI_STATE_VALUE, 620, object_name="R(1)'RHvacCoo'DhuCtl'DhuEnSlpCtl")
DEHUMIDIFICATION_SLOPE_CONTROL_DISABLED = 1
DEHUMIDIFICATION_SLOPE_CONTROL_EXTRACT_AIR = 2
DEHUMIDIFICATION_SLOPE_CONTROL_ROOM_MAX = 3

# Dehumidification slope switch-on point (e.g. 1.0)
DEHUMIDIFICATION_SLOPE_SWITCH_ON = DeviceProperty(ObjectType.ANALOG_VALUE, 2295, object_name="R(1)'RHvacCoo'DhuCtl'DhuPosTrig")

# Dehumidification slope switch-off point (e.g. -0.3)
DEHUMIDIFICATION_SLOPE_SWITCH_OFF = DeviceProperty(ObjectType.ANALOG_VALUE, 2292, object_name="R(1)'RHvacCoo'DhuCtl'DhuNegTrig")

# Dehumidification calculated slope (e.g. 0.0)
DEHUMIDIFICATION_SLOPE = DeviceProperty(ObjectType.ANALOG_VALUE, 2308, object_name="R(1)'RHvacCoo'DhuCtl'DhuSlopeResVal")

# Dehumidification request is caused by slope (e.g. inactive)
DEHUMIDIFICATION_BY_SLOPE = DeviceProperty(ObjectType.BINARY_VALUE, 653)
DEHUMIDIFICATION_BY_SLOPE_ACTIVE = 1

# Dehumidification slope resolution (e.g. 5 minutes)
DEHUMIDIFICATION_SLOPE_RESOLUTION = DeviceProperty(ObjectType.POSITIVE_INTEGER_VALUE, 261, object_name="R(1)'RHvacCoo'DhuCtl'DhuSlopeRes")

# On delay for slope control (e.g. 600 seconds)
DEHUMIDIFICATION_SLOPE_ON_DELAY = DeviceProperty(ObjectType.POSITIVE_INTEGER_VALUE, 1229)

# Dehumidification switch-off delay (e.g. 30 minutes)
DEHUMIDIFICATION_SWITCH_OFF_DELAY = DeviceProperty(ObjectType.POSITIVE_INTEGER_VALUE, 262, object_name="R(1)'RHvacCoo'DhuCtl'DhuEndRunTi")

# Dehumidification maximum runtime (e.g. 120 minutes)
DEHUMIDIFICATION_MAX_RUNTIME = DeviceProperty(ObjectType.POSITIVE_INTEGER_VALUE, 263, object_name="R(1)'RHvacCoo'DhuCtl'DhuMaxRunTi")

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
    800140: "S7 RER",
    800141: "S7 REL",
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
