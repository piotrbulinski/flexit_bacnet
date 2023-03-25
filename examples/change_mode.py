import asyncio
import sys

# import FlexitBACnet
from flexit_bacnet import (
    FlexitBACnet,
    VENTILATION_MODE_AWAY,
    VENTILATION_MODE_HOME,
    VENTILATION_MODES,
)


async def main():
    if len(sys.argv) < 2:
        print(f"usage ./{sys.argv[0]} <flexit-unit-ip-address>")
        exit()

    device_address = sys.argv[1]

    # create a FlexitBACnet device instance with the IP address and Device ID
    device = FlexitBACnet(device_address, 2)

    await device.update()

    # check whether device address and ID are correct
    if not device.is_valid():
        raise Exception("not a valid device")

    print(f"Comfort button: {device.comfort_button}")
    print(f"Operation mode: {device.operation_mode}")
    print(f"Ventilation mode (before): {device.ventilation_mode}")

    # check current ventilation mode and toggle it between HOME & AWAY
    if device.ventilation_mode == VENTILATION_MODES[VENTILATION_MODE_HOME]:
        await device.set_ventilation_mode(VENTILATION_MODE_AWAY)
    elif device.ventilation_mode == VENTILATION_MODES[VENTILATION_MODE_AWAY]:
        await device.set_ventilation_mode(VENTILATION_MODE_HOME)
    else:
        print("This example toggles only between Home and Away modes.")

    print(f"Ventilation mode (after):  {device.ventilation_mode}")


if __name__ == "__main__":
    asyncio.run(main())
