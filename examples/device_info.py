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
