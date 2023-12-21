import asyncio
import os
import socket

from enum import IntEnum
from struct import pack, unpack
from typing import Any, Dict, List, Optional, Tuple


DEBUG = os.getenv("DEBUG") is not None


class APDUType(IntEnum):
    CONFIRMED_REQ = 0
    UNCONFIRMED_REQ = 1
    SIMPLE_ACK = 2
    COMPLEX_ACK = 3


class PDUFlags(IntEnum):
    SEGMENTED_RESPONSE_ACCEPTED = 2
    MORE_SEGMENTS = 4
    SEGMENTED_REQUEST = 8


# max 16 segments
MAX_RESPONSE_SEGMENTS = 4

# max 1024 octets
MAX_APDU_SIZE = 4

# use static invoke ID
INVOKE_ID = 1

TAG_OBJECT_TYPE_SHIFT = 22
TAG_INSTANCE_ID_MASK = 0x3FFFFF

TAG_OPEN = 6
TAG_CLOSE = 7
TAG_NO_PROPERTY_VALUE = 4
TAG_NO_PROPERTY_ACCESS_ERROR = 5

PROPERTY_ACCESS_ERROR_SIZE = 4


class ServiceChoice(IntEnum):
    READ_PROPERTY_MULTIPLE = 14
    WRITE_PROPERTY = 15


class UnconfirmedServiceChoice(IntEnum):
    UNCONFIRMED_PRIVATE_TRANSFER = 4


BVLC_TYPE = 0x81
BVLC_FUNCTION_UNICAST = 0x0A
BVLC_FUNCTION_BROADCAST = 0x0B
BVLC_LENGTH = 4

NPDU_VERSION = 1
NPDU_EXPECT_REPLY = 4
NPDU = pack("!BB", NPDU_VERSION, NPDU_EXPECT_REPLY)


class ReadValue(IntEnum):
    DESCRIPTION = 28
    OBJECT_NAME = 77
    PRESENT_VALUE = 85


class ObjectType(IntEnum):
    ANALOG_INPUT = 0
    ANALOG_OUTPUT = 1
    ANALOG_VALUE = 2
    BINARY_VALUE = 5
    DEVICE = 8
    MULTI_STATE_VALUE = 19
    POSITIVE_INTEGER_VALUE = 48


# ObjectIdentifier tuple represents ObjectType and InstanceIdentifier
ObjectIdentifier = Tuple[ObjectType, int]

# ObjectProperties represents a map of ReadValue to the actual value
ObjectProperties = List[Tuple[ReadValue, Any]]

DeviceState = Dict[ObjectIdentifier, ObjectProperties]


class Tag:
    def __init__(self, number: int, is_context: bool, length_type: int):
        self.number = number
        self.is_context = is_context
        self.length_type = length_type

    @property
    def int(self) -> int:
        ctx = 8 if self.is_context else 0
        return self.number << 4 | ctx | self.length_type

    def pack(self) -> bytes:
        return pack("!B", self.int)


class CtxTag(Tag):
    def __init__(self, number: int, length_type: int):
        super().__init__(number=number, is_context=True, length_type=length_type)


class AppTag(Tag):
    def __init__(self, number: int, length_type: int):
        super().__init__(number=number, is_context=False, length_type=length_type)


class WriteType(IntEnum):
    UnsignedInt = 2
    Real = 4
    Enumerated = 9


class DecodingError(Exception):
    pass


