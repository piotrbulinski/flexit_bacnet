import asyncio
import os
import socket

from enum import IntEnum
from struct import pack, unpack
from typing import Any, Dict, List, NamedTuple, Optional, Tuple, Type


DEBUG = os.getenv("DEBUG") is not None


class APDUType(IntEnum):
    CONFIRMED_REQ = 0
    UNCONFIRMED_REQ = 1
    SIMPLE_ACK = 2
    COMPLEX_ACK = 3
    SEGMENT_ACK = 4
    ERROR = 5
    REJECT = 6
    ABORT = 7


class PDUFlags(IntEnum):
    SEGMENTED_RESPONSE_ACCEPTED = 2
    MORE_SEGMENTS = 4
    SEGMENTED_REQUEST = 8


# max 16 segments
MAX_RESPONSE_SEGMENTS = 4

# max 1024 octets
MAX_APDU_SIZE = 4

# Max number of properties per readPropertyMultiple request. Keeps every
# request APDU well under the units' 1024 octet max-APDU: a Nordic CL4 answers
# a 1030 octet request with Abort buffer-overflow and silently drops larger
# ones. (Answers over 1024 octets are segmented; BACnetRequest reassembles them.)
READ_MULTIPLE_MAX_PROPERTIES = 50

# Window size accepted for a segmented answer (clause 5.4.4.3: at most the
# window the unit proposes; a Nordic CL4 proposes 4).
MAX_SEGMENT_WINDOW = 16

# Default seconds to wait for each answer, and how many times a read is
# retried after a timeout. Writes are never retried.
DEFAULT_TIMEOUT = 1.0
DEFAULT_READ_RETRIES = 1

# use static invoke ID
INVOKE_ID = 1

TAG_OBJECT_TYPE_SHIFT = 22
TAG_INSTANCE_ID_MASK = 0x3FFFFF

TAG_OPEN = 6
TAG_CLOSE = 7
TAG_NO_PROPERTY_VALUE = 4
TAG_NO_PROPERTY_ACCESS_ERROR = 5



class ServiceChoice(IntEnum):
    READ_PROPERTY_MULTIPLE = 14
    WRITE_PROPERTY = 15


class UnconfirmedServiceChoice(IntEnum):
    UNCONFIRMED_PRIVATE_TRANSFER = 4


BVLC_TYPE = 0x81
BVLC_FUNCTION_UNICAST = 0x0A
BVLC_FUNCTION_BROADCAST = 0x0B
BVLC_FUNCTION_FORWARDED_NPDU = 0x04
BVLC_LENGTH = 4

NPDU_VERSION = 1
NPDU_EXPECT_REPLY = 4
NPDU_NETWORK_LAYER_MESSAGE = 0x80
NPDU_DESTINATION_SPECIFIER = 0x20
NPDU_SOURCE_SPECIFIER = 0x08
NPDU = pack("!BB", NPDU_VERSION, NPDU_EXPECT_REPLY)


class ReadValue(IntEnum):
    DESCRIPTION = 28
    OBJECT_LIST = 76
    OBJECT_NAME = 77
    PRESENT_VALUE = 85


class ObjectType(IntEnum):
    ANALOG_INPUT = 0
    ANALOG_OUTPUT = 1
    ANALOG_VALUE = 2
    BINARY_VALUE = 5
    DEVICE = 8
    MULTI_STATE_INPUT = 13
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


class BACnetError(DecodingError):
    """The unit answered a request with an Error, Reject or Abort PDU.

    `kind` is "error", "reject" or "abort"; `reason` is the decoded text, e.g.
    "property / write-access-denied" or "out-of-resources".
    """

    def __init__(self, kind: str, reason: str):
        super().__init__(f"{kind} from unit: {reason}")
        self.kind = kind
        self.reason = reason


# BACnet-Error error-class (clause 18)
ERROR_CLASSES = {
    0: "device",
    1: "object",
    2: "property",
    3: "resources",
    4: "security",
    5: "services",
    6: "vt",
    7: "communication",
}

