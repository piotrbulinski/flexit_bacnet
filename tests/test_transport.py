"""Transport behaviour seen on a real Nordic CL4: segmentation, send errors, lost answers, concurrency."""

import asyncio
import functools
import time

import pytest

from flexit_bacnet import bacnet, nordic
from flexit_bacnet.bacnet import (
    BACnetClient,
    BACnetRequest,
    ReadValue,
    _apdu_from_response,
    _parse_read_property_multiple_response,
    _segment_ack,
)

from conftest import load_recorded


def run_async(test):
    """Run an async test function with asyncio.run (no pytest plugin needed)."""

    @functools.wraps(test)
    def wrapper(*args, **kwargs):
        return asyncio.run(test(*args, **kwargs))

    return wrapper

SEGMENTED = load_recorded("nordic_cl4_rer", "segmented_present_value_and_name")
UPDATE = load_recorded("nordic_cl4_rer", "update")


class _FakeTransport:
    def __init__(self, protocol):
        self.protocol = protocol
        self.sent = []
        self.closed = False

    def sendto(self, data, addr=None):
        self.sent.append(data)

    def close(self):
        if not self.closed:
            self.closed = True
            self.protocol.connection_lost(None)


def _request():
    request = BACnetRequest(b"request")
    transport = _FakeTransport(request)
    request.connection_made(transport)
    transport.sent.clear()
    return request, transport