class DeviceProperty:
    def __init__(
        self,
        object_type: ObjectType,
        instance_id: int,
        read_values: Optional[List[ReadValue]] = None,
        priority: Optional[int] = None,
        write_type: Optional[WriteType] = None,
    ):
        self.object_type = object_type
        self.instance_id = instance_id
        self.read_values = read_values or [ReadValue.PRESENT_VALUE]
        self.priority = priority
        self.write_type = write_type

    @property
    def object_identifier(self) -> ObjectIdentifier:
        return (self.object_type, self.instance_id)

    def apdu_object_identifier(self) -> bytes:
        apdu = CtxTag(0, 4).pack()
        apdu += pack("!I", self.object_type << TAG_OBJECT_TYPE_SHIFT | self.instance_id)
        return apdu

    # read_access_spec returns APDU's read access spec for read-property-multiple service
    def read_access_spec(self) -> bytes:
        # object-identifier definition
        apdu = self.apdu_object_identifier()

        # list of property references
        apdu += CtxTag(1, TAG_OPEN).pack()

        for read_value in self.read_values:
            apdu += pack("!BB", CtxTag(0, 1).int, read_value)

        apdu += CtxTag(1, TAG_CLOSE).pack()

        return apdu

        # read_access_spec returns APDU's read access spec for read-property-multiple service

    def write_access_spec(self, value: Any) -> bytes:
        # object-identifier definition
        apdu = self.apdu_object_identifier()
        apdu += pack("!BB", CtxTag(1, 1).int, ReadValue.PRESENT_VALUE)

        apdu += CtxTag(3, TAG_OPEN).pack()

        if self.object_type == ObjectType.ANALOG_VALUE:
            apdu += pack("!Bf", AppTag(WriteType.Real, 4).int, value)
        elif self.object_type == ObjectType.BINARY_VALUE:
            apdu += pack("!BB", AppTag(WriteType.Enumerated, 1).int, value)
        else:
            apdu += pack("!BB", AppTag(WriteType.UnsignedInt, 1).int, value)

        apdu += CtxTag(3, TAG_CLOSE).pack()

        if self.priority is not None:
            apdu += pack("!BB", CtxTag(4, 1).int, self.priority)

        return apdu


# _read_property_multiple returns request payload for read-property-multiple service
def _read_property_multiple(device_properties: List[DeviceProperty]) -> bytes:
    apdu = pack(
        "!BBBB",
        APDUType.CONFIRMED_REQ << 4 | PDUFlags.SEGMENTED_RESPONSE_ACCEPTED,
        MAX_RESPONSE_SEGMENTS << 4 | MAX_APDU_SIZE,
        INVOKE_ID,
        ServiceChoice.READ_PROPERTY_MULTIPLE,
    )

    # for each device property, build read access spec chunk and append to the APDU
    for dp in device_properties:
        apdu += dp.read_access_spec()

    bvlc = pack("!BBH", BVLC_TYPE, BVLC_FUNCTION_UNICAST, BVLC_LENGTH + len(NPDU) + len(apdu))

    return bvlc + NPDU + apdu


# _parse_read_property_multiple_response and return DeviceState
def _parse_read_property_multiple_response(response: bytes) -> DeviceState:
    bvlc_type, bvlc_function, _ = unpack("!BBH", response[0:4])
    if bvlc_type != BVLC_TYPE or bvlc_function != BVLC_FUNCTION_UNICAST:
        raise DecodingError("unexpected response")

    apdu_start_index = BVLC_LENGTH + len(NPDU)
    apdu = response[apdu_start_index:]

    apdu_type = apdu[0] >> 4

    if apdu_type != APDUType.COMPLEX_ACK:
        raise DecodingError(f"unsupported response type: {apdu_type}")

    invoke_id = apdu[1]
    if invoke_id != INVOKE_ID:
        raise DecodingError(f"unexpected invoke ID: {invoke_id}")

    service_choice = apdu[2]
    if service_choice != ServiceChoice.READ_PROPERTY_MULTIPLE:
        raise DecodingError(f"unexpected service choice: {service_choice}")

    decoder = BACnetDecoder(apdu, 3)

    device_state = {}

    while not decoder.eof():
        object_type, instance_number = decoder.parse_object_identifier()
        object_id = (object_type, instance_number)
        device_state[object_id] = decoder.parse_list_of_results()

    return device_state


