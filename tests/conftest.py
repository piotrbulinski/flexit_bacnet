import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


class Recorded:
    """A request and the datagram(s) a real unit answered it with.

    Recorded with tests/live/record_fixtures.py; serial numbers are scrubbed.
    """

    def __init__(self, path: Path):
        data = json.loads(path.read_text())
        self.name = path.stem
        self.unit = data["unit"]
        self.note = data["note"]
        self.request = bytes.fromhex(data["request"])
        self.responses = [bytes.fromhex(r) for r in data["responses"]]

    @property
    def response(self) -> bytes:
        assert len(self.responses) == 1, f"{self.name} has {len(self.responses)} datagrams"
        return self.responses[0]

    def reassembled(self) -> bytes:
        """The answer as one datagram: segments (if the unit sent several) put together."""
        from flexit_bacnet import bacnet

        if len(self.responses) == 1:
            return self.responses[0]

        assembler = bacnet._SegmentAssembler()
        complete = None
        for datagram in self.responses:
            _, complete = assembler.add(datagram, bacnet._apdu_from_response(datagram))

        assert complete is not None, f"{self.name}: segments do not reassemble"
        return complete

    def requested_objects(self) -> set:
        """Object identifiers the recorded readPropertyMultiple request asked for."""
        from flexit_bacnet.bacnet import BACnetDecoder, _apdu_from_response

        decoder = BACnetDecoder(_apdu_from_response(self.request), 4)
        objects = set()
        while not decoder.eof():
            objects.add(decoder.parse_object_identifier())
            # skip the property references up to the closing tag 1
            tag_number, tag_type = decoder.read_context_tag()
            while True:
                tag_number, tag_class, length = decoder.read_tag()
                if tag_class == 1 and tag_number == 1 and length == 7:
                    break
                decoder.read_bytes(length)
        return objects


def load_recorded(unit: str, name: str) -> Recorded:
    return Recorded(FIXTURES / unit / f"{name}.json")


@pytest.fixture
def cl4():
    """Loader for answers recorded from a Nordic CL4 RER (POS3.67, HvacFnct21y_A v2.425)."""
    return lambda name: load_recorded("nordic_cl4_rer", name)