def _segments(body: bytes, count: int, window: int = 4):
    """Split a ComplexACK body into `count` recorded-style segments (invoke 1, RPM)."""
    size = -(-len(body) // count)
    parts = [body[i * size:(i + 1) * size] for i in range(count)]
    datagrams = []
    for seq, part in enumerate(parts):
        more = 0x04 if seq < count - 1 else 0
        apdu = bytes([0x38 | more, 1, seq, window, 14]) + part
        datagrams.append(bytes([0x81, 0x0A]) + (6 + len(apdu)).to_bytes(2, "big") + b"\x01\x00" + apdu)
    return datagrams


def _update_body() -> bytes:
    return _apdu_from_response(UPDATE.response)[3:]


def _ack_seqs(sent):
    return [(d[6] & 0x02 == 0x02, d[8], d[9]) for d in sent]


@run_async
async def test_recorded_segments_are_acked_and_reassembled():
    request, transport = _request()

    first, second, last = SEGMENTED.responses

    request.datagram_received(first, ("unit", 47808))
    # the first segment is always acknowledged; it sets the window size (4)
    assert _ack_seqs(transport.sent) == [(False, 0, 4)]

    request.datagram_received(second, ("unit", 47808))
    assert len(transport.sent) == 1
    assert not transport.closed

    request.datagram_received(last, ("unit", 47808))
    assert _ack_seqs(transport.sent) == [(False, 0, 4), (False, 2, 4)]
    assert transport.closed

    state = _parse_read_property_multiple_response(request.response)
    assert len(state) == len(nordic.DEVICE_PROPERTIES)


@run_async
async def test_acks_once_per_window():
    request, transport = _request()

    for datagram in _segments(_update_body(), 9):
        request.datagram_received(datagram, ("unit", 47808))

    # ack 0 (window set up), then the last segment of each window of 4, then the final one
    assert [seq for _, seq, _ in _ack_seqs(transport.sent)] == [0, 4, 8]
    assert _parse_read_property_multiple_response(request.response) == (
        _parse_read_property_multiple_response(UPDATE.response)
    )


@run_async
async def test_duplicate_segments_are_discarded():
    # the unit repeats segment 0 every ~6 s until it is acknowledged, and
    # repeats a window when an ack is lost
    request, transport = _request()
    segments = _segments(_update_body(), 6)

    for index in (0, 0, 1, 2, 1, 3, 4, 2, 5):
        request.datagram_received(segments[index], ("unit", 47808))

    assert transport.closed
    assert _parse_read_property_multiple_response(request.response) == (
        _parse_read_property_multiple_response(UPDATE.response)
    )


@run_async
async def test_out_of_order_segment_is_negatively_acked():
    request, transport = _request()
    segments = _segments(_update_body(), 9)

    request.datagram_received(segments[0], ("unit", 47808))
    request.datagram_received(segments[6], ("unit", 47808))

    assert _ack_seqs(transport.sent)[-1] == (True, 0, 4)
    assert not transport.closed

    # the unit resends from segment 1
    for datagram in segments[1:]:
        request.datagram_received(datagram, ("unit", 47808))

    assert transport.closed
    assert _parse_read_property_multiple_response(request.response) == (
        _parse_read_property_multiple_response(UPDATE.response)
    )


@run_async
async def test_window_is_capped():
    request, transport = _request()
    segments = _segments(_update_body(), 3, window=127)

    request.datagram_received(segments[0], ("unit", 47808))

    assert _ack_seqs(transport.sent) == [(False, 0, bacnet.MAX_SEGMENT_WINDOW)]


@run_async
async def test_segment_ack_encoding():
    # BVLC unicast, NPDU without expecting reply, SegmentACK (client, NAK bit 1)
    assert _segment_ack(1, 4, 4).hex() == "810a000a0100" + "40010404"
    assert _segment_ack(1, 0, 4, negative=True).hex() == "810a000a0100" + "42010004"


@run_async
async def test_send_error_fails_fast_with_real_cause():
    # Seen live: sendto() to an unreachable LAN address fails at once with
    # EHOSTUNREACH; the request must fail with that cause, not after the timeout.
    request, transport = _request()

    request.error_received(OSError(65, "No route to host"))

    assert await request.wait(timeout=0.1)
    assert isinstance(request.exception, OSError)


@run_async
async def test_clean_close_does_not_hide_send_error():
    request, transport = _request()

    request.error_received(OSError(65, "No route to host"))
    request.connection_lost(None)

    assert isinstance(request.exception, OSError)


class _FakeUnit(asyncio.DatagramProtocol):
    """UDP server on localhost that behaves like the CL4 for one recorded answer."""

    def __init__(self, segments=None, drop_first=0, delay=0.0):
        self.segments = segments or [UPDATE.response]
        self.drop_first = drop_first
        self.delay = delay
        self.requests = []
        self.in_flight = 0
        self.max_in_flight = 0

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        apdu_type = data[6] >> 4

        if apdu_type == bacnet.APDUType.SEGMENT_ACK:
            seq = data[8]
            for segment in self.segments[seq + 1: seq + 1 + data[9]]:
                self.transport.sendto(segment, addr)
            return

        self.requests.append(data)
        if len(self.requests) <= self.drop_first:
            return

        asyncio.get_running_loop().create_task(self._answer(addr))

    async def _answer(self, addr):
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        await asyncio.sleep(self.delay)
        self.in_flight -= 1
        # like the unit: the first segment alone, the rest after its ack
        self.transport.sendto(self.segments[0], addr)


async def start_fake_unit(**kwargs):
    unit = _FakeUnit(**kwargs)
    transport, _ = await asyncio.get_running_loop().create_datagram_endpoint(
        lambda: unit, local_addr=("127.0.0.1", 0)
    )
    return unit, transport.get_extra_info("sockname")[1]


@run_async
async def test_client_reads_segmented_answer():
    unit, port = await start_fake_unit(segments=SEGMENTED.responses)
    client = BACnetClient("127.0.0.1", port)

    state = await client.read_multiple(nordic.DEVICE_PROPERTIES)

    assert dict(state[nordic.SUPPLY_AIR_TEMPERATURE.object_identifier])[ReadValue.OBJECT_NAME] == "R(1)'TSu"


@run_async
async def test_client_retries_read_after_lost_answer():
    unit, port = await start_fake_unit(drop_first=1)
    client = BACnetClient("127.0.0.1", port, timeout=0.2)

    state = await client.read_multiple(nordic.DEVICE_PROPERTIES)

    assert len(unit.requests) == 2
    assert len(state) == len(nordic.DEVICE_PROPERTIES) + 1


@run_async
async def test_client_gives_up_after_retries():
    unit, port = await start_fake_unit(drop_first=10)
    client = BACnetClient("127.0.0.1", port, timeout=0.1, read_retries=2)

    with pytest.raises(asyncio.TimeoutError):
        await client.read_multiple(nordic.DEVICE_PROPERTIES)

    assert len(unit.requests) == 3


@run_async
async def test_concurrent_reads_are_sent_one_at_a_time():
    # The CL4 serves one request at a time (~90 ms); 10 parallel requests
    # pushed the last one to ~1 s and 15 got Abort out-of-resources.
    unit, port = await start_fake_unit(delay=0.05)
    client = BACnetClient("127.0.0.1", port, timeout=0.5)

    started = time.perf_counter()
    results = await asyncio.gather(*(client.read_multiple(nordic.DEVICE_PROPERTIES) for _ in range(5)))

    assert unit.max_in_flight == 1
    assert len(results) == 5
    # each request gets its full timeout: waiting for the lock does not count
    assert time.perf_counter() - started >= 0.25
