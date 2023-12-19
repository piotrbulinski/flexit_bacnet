def hex_to_dotted(hex_str):
    """Convert a hexadecimal string to dotted decimal format."""
    parts = [str(int(hex_str[i:i + 2], 16)) for i in range(0, len(hex_str), 2)]
    return '.'.join(reversed(parts))


def get_local_networks():
    """Get local networks from /proc/net/route."""
    local_networks = []

    with open('/proc/net/route', 'r') as f:
        for line in f.readlines():
            line = line.strip()

            if not line:
                continue

            parts = line.split()
            if len(parts) < 8 or parts[0] == 'Iface':
                continue

            network = hex_to_dotted(parts[1])
            netmask = hex_to_dotted(parts[7])
            local_networks.append((network, netmask))

    return local_networks


def get_broadcast_address(network, netmask):
    """Get broadcast address for a network and netmask."""
    network = network.split('.')
    netmask = netmask.split('.')
    broadcast = []

    for i in range(4):
        broadcast.append(str(int(network[i]) | int(netmask[i]) ^ 255))

    return '.'.join(broadcast)


def get_broadcast_addresses():
    """Get broadcast addresses for all local networks."""

    broadcast_addresses = []
    for network, netmask in get_local_networks():
        broadcast_addresses.append(get_broadcast_address(network, netmask))

    return broadcast_addresses
