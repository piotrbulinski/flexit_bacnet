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

    # check current ventilation mode
    print("ventilation mode:", device.ventilation_mode)


if __name__ == "__main__":
    asyncio.run(main())
