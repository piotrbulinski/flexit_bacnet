import sys

# import FlexitBACnet
from flexit_bacnet import FlexitBACnet

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

    # check device name and s/n
    print('Device Name:', device.device_name)
    print('Serial Number:', device.serial_number)
