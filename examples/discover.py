import asyncio

# import FlexitBACnet
from flexit_bacnet import discover


async def main():
    devices = await discover()

    if not devices:
        print("No devices found")
        return

    print("Found devices:")
    for device in devices:
        print(device)


if __name__ == "__main__":
    asyncio.run(main())
