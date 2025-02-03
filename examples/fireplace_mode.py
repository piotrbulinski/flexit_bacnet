import asyncio
import sys

# import FlexitBACnet
from flexit_bacnet import FlexitBACnet


async def main():
    if len(sys.argv) < 3:
        print(f"usage ./{sys.argv[0]} <flexit-unit-ip-address> <duration-in-minutes>")
        exit()

    device_address = sys.argv[1]

    try:
        duration = int(sys.argv[2])
    except ValueError:
        print(f"duration-in-minutes must be a number")
        exit(1)

    # create a FlexitBACnet device instance with the IP address and Device ID
    device = FlexitBACnet(device_address, 2)

    await device.update()

    await device.start_fireplace_ventilation(duration)

    await device.update()

    if device.fireplace_ventilation_status:
        print(f"fireplace mode on for: {device.fireplace_ventilation_remaining_duration} minutes")
    else:
        print("fireplace mode off")


if __name__ == "__main__":
    asyncio.run(main())