class BACnetDecoder:
    def __init__(self, data: bytes, offset: int = 0):
        self.data = data
        self.i = offset

    def eof(self) -> bool:
        return self.i >= len(self.data)

    def read_bytes(self, n: int) -> bytes:
        if self.i + n > len(self.data):
            raise DecodingError("unexpected EOF")

        data = self.data[self.i : self.i + n]

        self.i += n

        return data

    def read_byte(self) -> int:
        if self.i + 1 > len(self.data):
            raise DecodingError("unexpected EOF")

        byte = self.data[self.i]

        self.i += 1

        return byte

    # read_tag returns tag number, class and type/length.
    # class=0 -> context specific tag
    # class=1 -> application tag
    def read_tag(self) -> Tuple[int, int, int]:
        byte = self.read_byte()

        tag_number = byte >> 4
        tag_class = byte >> 3 & 1
        tag_type_length = byte & 7

        if tag_type_length == 5:
            tag_type_length = self.read_byte()

        return tag_number, tag_class, tag_type_length

    # read_context_tag returns tag number and type/length for a context specific tag
    def read_context_tag(self) -> Tuple[int, int]:
        tag_number, tag_class, tag_type_length = self.read_tag()
        if tag_class != 1:
            raise DecodingError(f"expected context specific tag, got {tag_class}")

        return tag_number, tag_type_length

    # read_application_tag returns tag number and type/length for an application tag
    def read_application_tag(self) -> Tuple[int, int]:
        tag_number, tag_class, tag_type_length = self.read_tag()
        if tag_class != 0:
            raise DecodingError(f"expected application tag, got {tag_class}")

        return tag_number, tag_type_length

    def parse_object_identifier(self) -> Tuple[ObjectType, int]:
        tag_number, tag_length = self.read_context_tag()

        if tag_number != 0:
            raise DecodingError("unexpected tag")

        data = unpack("!I", self.read_bytes(tag_length))[0]

        object_type = ObjectType(data >> TAG_OBJECT_TYPE_SHIFT)
        instance_number = data & 0x3FFFFF

        return object_type, instance_number

    def parse_list_of_results(self) -> ObjectProperties:
        opening_tag_number, tag_type = self.read_context_tag()
        if tag_type != TAG_OPEN:
            raise DecodingError("expected opening tag")

        results = []

        while True:
            tag_number, tag_type = self.read_context_tag()
            if tag_number == opening_tag_number and tag_type == TAG_CLOSE:
                break

            if tag_number != 2:
                raise DecodingError("unexpected tag")

            data = self.read_byte()

            read_value = ReadValue(data)

            value = self.read_value()

            results.append((read_value, value))

        return results

    def read_value(self) -> Any:
        # check the opening tag
        opening_tag_number, tag_type = self.read_context_tag()
        if tag_type != TAG_OPEN:
            raise DecodingError("expected opening tag")

        value: Any = 0

        if opening_tag_number == TAG_NO_PROPERTY_VALUE:
            tag_number, tag_length = self.read_application_tag()

            value = {
                2: self.parse_unsinged_int,
                4: self.parse_float,
                7: self.parse_string,
                9: self.parse_enumarated_value,
            }[tag_number](tag_length)
        elif opening_tag_number == TAG_NO_PROPERTY_ACCESS_ERROR:
            self.read_bytes(PROPERTY_ACCESS_ERROR_SIZE)

        # check the closing tag
        tag_number, tag_type = self.read_context_tag()
        if tag_number != opening_tag_number or tag_type != TAG_CLOSE:
            raise DecodingError("expected closing tag")

        return value

    def parse_enumarated_value(self, length: int) -> int:
        return self.read_byte()

    def parse_unsinged_int(self, length: int) -> int:
        value = 0
        for i in range(length):
            value <<= 8
            value |= self.read_byte()

        return value

    def parse_float(self, length: int) -> float:
        if length != 4:
            raise DecodingError(f"unsupported float size: {length}")

        return unpack("!f", self.read_bytes(length))[0]

    def parse_string(self, length: int) -> str:
        encoding = self.read_byte()

        if encoding != 0:
            raise DecodingError(f"unsupported encoding: {encoding}")

        return self.read_bytes(length - 1).decode("utf-8")


def _write_property(device_property: DeviceProperty, value: Any) -> bytes:
    apdu = pack(
        "!BBBB",
        APDUType.CONFIRMED_REQ << 4 | PDUFlags.SEGMENTED_RESPONSE_ACCEPTED,
        MAX_RESPONSE_SEGMENTS << 4 | MAX_APDU_SIZE,
        INVOKE_ID,
        ServiceChoice.WRITE_PROPERTY,
    )

    apdu += device_property.write_access_spec(value)

    bvlc = pack("!BBH", BVLC_TYPE, BVLC_FUNCTION_UNICAST, BVLC_LENGTH + len(NPDU) + len(apdu))

    return bvlc + NPDU + apdu


