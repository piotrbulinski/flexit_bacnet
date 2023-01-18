# import FlexitBACnet
from flexit_bacnet import (
    FlexitBACnet,
)

if __name__ == '__main__':
    # create a FlexitBACnet device instance with the IP address and Device ID
    device = FlexitBACnet('192.168.2.14', 2)

    # check whether device address and ID are correct
    if not device.is_valid():
        raise Exception('not a valid device')

    # check current ventilation mode
    print('ventilation mode:', device.ventilation_mode)