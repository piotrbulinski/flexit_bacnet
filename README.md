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


## Free cooling

Free cooling cools an overheated house by replacing warm indoor air with cooler outdoor air
when the outdoor air is colder than the extract air, according to the setpoints below. The
unit does this by running the ventilation in HIGH - no cooling component is involved. It
starts when all three hold:

- the extract air is above `free_cooling_extract_temp_setpoint` (the room is too warm),
- the outdoor air is above `free_cooling_outside_temp_limit` (not cold enough to be uncomfortable),
- the outdoor air is at least `free_cooling_dt_enable_start` K colder than the extract air (cooling is possible).

It stops when the extract air drops below the setpoint or the difference falls below
`free_cooling_dt_disable`, and never before the minimum on time configured in Flexit GO
(that one is not readable over BACnet).

Two flags are easy to confuse: `free_cooling_enabled` is the on/off an end user sees in
Flexit GO and only says the function is *allowed* to run; `free_cooling_active` (derived from
`plant_state`) says it *is* running right now - which is what explains a unit that is suddenly
in HIGH with cold supply air.

The settings are installer-level in Flexit GO (local login required). With the factory
defaults (setpoint 22 °C, outside limit 18 °C, start 4 K / stop 1 K) the function rarely runs
in a Nordic climate, because the outdoor air is seldom both above 18 °C and 4 K colder than
the room. A combination that runs regularly on a unit in Sweden is outside limit 10 °C,
start 2.5 K, stop 1.5 K and a setpoint around 22-23 °C. Keep `dt_enable_start` larger than
`dt_disable`, or the function will flap.

```python
import asyncio

from flexit_bacnet import FlexitBACnet


async def main():
    device = FlexitBACnet('192.168.0.18', 2)
    await device.update()

    print('free cooling enabled:', device.free_cooling_enabled)
    print('free cooling active :', device.free_cooling_active)
    print('setpoint / outside limit / start / stop:',
          device.free_cooling_extract_temp_setpoint,
          device.free_cooling_outside_temp_limit,
          device.free_cooling_dt_enable_start,
          device.free_cooling_dt_disable)


if __name__ == "__main__":
    asyncio.run(main())
```

## Examples

To execute examples without installing the package, set PYTHONPATH to local directory, e.g.:

```bash
PYTHONPATH=. python3 examples/current_mode.py 192.168.0.100
```

Where 192.168.0.100 should be replaced with your unit's IP address.

## Finding device IP address

If you don't know the IP address of your unit, you can use the following script to find it:

```bash
PYTHONPATH=. python3 examples/discover.py
```
