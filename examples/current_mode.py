# import FlexitBACnet
import sys

from flexit_bacnet import (
    FlexitBACnet,
    VENTILATION_MODE
)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f'usage ./{sys.argv[0]} <flexit-unit-ip-address>')
        exit()

    device_address = sys.argv[1]

    # create a FlexitBACnet device instance with the IP address and Device ID
    device = FlexitBACnet(device_address, 2)

    # check whether device address and ID are correct
    if not device.is_valid():
        raise Exception('not a valid device')

    # check current ventilation mode
    print('ventilation mode:', device.ventilation_mode)