# _parse_write_property_response and check for errors
def _parse_write_property_response(response: bytes):
    bvlc_type, bvlc_function, _ = unpack("!BBH", response[0:4])
    if bvlc_type != BVLC_TYPE or bvlc_function != BVLC_FUNCTION_UNICAST:
        raise DecodingError("unexpected response")

    apdu = response[BVLC_LENGTH + len(NPDU) :]

    apdu_type = apdu[0] >> 4

    if apdu_type != APDUType.SIMPLE_ACK:
        raise DecodingError(f"unsupported response type: {apdu_type}")

    invoke_id = apdu[1]
    if invoke_id != INVOKE_ID:
        raise DecodingError(f"unexpected invoke ID: {invoke_id}")

    service_choice = apdu[2]
    if service_choice != ServiceChoice.WRITE_PROPERTY:
        raise DecodingError(f"unexpected service choice: {service_choice}")


DEFAULT_BACNET_PORT = 47808


class BACnetRequest:
    _transport: asyncio.DatagramTransport

    # response is the response payload
    response: bytes

    # exception is the exception that occurred during the request
    exception: Exception

    def __init__(self, request: bytes, done: asyncio.Future = None):
        self.request = request

        if done is None:
            done = asyncio.get_running_loop().create_future()

        self.done = done

    def connection_made(self, transport: asyncio.DatagramTransport):
        self._transport = transport
        self._transport.sendto(self.request)

    def datagram_received(self, response: bytes, addr: Tuple[str, int]):
        self.response = response
        self._transport.close()

    def error_received(self, exception: Exception):
        self.exception = exception

    def connection_lost(self, exception: Exception):
        self.exception = exception
        self.done.set_result(True)

    def wait(self, timeout: float = 1.0):
        return asyncio.wait_for(self.done, timeout=timeout)


class BACnetClient:
    def __init__(self, address: str, port: int = DEFAULT_BACNET_PORT):
        self.address = address
        self.port = port

    async def _send(self, request: bytes) -> bytes:
        loop = asyncio.get_running_loop()

        bacnet_request = BACnetRequest(request)

        transport, _ = await loop.create_datagram_endpoint(
            lambda: bacnet_request, remote_addr=(self.address, self.port)
        )

        try:
            await bacnet_request.wait(timeout=1.0)
        finally:
            transport.close()

        if bacnet_request.exception is not None:
            raise ConnectionError from bacnet_request.exception

        return bacnet_request.response

    async def read_multiple(
        self, device_properties: List[DeviceProperty]
    ) -> DeviceState:
        request = _read_property_multiple(device_properties)

        if DEBUG:
            print(f">>> {request.hex()}")

        response = await self._send(request)

        if DEBUG:
            print(f"<<< {response.hex()}")

        try:
            return _parse_read_property_multiple_response(response)
        except DecodingError as exc:
            raise DecodingError(
                f"response decoding failed: {exc}\n{response.hex()}"
            ) from exc

    async def write(self, device_property: DeviceProperty, value: Any):
        request = _write_property(device_property, value)

        response = await self._send(request)

        try:
            return _parse_write_property_response(response)
        except DecodingError as exc:
            raise DecodingError(
                f"response decoding failed: {exc}\n{response.hex()}"
            ) from exc


# Flexit uses a proprietary service defined by Siemens to discover devices on the local network.
VENDOR_ID_SIEMENS = 7
SERVICE_NUMBER_DISCOVERY = 515
SERVICE_NUMBER_IDENTIFICATION = 516