# BACnet-Error error-code (clause 18) - the ones a client can run into
ERROR_CODES = {
    0: "other",
    2: "configuration-in-progress",
    3: "device-busy",
    7: "inconsistent-parameters",
    9: "invalid-data-type",
    13: "invalid-parameter-data-type",
    16: "missing-required-parameter",
    25: "operational-problem",
    26: "password-failure",
    27: "read-access-denied",
    29: "service-request-denied",
    30: "timeout",
    31: "unknown-object",
    32: "unknown-property",
    36: "unsupported-object-type",
    37: "value-out-of-range",
    40: "write-access-denied",
    42: "invalid-array-index",
    45: "optional-functionality-not-supported",
    47: "datatype-not-supported",
}

# BACnet-Reject-Reason (clause 18)
REJECT_REASONS = {
    0: "other",
    1: "buffer-overflow",
    2: "inconsistent-parameters",
    3: "invalid-parameter-data-type",
    4: "invalid-tag",
    5: "missing-required-parameter",
    6: "parameter-out-of-range",
    7: "too-many-arguments",
    8: "undefined-enumeration",
    9: "unrecognized-service",
}

# BACnet-Abort-Reason (clause 18)
ABORT_REASONS = {
    0: "other",
    1: "buffer-overflow",
    2: "invalid-apdu-in-this-state",
    3: "preempted-by-higher-priority-task",
    4: "segmentation-not-supported",
    5: "security-error",
    6: "insufficient-security",
    7: "window-size-out-of-range",
    8: "application-exceeded-reply-time",
    9: "out-of-resources",
    10: "tsm-timeout",
    11: "apdu-too-long",
}


def _raise_if_error_pdu(apdu: bytes) -> None:
    """Raise BACnetError if the APDU is an Error, Reject or Abort PDU.

    Error-PDU:  0x50 invoke-id service-choice error-class error-code
                (class and code as application-tagged ENUMERATED)
    Reject-PDU: 0x60 invoke-id reject-reason
    Abort-PDU:  0x70|0x71 invoke-id abort-reason (bit 0 = sent by server)
    """
    apdu_type = apdu[0] >> 4

    if apdu_type == APDUType.ABORT:
        reason = apdu[2] if len(apdu) > 2 else None
        raise BACnetError("abort", ABORT_REASONS.get(reason, f"reason {reason}"))

    if apdu_type == APDUType.REJECT:
        reason = apdu[2] if len(apdu) > 2 else None
        raise BACnetError("reject", REJECT_REASONS.get(reason, f"reason {reason}"))

    if apdu_type == APDUType.ERROR:
        try:
            decoder = BACnetDecoder(apdu, 3)
            _, length = decoder.read_application_tag()
            error_class = decoder.parse_unsinged_int(length)
            _, length = decoder.read_application_tag()
            error_code = decoder.parse_unsinged_int(length)
        except DecodingError:
            raise BACnetError("error", f"undecodable error PDU {apdu.hex()}")

        raise BACnetError(
            "error",
            f"{ERROR_CLASSES.get(error_class, f'class {error_class}')} / "
            f"{ERROR_CODES.get(error_code, f'code {error_code}')}",
        )


def _enum_or_int(enum: Type[IntEnum], value: int) -> int:
    """Return enum(value), or the plain int for a value the enum does not define.

    The units have object types (e.g. schedule, structured view, proprietary
    264) and properties the library has no name for; those must not abort
    decoding of the whole answer.
    """
    try:
        return enum(value)
    except ValueError:
        return value


