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


def load_recorded(unit: str, name: str) -> Recorded:
    return Recorded(FIXTURES / unit / f"{name}.json")


@pytest.fixture
def cl4():
    """Loader for answers recorded from a Nordic CL4 RER (POS3.67, HvacFnct21y_A v2.425)."""
    return lambda name: load_recorded("nordic_cl4_rer", name)
