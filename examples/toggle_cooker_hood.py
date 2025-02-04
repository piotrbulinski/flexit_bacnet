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

    if device.cooker_hood_status:
        print("cooker hood on, deactivating...")
        await device.deactivate_cooker_hood()
    else:
        print("cooker hood off, activating")
        await device.activate_cooker_hood()

    await device.update()

    if device.cooker_hood_status:
        print("cooker hood status: on")
    else:
        print("cooker hood status: off")


if __name__ == "__main__":
    asyncio.run(main())
