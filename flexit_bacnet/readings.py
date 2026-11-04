"""Metadata (label and unit) for the values FlexitBACnet exposes.

Getters are marked with `@reading(...)` under `@property`, so they stay plain
properties (and keep their return types for type checkers) while consumers
can look up how to render them:

    for info in FlexitBACnet.readings():
        value = getattr(device, info.name)
        print(f"{info.label}: {info.format(value)}")

    FlexitBACnet.get_reading("extract_air_humidity").unit  # Unit.PERCENT
"""
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Callable, Optional, TypeVar

UNSUPPORTED = "(unsupported)"

_ATTRIBUTE = "__flexit_reading__"

F = TypeVar("F", bound=Callable[..., Any])


class Unit(StrEnum):
    """Unit of a reading; the value is its display symbol."""

    CELSIUS = "°C"
    KELVIN = "K"
    PERCENT = "%"
    KILOWATT = "kW"
    RPM = "rpm"
    HOURS = "h"
    MINUTES = "min"
    SECONDS = "s"


@dataclass(frozen=True)
class Reading:
    """Label and unit of one FlexitBACnet property."""

    name: str
    label: str
    unit: Optional[Unit] = None

    def format(self, value: Any) -> str:
        """Render a value of this reading, e.g. "21.5 °C" or "(unsupported)" for None."""
        if value is None:
            return UNSUPPORTED

        if self.unit is None:
            return str(value)

        return f"{value} {self.unit}"


def reading(label: str, unit: Optional[Unit] = None) -> Callable[[F], F]:
    """Attach a label and unit to a getter. Apply it below `@property`."""

    def decorator(fget: F) -> F:
        setattr(fget, _ATTRIBUTE, Reading(fget.__name__, label, unit))
        return fget

    return decorator


def collect_readings(cls: type) -> list[Reading]:
    """Return the readings declared on cls (and its bases), in definition order."""
    found: dict[str, Reading] = {}

    for klass in reversed(cls.__mro__):
        for name, member in vars(klass).items():
            if isinstance(member, property):
                info = getattr(member.fget, _ATTRIBUTE, None)
                if info is not None:
                    found[name] = info

    return list(found.values())