def _apdu_from_response(response: bytes) -> bytes:
    """Strip BVLC and NPDU headers and return the APDU.

    Also handles Forwarded-NPDU (BBMD) frames and NPDUs carrying source or
    destination network addresses (answers routed through a BACnet router).
    """
    if len(response) < BVLC_LENGTH + 2:
        raise DecodingError(f"response too short: {len(response)} octets")

    bvlc_type, bvlc_function, bvlc_length = unpack("!BBH", response[0:4])
    if bvlc_type != BVLC_TYPE or bvlc_function not in (BVLC_FUNCTION_UNICAST, BVLC_FUNCTION_FORWARDED_NPDU):
        raise DecodingError("unexpected response")

    if bvlc_length != len(response):
        raise DecodingError(f"BVLC length {bvlc_length} does not match datagram length {len(response)}")

    i = BVLC_LENGTH
    if bvlc_function == BVLC_FUNCTION_FORWARDED_NPDU:
        i += 6  # original source B/IP address: 4 octets IP + 2 octets port

    try:
        version, control = response[i], response[i + 1]
        i += 2

        if version != NPDU_VERSION:
            raise DecodingError(f"unsupported NPDU version: {version}")

        if control & NPDU_NETWORK_LAYER_MESSAGE:
            raise DecodingError("network layer message, not an APDU")

        if control & NPDU_DESTINATION_SPECIFIER:
            i += 3 + response[i + 2]  # DNET, DLEN, DADR

        if control & NPDU_SOURCE_SPECIFIER:
            i += 3 + response[i + 2]  # SNET, SLEN, SADR

        if control & NPDU_DESTINATION_SPECIFIER:
            i += 1  # hop count
    except IndexError:
        raise DecodingError("truncated NPDU")

    apdu = response[i:]
    if not apdu:
        raise DecodingError("empty APDU")

    return apdu


