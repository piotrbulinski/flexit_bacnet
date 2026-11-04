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

    # every value property comes with a label and a unit;
    # values the unit does not support are shown as "(unsupported)"
    for info in FlexitBACnet.readings():
        print(f"{info.label}: {info.format(getattr(device, info.name))}")


if __name__ == "__main__":
    asyncio.run(main())
