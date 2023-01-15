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

## Install this python package

In order to use this package you need to first clone the repo and run `python3 -m pip install .`

You need to have Python version 3.10 or above.

## Connecting to a device

```python
# import FlexitBACnet
from flexit_bacnet import FlexitBACnet

if __name__ == '__main__':
    # create a FlexitBACnet device instance with the IP address and Device ID
    device = FlexitBACnet('192.168.0.18', 2)

    # check whether device address and ID are correct
    if not device.is_valid():
        raise Exception('not a valid device')

    # check device name and s/n
    print('Device Name:', device.device_name)
    print('Serial Number:', device.serial_number)
```

## Interacting with the device

For list of available states and interactions, please study [device.py](./flexit_bacnet/device.py).

For example, changing ventilation mode can be done as follows:

```python
# import FlexitBACnet
from flexit_bacnet import (
    FlexitBACnet,
    VENTILATION_MODE,
)

if __name__ == '__main__':
    # create a FlexitBACnet device instance with the IP address and Device ID
    device = FlexitBACnet('192.168.0.18', 2)

    # check current ventilation mode
    print('ventilation mode (before):', device.ventilation_mode)

    # set ventilation mode to High
    device.set_ventilation_mode(VENTILATION_MODE.HIGH)

    # check current ventilation mode again
    print('ventilation mode (after):', device.ventilation_mode)
```

Which would result in the following output:

```text
ventilation mode (before): Home
ventilation mode (after): High
```