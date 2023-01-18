import socket
from typing import List, Any

import BAC0
from BAC0.scripts import Lite
from decorator import contextmanager

from flexit_bacnet.device_property import DeviceProperty, PRESENT_VALUE
from flexit_bacnet.typing import DeviceState

BAC0.log_level('silence')


def get_local_ip(device_address: str) -> None | str:
    """Get the local IP address used to connect to the remote one."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]
    except Exception:  # pylint: disable=broad-except
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


@contextmanager
def run_bacnet(device_address: str) -> Lite:
    """Return a running BACnet application to accept read and write requests."""
    bacnet_lite = BAC0.lite(get_local_ip(device_address), ping=False)

    try:
        yield bacnet_lite
    finally:
        bacnet_lite.disconnect()


def read_multiple(device_address: str, device_properties: List[DeviceProperty]) -> DeviceState:
    request = {
        'address': device_address,
        'objects': {
            f'{dp.object_type}:{dp.instance_id}': dp.read_values
            for dp in device_properties
        },
    }

    result: DeviceState

    with run_bacnet(device_address) as bacnet:
        result = bacnet.readMultiple(device_address, request)

    if result == ['']:
        raise ConnectionError

    return result


def write(device_address: str, device_property: DeviceProperty, value: Any):
    with run_bacnet(device_address) as bacnet:
        args = [
            device_address,
            device_property.object_type,
            device_property.instance_id,
            PRESENT_VALUE,
            value
        ]

        if device_property.priority is not None:
            args += [f'- {device_property.priority}']

        bacnet.write(" ".join(map(lambda arg: str(arg), args)))
