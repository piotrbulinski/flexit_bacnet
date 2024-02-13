import asyncio
import sys

# import FlexitBACnet
from flexit_bacnet import FlexitBACnet


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
    print(f"Outside air temp.: {device.outside_air_temperature} °C")
    print(f"Supply air temp.: {device.supply_air_temperature} °C")
    print(f"Extract air temp.: {device.extract_air_temperature} °C")
    print(f"Exhaust air temp.: {device.exhaust_air_temperature} °C")
    print(f"Room air temp.: {device.room_temperature} °C")
    print(f"Extract air humidity: {device.extract_air_humidity}%")
    print(f"Room 1 humidity: {device.room_1_humidity}%")
    print(f"Room 2 humidity: {device.room_2_humidity}%")
    print(f"Room 3 humidity: {device.room_3_humidity}%")
    print(f"Comfort button state: {device.comfort_button}")
    print(f"Operation mode: {device.operation_mode}")
    print(f"Ventilation mode: {device.ventilation_mode}")
    print(f"Air temp. setpoint Away: {device.air_temp_setpoint_away} °C")
    print(f"Air temp. setpoint Home: {device.air_temp_setpoint_home} °C")
    print(
        f"Fireplace duration remaining: {device.fireplace_ventilation_remaining_duration} minutes"
    )
    print(
        f"Rapid ventilation duration remaining: {device.fireplace_ventilation_remaining_duration} minutes"
    )
    print(f"Supply air fan control signal: {device.supply_air_fan_control_signal}%")
    print(f"Supply air fan RPM: {device.supply_air_fan_rpm}")
    print(f"Exhaust air fan control signal: {device.exhaust_air_fan_control_signal}%")
    print(f"Exhaust air fan RPM: {device.exhaust_air_fan_rpm}")
    print(f"Electric heater enabled: {device.electric_heater}")
    print(f"Electric heater nominal power: {device.electric_heater_nominal_power} kW")
    print(f"Electric heater power consumption: {device.electric_heater_power} kW")
    print(f"Fan setpoint - supply air Home: {device.fan_setpoint_supply_air_home}%")
    print(f"Fan setpoint - supply air Away: {device.fan_setpoint_supply_air_away}%")
    print(f"Fan setpoint - supply air High: {device.fan_setpoint_supply_air_high}%")
    print(f"Fan setpoint - supply air Cooker: {device.fan_setpoint_supply_air_cooker}%")
    print(
        f"Fan setpoint - supply air Fireplace: {device.fan_setpoint_supply_air_fire}%"
    )
    print(f"Fan setpoint - extract air Home: {device.fan_setpoint_extract_air_home}%")
    print(f"Fan setpoint - extract air Away: {device.fan_setpoint_extract_air_away}%")
    print(f"Fan setpoint - extract air High: {device.fan_setpoint_extract_air_high}%")
    print(
        f"Fan setpoint - extract air Cooker: {device.fan_setpoint_extract_air_cooker}%"
    )
    print(
        f"Fan setpoint - extract air Fireplace: {device.fan_setpoint_extract_air_fire}%"
    )
    print(f"Air filter operating time: {device.air_filter_operating_time} hours")
    print(f"Air filter exchange interval: {device.air_filter_exchange_interval} days")
    print(f"Air filter polluted: {device.air_filter_polluted}")
    print(f"Heat-exchanger efficiency: {device.heat_exchanger_efficiency}%")
    print(f"Heat-exchanger speed: {device.heat_exchanger_speed}%")


if __name__ == "__main__":
    asyncio.run(main())