# As I cannot find the specification for the service parameters,
# will use what I've captured them from the Flexit app using Wireshark.
# It seems to contain a UUID and some other "random" value,
# but will use a fixed value for now and worry about it if anyone ever complains.
DISCOVERY_SERVICE_PARAMETERS = (
        b"\x80\x01\x00\x04\x00\x00\x00\x08\x64\x69\x73\x63\x6f\x76\x65\x72" +
        b"\x00\x00\x00\x00\x0c\x00\x01\x0b\x00\x01\x00\x00\x00\x00\x0b\x00" +
        b"\x02\x00\x00\x00\x2e\x41\x42\x54\x4d\x6f\x62\x69\x6c\x65\x3a\x38" +
        b"\x34\x33\x30\x33\x64\x32\x64\x2d\x30\x34\x39\x37\x2d\x34\x65\x33" +
        b"\x62\x2d\x62\x63\x38\x31\x2d\x37\x65\x36\x65\x62\x62\x31\x31\x65" +
        b"\x64\x62\x38\x0b\x00\x03\x00\x00\x00\x0c\x3f\x44\x65\x76\x69\x63" +
        b"\x65\x73\x3d\x41\x6c\x6c\x00\x00")


def _discovery_request() -> bytes:
    """Build a discovery request."""

    # start APDU for unconfirmed private transfer
    apdu = pack("!BB",
                APDUType.UNCONFIRMED_REQ << 4,
                UnconfirmedServiceChoice.UNCONFIRMED_PRIVATE_TRANSFER)

    # set vendor ID and service number
    apdu += pack("!BBBH",
                 CtxTag(0, 1).int, VENDOR_ID_SIEMENS,
                 CtxTag(1, 2).int, SERVICE_NUMBER_DISCOVERY)

    # set the service parameters
    apdu += CtxTag(2, TAG_OPEN).pack()
    apdu += DISCOVERY_SERVICE_PARAMETERS
    apdu += CtxTag(2, TAG_CLOSE).pack()

    # set custom npdu and bvlc
    npdu = pack("!BB", NPDU_VERSION, 0)  # don't expect reply
    bvlc = pack("!BBH", BVLC_TYPE, BVLC_FUNCTION_BROADCAST, BVLC_LENGTH + len(npdu) + len(apdu))

    return bvlc + npdu + apdu


def _is_discovery_response(response: bytes) -> bool:
    """Check if the response is a discovery response."""
    if len(response) < 32:
        return False

    bvlc_type, bvlc_function, _ = unpack("!BBH", response[0:4])
    if bvlc_type != BVLC_TYPE or bvlc_function != BVLC_FUNCTION_BROADCAST:
        return False

    apdu_start_index = BVLC_LENGTH + len(NPDU)
    apdu = response[apdu_start_index:]

    apdu_type = apdu[0] >> 4

    if apdu_type != APDUType.UNCONFIRMED_REQ:
        return False

    decoder = BACnetDecoder(apdu, 2)

    if decoder.read_context_tag() != (0, 1):
        return False

    if decoder.read_byte() != VENDOR_ID_SIEMENS:
        return False

    if decoder.read_context_tag() != (1, 2):
        return False

    if decoder.parse_unsinged_int(2) != SERVICE_NUMBER_IDENTIFICATION:
        return False

    return True


async def _receive_identification_responses(sock: socket.socket, response_ips: set):
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            if _is_discovery_response(data):
                response_ips.add(addr[0])
        except BlockingIOError:
            await asyncio.sleep(0.1)  # Wait briefly to avoid busy loop
            continue
        except Exception as e:
            print(f"Error receiving data: {e}")
            break


BROADCAST_ADDRESS = "255.255.255.255"


async def _send_discovery_request(sock: socket.socket):
    while True:
        sock.sendto(_discovery_request(), (BROADCAST_ADDRESS, DEFAULT_BACNET_PORT))
        await asyncio.sleep(0.1)  # Slight delay between sends


async def discover(timeout: float = 2.0) -> List[str]:
    """
    Discover devices on the local network.

    Returns a list of IP addresses.
    """
    response_ips = set()

    # Create a UDP socket
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(('', DEFAULT_BACNET_PORT))
        sock.setblocking(False)

        # Run sending and receiving tasks concurrently
        try:
            receiver = asyncio.create_task(_receive_identification_responses(sock, response_ips))
            sender = asyncio.create_task(_send_discovery_request(sock))

            # Wait a bit, so we can collect all device responses
            await asyncio.sleep(timeout)
        finally:
            # cancel the receiver task
            receiver.cancel()
            sender.cancel()

    return list(response_ips)
