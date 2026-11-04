import asyncio
import sys
from typing import Any

# import FlexitBACnet
from flexit_bacnet import FlexitBACnet


def show(value: Any, unit: str = "") -> str:
    """Format a property value with its unit.

    Getters return None when the unit does not have the underlying object.
    """
    if value is None:
        return "(unsupported)"

    return f"{value}{unit}"


async def main():
    if len(sys.argv) < 2:
        print(f"usage ./{sys.argv[0]} <flexit-unit-ip-address>")
        exit()

    device_address = sys.argv[1]

    # create a FlexitBACnet device instance with the IP address and Device ID
    device = FlexitBACnet(device_address, 2)

    await device.update()

    # check device name and s/n
    print(f"Device Name: {device.device_name}")
    print(f"Serial Number: {device.serial_number}")
    print(f"Device Model: {device.model}")
    print(f"Outside air temp.: {show(device.outside_air_temperature, ' °C')}")
    print(f"Supply air temp.: {show(device.supply_air_temperature, ' °C')}")
    print(f"Extract air temp.: {show(device.extract_air_temperature, ' °C')}")
    print(f"Exhaust air temp.: {show(device.exhaust_air_temperature, ' °C')}")
    print(f"Room air temp.: {show(device.room_temperature, ' °C')}")
    print(f"Extract air humidity: {show(device.extract_air_humidity, '%')}")
    print(f"Room 1 humidity: {show(device.room_1_humidity, '%')}")
    print(f"Room 2 humidity: {show(device.room_2_humidity, '%')}")
    print(f"Room 3 humidity: {show(device.room_3_humidity, '%')}")
    print(f"Humidity setpoint (present/Home/Away/High): {show(device.humidity_setpoint_present, '%')}/"
          f"{show(device.humidity_setpoint_home, '%')}/{show(device.humidity_setpoint_away, '%')}/"
          f"{show(device.humidity_setpoint_high, '%')}")
    print(f"Dehumidification fan control: {show(device.dehumidification_fan_control, '%')}")
    print(f"Dehumidification PID control: {show(device.dehumidification_pid_control)}")
    print(f"Dehumidification slope control: {show(device.dehumidification_slope_control)}")
    print(f"Dehumidification slope (current/on/off): {show(device.dehumidification_slope)}/"
          f"{show(device.dehumidification_slope_switch_on)}/{show(device.dehumidification_slope_switch_off)}")
    print(f"Dehumidification by slope: {show(device.dehumidification_by_slope)}")
    print(f"Dehumidification slope resolution: {show(device.dehumidification_slope_resolution, ' minutes')}")
    print(f"Dehumidification slope on delay: {show(device.dehumidification_slope_on_delay, ' seconds')}")
    print(f"Dehumidification switch-off delay: {show(device.dehumidification_switch_off_delay, ' minutes')}")
    print(f"Dehumidification max runtime: {show(device.dehumidification_max_runtime, ' minutes')}")
    print(f"Comfort button state: {show(device.comfort_button)}")
    print(f"Operation mode: {show(device.operation_mode)}")
    print(f"Ventilation mode: {show(device.ventilation_mode)}")
    print(f"Air temp. setpoint Away: {show(device.air_temp_setpoint_away, ' °C')}")
    print(f"Air temp. setpoint Home: {show(device.air_temp_setpoint_home, ' °C')}")
    print(f"Cooker-hood status: {show(device.cooker_hood_status)}")
    print(f"Fireplace status: {show(device.fireplace_ventilation_status)}")
    print(f"Fireplace mode runtime: {show(device.fireplace_mode_runtime, ' minutes')}")
    print(
        f"Fireplace duration remaining: {show(device.fireplace_ventilation_remaining_duration, ' minutes')}"
    )
    print(
        f"Rapid ventilation duration remaining: {show(device.rapid_ventilation_remaining_duration, ' minutes')}"
    )
    print(f"Supply air fan control signal: {show(device.supply_air_fan_control_signal, '%')}")
    print(f"Supply air fan RPM: {show(device.supply_air_fan_rpm)}")
    print(f"Exhaust air fan control signal: {show(device.exhaust_air_fan_control_signal, '%')}")
    print(f"Exhaust air fan RPM: {show(device.exhaust_air_fan_rpm)}")
    print(f"Electric heater enabled: {show(device.electric_heater)}")
    print(f"Electric heater nominal power: {show(device.electric_heater_nominal_power, ' kW')}")
    print(f"Electric heater power consumption: {show(device.electric_heater_power, ' kW')}")
    print(f"Fan setpoint - supply air Home: {show(device.fan_setpoint_supply_air_home, '%')}")
    print(f"Fan setpoint - supply air Away: {show(device.fan_setpoint_supply_air_away, '%')}")
    print(f"Fan setpoint - supply air High: {show(device.fan_setpoint_supply_air_high, '%')}")
    print(f"Fan setpoint - supply air Cooker: {show(device.fan_setpoint_supply_air_cooker, '%')}")
    print(
        f"Fan setpoint - supply air Fireplace: {show(device.fan_setpoint_supply_air_fire, '%')}"
    )
    print(f"Fan setpoint - extract air Home: {show(device.fan_setpoint_extract_air_home, '%')}")
    print(f"Fan setpoint - extract air Away: {show(device.fan_setpoint_extract_air_away, '%')}")
    print(f"Fan setpoint - extract air High: {show(device.fan_setpoint_extract_air_high, '%')}")
    print(
        f"Fan setpoint - extract air Cooker: {show(device.fan_setpoint_extract_air_cooker, '%')}"
    )
    print(
        f"Fan setpoint - extract air Fireplace: {show(device.fan_setpoint_extract_air_fire, '%')}"
    )
    print(f"Air filter operating time: {show(device.air_filter_operating_time, ' hours')}")
    print(f"Air filter exchange interval: {show(device.air_filter_exchange_interval, ' days')}")
    print(f"Air filter polluted: {show(device.air_filter_polluted)}")
    print(f"Heat-exchanger efficiency: {show(device.heat_exchanger_efficiency, '%')}")
    print(f"Heat-exchanger speed: {show(device.heat_exchanger_speed, '%')}")


if __name__ == "__main__":
    asyncio.run(main())
