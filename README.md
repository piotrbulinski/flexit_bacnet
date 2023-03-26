# Flexit BACnet

This library allows integration with Flexit Nordic series of air handling units via BACnet protocol.

## Prerequisites

In order to use that library, you need to know the IP address and Device ID of your unit.

1. Open Flexit Go app on your mobile.
2. Use "Find product" button on tha main screen.
3. Select your device and press "Connect".
4. Enter installer code (default: 1000) and press "Login".
5. Open "More" menu -> Installer -> Communication -> BACnet settings.
6. Note down "IP address" and "Device ID".

You need to have Python version 3.7 or above.


## Connecting to a device

```python
import asyncio

# import FlexitBACnet
from flexit_bacnet import FlexitBACnet


async def main():
    # create a FlexitBACnet device instance with the IP address and Device ID
    device = FlexitBACnet('192.168.0.18', 2)

    await device.update()

    # check device name and s/n
    print('Device Name:', device.device_name)
    print('Serial Number:', device.serial_number)


if __name__ == "__main__":
    asyncio.run(main())
```

## Interacting with the device

For list of available states and interactions, please study [device.py](./flexit_bacnet/device.py).

For example, changing ventilation mode can be done as follows:

```python
import asyncio

# import FlexitBACnet
from flexit_bacnet import (
    FlexitBACnet,
    VENTILATION_MODE_HIGH
)


async def main():
    # create a FlexitBACnet device instance with the IP address and Device ID
    device = FlexitBACnet('192.168.0.18', 2)

    await device.update()

    # check current ventilation mode
    print('ventilation mode (before):', device.ventilation_mode)

    # set ventilation mode to High
    await device.set_ventilation_mode(VENTILATION_MODE_HIGH)

    # check current ventilation mode again
    print('ventilation mode (after):', device.ventilation_mode)


if __name__ == "__main__":
    asyncio.run(main())
```

Which would result in the following output:

```text
ventilation mode (before): 3
ventilation mode (after): 2
```


## Examples

To execute examples without installing the package, set PYTHONPATH to local directory, e.g.:

```bash
PYTHONPATH=. python3 examples/current_mode.py 192.168.0.100
```

Where 192.168.0.100 should be replaced with your unit's IP address.