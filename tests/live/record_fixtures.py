"""Record answers of a real unit as test fixtures (read-only).

    python tests/live/record_fixtures.py <unit-ip> <fixture-dir-name> [device-id]

Sends only readPropertyMultiple requests and writes tests/fixtures/<dir>/*.json
with the request and every datagram the unit answered (segments kept as sent,
so reassembly can be replayed). The serial number is replaced by zeros.
"""

import asyncio
import datetime
import json
import sys
from pathlib import Path

from flexit_bacnet import bacnet, nordic
from flexit_bacnet.bacnet import BACnetRequest, DeviceProperty, ObjectType, ReadValue

OUT = Path(__file__).parent.parent / "fixtures"


class _RecordingRequest(BACnetRequest):
    def __init__(self, request):
        super().__init__(request)
        self.datagrams = []

    def datagram_received(self, response, addr):
        self.datagrams.append(response)
        super().datagram_received(response, addr)


async def _record(address, port, request):
    assert request[6] >> 4 == bacnet.APDUType.CONFIRMED_REQ
    assert request[9] == bacnet.ServiceChoice.READ_PROPERTY_MULTIPLE, "read-only: readPropertyMultiple only"

    recording = _RecordingRequest(request)
    transport, _ = await asyncio.get_running_loop().create_datagram_endpoint(
        lambda: recording, remote_addr=(address, port)
    )
    try:
        await recording.wait(timeout=5)
    finally:
        transport.close()

    return recording.datagrams


async def main(address, name, device_id):
    device = DeviceProperty(ObjectType.DEVICE, device_id, read_values=[ReadValue.OBJECT_NAME, ReadValue.DESCRIPTION])
    info = DeviceProperty(ObjectType.DEVICE, device_id, read_values=[77, 28, 70, 44, 12, 62, 107, 11])
    port = bacnet.DEFAULT_BACNET_PORT

    identity = bacnet._parse_read_property_multiple_response((await _record(address, port, bacnet._read_property_multiple([info])))[0])
    props = dict(identity[(ObjectType.DEVICE, device_id)])
    serial = props[ReadValue.DESCRIPTION]
    scrubbed = serial[:6] + "".join("0" if c.isdigit() else c for c in serial[6:])
    unit = f"{props[ReadValue.OBJECT_NAME]} serial {serial[:6]}, {props[70]}, {props[44]}, {props[12]}"

    scenarios = {
        "update": ("FlexitBACnet.update() request", nordic.DEVICE_PROPERTIES + [device]),
        "segmented_present_value_and_name": (
            "present-value + object-name of every nordic object (segmented answer)",
            [DeviceProperty(p.object_type, p.instance_id, read_values=[85, 77]) for p in nordic.DEVICE_PROPERTIES],
        ),
        "device_object": ("device object properties", [info]),
    }

    (OUT / name).mkdir(parents=True, exist_ok=True)

    for scenario, (note, properties) in scenarios.items():
        request = bacnet._read_property_multiple(properties)
        datagrams = [d.replace(serial.encode(), scrubbed.encode()) for d in await _record(address, port, request)]
        path = OUT / name / f"{scenario}.json"
        path.write_text(json.dumps({
            "unit": unit,
            "captured": datetime.date.today().isoformat(),
            "note": note,
            "request": request.hex(),
            "responses": [d.hex() for d in datagrams],
        }, indent=1) + "\n")
        print(f"{path}: {len(datagrams)} datagram(s)")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)

    asyncio.run(main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 2))
