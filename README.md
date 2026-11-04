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

You need to have Python version 3.11 or above.


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

## Finding device IP address

If you don't know the IP address of your unit, you can use the following script to find it:

```bash
PYTHONPATH=. python3 examples/discover.py
```

## Adding tests for your unit

Flexit units differ between models and firmware versions: some objects are
missing, and some have different numbers. If you own a unit, you can record
how it answers and add those recordings to the test suite. The tests then
replay them offline, so every future change is checked against your model
without anyone needing your hardware.

Everything below only **reads** from the unit. Nothing is written to it.

You need Python 3.11 or newer, git, and a computer on the same network as the
unit. You also need the unit's IP address and Device ID (see
[Prerequisites](#prerequisites); the Device ID is usually 2).

### 1. Get the code

```bash
git clone https://github.com/piotrbulinski/flexit_bacnet.git
cd flexit_bacnet
```

### 2. Create a virtual environment and install the library

macOS / Linux:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e . pytest
```

Windows (PowerShell):

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -e . pytest
```

Keep the virtual environment activated for the following steps. Make sure the
existing tests pass before you add anything:

```bash
python -m pytest
```

### 3. Check that you can reach the unit

```bash
python examples/device_info.py 192.168.0.18
```

Replace `192.168.0.18` with your unit's IP address. You should see the model,
the serial number and a list of readings. Readings shown as `(unsupported)`
are objects your unit does not have. This example uses Device ID 2. If yours
is different, use the Device ID argument in the next steps.

If nothing comes back, check that the computer and the unit are on the same
network and that BACnet is enabled on the unit. On macOS, also allow your
terminal app under System Settings → Privacy & Security → Local Network.

### 4. Run the live checks

These read from the unit and check the answers: identification, all readings,
20 updates in a row, 15 updates at the same time, a large (segmented) answer
and the device information.

macOS / Linux:

```bash
FLEXIT_HOST=192.168.0.18 python -m pytest tests/live -s --override-ini addopts=
```

Windows (PowerShell):

```powershell
$env:FLEXIT_HOST = "192.168.0.18"
python -m pytest tests/live -s --override-ini addopts=
```

Add `FLEXIT_DEVICE_ID=<id>` (`$env:FLEXIT_DEVICE_ID = "<id>"` on Windows) if
your Device ID is not 2. If a check fails, keep its output: it is exactly what
we need to know about your model.

### 5. Record your unit's answers

Pick a folder name for your unit: lowercase, product line and model, e.g.
`nordic_s3_rer` or `econordic_wh4`. Then run:

```bash
python tests/live/record_fixtures.py 192.168.0.18 nordic_s3_rer
```

Add the Device ID as a third argument if it is not 2. This creates
`tests/fixtures/nordic_s3_rer/` with three files:

| File | What it holds |
|---|---|
| `update.json` | the answer to the request `update()` sends |
| `segmented_present_value_and_name.json` | values and names of every object (big enough to make most units split their answer into segments) |
| `device_object.json` | model, firmware and application version, maximum message size |

Your serial number is replaced with zeros after the six digit model prefix,
e.g. `800220-000000`. The files contain no IP address. Open them if you want to
check what you are sharing.

### 6. Run the tests with your recordings

```bash
python -m pytest
```

`tests/test_recorded_models.py` picks up every folder in `tests/fixtures/` on
its own. It checks that your recordings decode, that every reading works on
your unit, that the serial number is scrubbed, and that the segmented answer
reassembles. You don't need to write any test code.

### 7. Optional: add checks specific to your model

If you know what your unit should report (e.g. which objects it does not
have), add a test file such as `tests/test_recorded_nordic_s3.py`.
`tests/test_recorded_nordic_cl4.py` shows how. In short:

```python
from conftest import load_recorded
from flexit_bacnet import bacnet

def test_my_unit_has_no_extract_air_humidity():
    state = bacnet._parse_read_property_multiple_response(
        load_recorded("nordic_s3_rer", "update").response
    )
    ...
```

### 8. Send it in

```bash
git checkout -b fixtures-nordic-s3-rer
git add tests/fixtures/nordic_s3_rer
git commit -m "Add recorded answers from a Nordic S3 RER"
```

Then fork the repository on GitHub, push the branch to your fork and open a
pull request. In the description, include the output of
`examples/device_info.py` and of the live checks from step 4.