class DeviceProperty:
    def __init__(
        self,
        object_type: ObjectType,
        instance_id: int,
        read_values: Optional[List[ReadValue]] = None,
        priority: Optional[int] = None,
        write_type: Optional[WriteType] = None,
        object_name: Optional[str] = None,
    ):
        """One BACnet object of the unit.

        object_name -- the object's name on the unit, e.g. "R(1)'TOa". Object
        numbers differ between units and firmware versions while the names do
        not, so FlexitBACnet checks the name on the first update() and, if the
        object is not at instance_id, looks it up by name (see device.py).
        """
        self.object_type = object_type
        self.instance_id = instance_id
        self.read_values = read_values or [ReadValue.PRESENT_VALUE]
        self.priority = priority
        self.write_type = write_type
        self.object_name = object_name

    def __repr__(self) -> str:
        return f"DeviceProperty({getattr(self.object_type, 'name', self.object_type)}, {self.instance_id})"

    def moved_to(self, object_type: Any, instance_id: int) -> "DeviceProperty":
        """Return a copy of this property at another object identifier."""
        return DeviceProperty(
            object_type,
            instance_id,
            read_values=list(self.read_values),
            priority=self.priority,
            write_type=self.write_type,
            object_name=self.object_name,
        )

    def reading(self, read_value: "ReadValue") -> "DeviceProperty":
        """Return a property reading read_value (e.g. OBJECT_NAME) of the same object."""
        return DeviceProperty(self.object_type, self.instance_id, read_values=[read_value])

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
            # unsigned integer encoded on the minimal number of octets (1-4)
            try:
                unsigned = int(value)
            except (TypeError, ValueError, OverflowError) as e:
                raise ValueError(f"unsigned integer value required: {value}") from e

            # reject lossy conversions, e.g. 1.5 -> 1 (integral floats like 30.0 are accepted)
            if unsigned != value:
                raise ValueError(f"unsigned integer value required: {value}")

            if not 0 <= unsigned <= 0xFFFFFFFF:
                raise ValueError(f"unsigned integer value out of range (0 - 4294967295): {value}")

            length = max(1, (unsigned.bit_length() + 7) // 8)
            apdu += AppTag(WriteType.UnsignedInt, length).pack()
            apdu += unsigned.to_bytes(length, "big")

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
    apdu = _apdu_from_response(response)

    if len(apdu) < 3:
        raise DecodingError(f"truncated APDU: {apdu.hex()}")

    _raise_if_error_pdu(apdu)

    apdu_type = apdu[0] >> 4

    if apdu_type != APDUType.COMPLEX_ACK:
        raise DecodingError(f"unsupported response type: {apdu_type}")

    if apdu[0] & PDUFlags.SEGMENTED_REQUEST:
        # BACnetRequest reassembles segments before the answer is parsed;
        # a single segment cannot be decoded on its own
        raise DecodingError("segmented response must be reassembled before parsing")

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


class PropertyError(NamedTuple):
    """A per-property access error inside a readPropertyMultiple answer.

    The unit answers this (instead of a value) for an object or property it
    does not have, e.g. error class object (1) / unknown-object (31). It is
    kept in the device state so that "missing on this unit" can be told apart
    from a real reading of 0.
    """

    error_class: int
    error_code: int


class BitString(NamedTuple):
    """A decoded BACnet bit string, e.g. status-flags: bits[0] = in-alarm, [1] = fault, ..."""

    bits: Tuple[bool, ...]


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

    def peek_tag(self) -> Tuple[int, int, int]:
        """Return the next tag like read_tag() without consuming it."""
        i = self.i
        try:
            return self.read_tag()
        finally:
            self.i = i

    # read_tag returns tag number, class and type/length.
    # class=0 -> application tag
    # class=1 -> context specific tag
    def read_tag(self) -> Tuple[int, int, int]:
        byte = self.read_byte()

        tag_number = byte >> 4
        tag_class = byte >> 3 & 1
        tag_type_length = byte & 7

        # extended tag number (clause 20.2.1.2)
        if tag_number == 15:
            tag_number = self.read_byte()

        # 5 means extended length (clause 20.2.1.3.1): one octet,
        # or 254 + two octets, or 255 + four octets
        if tag_type_length == 5:
            tag_type_length = self.read_byte()
            if tag_type_length == 254:
                tag_type_length = self.parse_unsinged_int(2)
            elif tag_type_length == 255:
                tag_type_length = self.parse_unsinged_int(4)

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

        if tag_number != 0 or tag_length != 4:
            raise DecodingError(f"expected object identifier, got tag {tag_number} of length {tag_length}")

        return self._object_identifier(self.read_bytes(4))

    @staticmethod
    def _object_identifier(data: bytes) -> Tuple[ObjectType, int]:
        if len(data) != 4:
            raise DecodingError(f"object identifier of {len(data)} octets")

        value = unpack("!I", data)[0]

        # unknown object types (e.g. schedule, structured view or the
        # proprietary type 264 on Siemens controllers) are kept as int
        object_type = _enum_or_int(ObjectType, value >> TAG_OBJECT_TYPE_SHIFT)
        instance_number = value & TAG_INSTANCE_ID_MASK

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

            # property identifiers above 255 take more than one octet
            read_value = _enum_or_int(ReadValue, self.parse_unsinged_int(tag_type))

            # optional property array index, context tag 3
            tag_number, tag_class, tag_type = self.peek_tag()
            if tag_class == 1 and tag_number == 3 and tag_type not in (TAG_OPEN, TAG_CLOSE):
                self.read_tag()
                self.parse_unsinged_int(tag_type)

            value = self.read_value()

            results.append((read_value, value))

        return results

    def read_value(self) -> Any:
        # check the opening tag
        opening_tag_number, tag_type = self.read_context_tag()
        if tag_type != TAG_OPEN:
            raise DecodingError("expected opening tag")

        value: Any

        if opening_tag_number == TAG_NO_PROPERTY_VALUE:
            value = self._read_values_until_close(opening_tag_number)
        elif opening_tag_number == TAG_NO_PROPERTY_ACCESS_ERROR:
            # error class and error code, both enumerated
            _, length = self.read_application_tag()
            error_class = self.parse_unsinged_int(length)
            _, length = self.read_application_tag()
            error_code = self.parse_unsinged_int(length)
            value = PropertyError(error_class, error_code)

            # check the closing tag
            tag_number, tag_type = self.read_context_tag()
            if tag_number != opening_tag_number or tag_type != TAG_CLOSE:
                raise DecodingError("expected closing tag")
        else:
            raise DecodingError(f"unexpected tag {opening_tag_number} in read access result")

        return value

    def _read_values_until_close(self, closing_tag_number: int) -> Any:
        """Read values up to the matching closing tag.

        A single value (every present-value) is returned as is; arrays and
        lists (e.g. object-list) as a list; nested constructed data as nested
        lists; context tagged primitives inside constructed data as raw bytes.
        """
        values = []

        while True:
            tag_number, tag_class, tag_length = self.read_tag()

            if tag_class == 1:
                if tag_length == TAG_CLOSE:
                    if tag_number != closing_tag_number:
                        raise DecodingError("expected closing tag")
                    break

                if tag_length == TAG_OPEN:
                    values.append(self._read_values_until_close(tag_number))
                else:
                    values.append(self.read_bytes(tag_length))

                continue

            values.append(self._parse_application_value(tag_number, tag_length))

        if not values:
            raise DecodingError("empty property value")

        return values[0] if len(values) == 1 else values

    def _parse_application_value(self, tag_number: int, length: int) -> Any:
        if tag_number == 0:  # null
            return None

        if tag_number == 1:  # boolean, the value is in the length field
            return bool(length)

        parser = {
            2: self.parse_unsinged_int,
            3: self.parse_signed_int,
            4: self.parse_float,
            5: self.parse_double,
            6: self.read_bytes,  # octet string
            7: self.parse_string,
            8: self.parse_bit_string,
            9: self.parse_enumarated_value,
            10: self.read_bytes,  # date
            11: self.read_bytes,  # time
            12: lambda n: self._object_identifier(self.read_bytes(n)),
        }.get(tag_number)

        if parser is None:
            # reserved application tag: skip it but keep the answer decodable
            return self.read_bytes(length)

        return parser(length)

    def parse_enumarated_value(self, length: int) -> int:
        # enumerations above 255 take more than one octet
        return self.parse_unsinged_int(length)

    def parse_unsinged_int(self, length: int) -> int:
        value = 0
        for i in range(length):
            value <<= 8
            value |= self.read_byte()

        return value

    def parse_signed_int(self, length: int) -> int:
        return int.from_bytes(self.read_bytes(length), "big", signed=True)

    def parse_float(self, length: int) -> float:
        if length != 4:
            raise DecodingError(f"unsupported float size: {length}")

        return unpack("!f", self.read_bytes(length))[0]

    def parse_double(self, length: int) -> float:
        if length != 8:
            raise DecodingError(f"unsupported double size: {length}")

        return unpack("!d", self.read_bytes(length))[0]

    def parse_bit_string(self, length: int) -> BitString:
        if length == 0:
            return BitString(())

        unused = self.read_byte()
        data = self.read_bytes(length - 1)
        bits = [bool(byte >> (7 - i) & 1) for byte in data for i in range(8)]

        return BitString(tuple(bits[: len(bits) - unused] if unused else bits))

    def parse_string(self, length: int) -> str:
        if length == 0:
            raise DecodingError("character string without character set")

        encoding = self.read_byte()
        data = self.read_bytes(length - 1)

        codec = CHARACTER_SETS.get(encoding)
        if codec is None:
            raise DecodingError(f"unsupported encoding: {encoding}")

        return data.decode(codec, errors="replace")


# BACnet character sets (clause 20.2.9) and the matching Python codecs
CHARACTER_SETS = {
    0: "utf-8",
    3: "utf-32-be",
    4: "utf-16-be",
    5: "latin-1",
}


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
    apdu = _apdu_from_response(response)

    if len(apdu) < 3:
        raise DecodingError(f"truncated APDU: {apdu.hex()}")

    _raise_if_error_pdu(apdu)

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


def _segment_ack(invoke_id: int, sequence_number: int, window_size: int, negative: bool = False) -> bytes:
    """BACnet-SegmentACK-PDU sent by the client (clause 20.1.6)."""
    apdu = pack(
        "!BBBB",
        APDUType.SEGMENT_ACK << 4 | (2 if negative else 0),
        invoke_id,
        sequence_number,
        window_size,
    )
    npdu = pack("!BB", NPDU_VERSION, 0)

    return pack("!BBH", BVLC_TYPE, BVLC_FUNCTION_UNICAST, BVLC_LENGTH + len(npdu) + len(apdu)) + npdu + apdu


class _SegmentAssembler:
    """Receiver side of a segmented ComplexACK (clause 5.4.4.3 / 5.4.4.4).

    The unit sends the first segment alone and waits for a SegmentACK that
    sets the window size, then sends a window of segments at a time and waits
    for an ACK of the last segment of each window. Without these ACKs it
    repeats segment 0 every few seconds and the request times out.
    """

    def __init__(self):
        self.segments: List[bytes] = []
        self.header: bytes = b""
        self.window = 1
        self.initial_sequence = 0
        self.last_sequence = -1

    def add(self, response: bytes, apdu: bytes) -> Tuple[Optional[bytes], Optional[bytes]]:
        """Process one segment; return (ack to send or None, reassembled response or None)."""
        if len(apdu) < 5:
            raise DecodingError("truncated segment header")

        flags, invoke_id, sequence, proposed_window = apdu[0], apdu[1], apdu[2], apdu[3]
        more_follows = bool(flags & PDUFlags.MORE_SEGMENTS)

        if self.last_sequence < 0:
            if sequence != 0:
                # not the start of an answer we are waiting for
                return None, None

            # keep BVLC/NPDU of the first segment, rebuild the APDU header unsegmented
            self.header = response[: len(response) - len(apdu)]
            self.service_choice = apdu[4]
            self.invoke_id = invoke_id
            self.window = max(1, min(proposed_window, MAX_SEGMENT_WINDOW))
            self.segments.append(apdu[5:])
            self.last_sequence = 0
            self.initial_sequence = 0

            if not more_follows:
                return _segment_ack(invoke_id, 0, self.window), self._reassemble()

            # the first segment is always acknowledged, which sets the window size
            return _segment_ack(invoke_id, 0, self.window), None

        expected = (self.last_sequence + 1) % 256

        if sequence != expected:
            if (self.last_sequence - sequence) % 256 < self.window:
                # duplicate of a segment we already have: discard
                return None, None

            # out of order: ask for everything after the last good segment
            self.initial_sequence = self.last_sequence
            return _segment_ack(invoke_id, self.last_sequence, self.window, negative=True), None

        self.segments.append(apdu[5:])
        self.last_sequence = expected

        if len(self.segments) > MAX_SEGMENTS_ACCEPTED:
            raise DecodingError(f"answer has more than {MAX_SEGMENTS_ACCEPTED} segments")

        if not more_follows:
            return _segment_ack(invoke_id, sequence, self.window), self._reassemble()

        if sequence == (self.initial_sequence + self.window) % 256:
            self.initial_sequence = sequence
            return _segment_ack(invoke_id, sequence, self.window), None

        return None, None

    def _reassemble(self) -> bytes:
        apdu = pack("!BBB", APDUType.COMPLEX_ACK << 4, self.invoke_id, self.service_choice) + b"".join(self.segments)

        # rewrite the BVLC length for the reassembled message
        return pack("!BBH", self.header[0], self.header[1], len(self.header) + len(apdu)) + self.header[4:] + apdu


# MAX_RESPONSE_SEGMENTS = 4 asks the unit for at most 16 segments
MAX_SEGMENTS_ACCEPTED = 16


class BACnetRequest:
    _transport: asyncio.DatagramTransport

    # response is the response payload
    response: bytes

    # exception is the exception that occurred during the request
    exception: Optional[Exception] = None

    def __init__(self, request: bytes, done: asyncio.Future = None):
        self.request = request
        self._segments: Optional[_SegmentAssembler] = None

        if done is None:
            done = asyncio.get_running_loop().create_future()

        self.done = done

    def connection_made(self, transport: asyncio.DatagramTransport):
        self._transport = transport
        self._transport.sendto(self.request)

    def datagram_received(self, response: bytes, addr: Tuple[str, int]):
        try:
            apdu = _apdu_from_response(response)
        except DecodingError:
            apdu = b""

        segmented = (
            len(apdu) >= 1
            and apdu[0] >> 4 == APDUType.COMPLEX_ACK
            and apdu[0] & PDUFlags.SEGMENTED_REQUEST
        )

        if not segmented:
            self.response = response
            self._transport.close()
            return

        if self._segments is None:
            self._segments = _SegmentAssembler()

        try:
            ack, complete = self._segments.add(response, apdu)
        except DecodingError as exc:
            self.exception = exc
            self._transport.close()
            return

        if ack is not None:
            self._transport.sendto(ack)

        if complete is not None:
            self.response = complete
            self._transport.close()

    def error_received(self, exception: Exception):
        # e.g. ICMP port/host unreachable: fail now with the real cause instead
        # of letting the caller run into an unexplained timeout
        self.exception = exception
        self._transport.close()

    def connection_lost(self, exception: Exception):
        # a clean close (exception None) must not hide an error_received() cause
        if exception is not None:
            self.exception = exception
        if not self.done.done():
            self.done.set_result(True)

    def wait(self, timeout: float = DEFAULT_TIMEOUT):
        return asyncio.wait_for(self.done, timeout=timeout)


class BACnetClient:
    def __init__(
        self,
        address: str,
        port: int = DEFAULT_BACNET_PORT,
        timeout: float = DEFAULT_TIMEOUT,
        read_retries: int = DEFAULT_READ_RETRIES,
    ):
        """BACnet/IP client for one unit.

        timeout -- seconds to wait for each answer
        read_retries -- extra attempts for a read after a timeout (writes are never retried)
        """
        self.address = address
        self.port = port
        self.timeout = timeout
        self.read_retries = read_retries

        # The units answer one request at a time (~90 ms each on a Nordic
        # CL4); with ~10 requests in flight the last one exceeds a 1 s timeout
        # and more make the unit answer Abort out-of-resources. Requests from
        # one client are therefore sent one after another.
        self._lock = asyncio.Lock()

    async def _send(self, request: bytes) -> bytes:
        async with self._lock:
            return await self._send_unlocked(request)

    async def _send_unlocked(self, request: bytes) -> bytes:
        loop = asyncio.get_running_loop()

        bacnet_request = BACnetRequest(request)

        transport, _ = await loop.create_datagram_endpoint(
            lambda: bacnet_request, remote_addr=(self.address, self.port)
        )

        try:
            await bacnet_request.wait(timeout=self.timeout)
        finally:
            transport.close()

        if isinstance(bacnet_request.exception, DecodingError):
            raise bacnet_request.exception

        if bacnet_request.exception is not None:
            raise ConnectionError(str(bacnet_request.exception)) from bacnet_request.exception

        return bacnet_request.response

    async def read_multiple(
        self, device_properties: List[DeviceProperty]
    ) -> DeviceState:
        """Read the present value of many properties.

        The list is read in chunks of READ_MULTIPLE_MAX_PROPERTIES so that
        every request stays within the unit's max-APDU (see the constant).
        """
        device_state: DeviceState = {}

        for start in range(0, len(device_properties), READ_MULTIPLE_MAX_PROPERTIES):
            chunk = device_properties[start:start + READ_MULTIPLE_MAX_PROPERTIES]
            device_state.update(await self._read_multiple_chunk(chunk))

        return device_state

    async def _read_multiple_chunk(
        self, device_properties: List[DeviceProperty]
    ) -> DeviceState:
        request = _read_property_multiple(device_properties)

        if DEBUG:
            print(f">>> {request.hex()}")

        for attempt in range(self.read_retries + 1):
            try:
                response = await self._send(request)
                break
            except asyncio.TimeoutError:
                # a lost datagram is not a reason to fail the whole update
                if attempt == self.read_retries:
                    raise

        if DEBUG:
            print(f"<<< {response.hex()}")

        try:
            return _parse_read_property_multiple_response(response)
        except BACnetError:
            raise
        except DecodingError as exc:
            raise DecodingError(
                f"response decoding failed: {exc}\n{response.hex()}"
            ) from exc

    async def write(self, device_property: DeviceProperty, value: Any):
        request = _write_property(device_property, value)

        response = await self._send(request)

        try:
            return _parse_write_property_response(response)
        except BACnetError:
            raise
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
