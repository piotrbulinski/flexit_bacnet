"""Find the unit's objects by name when they are not where the mapping expects them.

BACnet reads address an object by its identifier (type and instance number),
but the instance numbers on Flexit units differ between models and firmware
versions, even within one product line: the air filter reset is
multiStateValue 613 on a Nordic S4 and CL4 and 609 on a Nordic S3, and the
extract air temperature is analogInput 59 on one and 95 on the other. The
object names (e.g. "R(1)'HVAC'AlmBdl'FilRpcRst") are the same everywhere.

So the identifiers in nordic.py/econordic.py are treated as hints. On the
first update() FlexitBACnet calls resolve_objects(), which

1. reads the object-name of every mapped object that has an object_name, at
   its hinted identifier (about 70 objects, 2 requests);
2. for every object whose name does not match there (the object is missing
   or something else is in its place), reads the unit's object-list and the
   names of the objects of the same type, and moves the object to where its
   name is. Objects keep their type when they move, so only those types are
   read: not all of the ~1800 objects of a unit.

An object whose name is not found anywhere keeps its hinted identifier, so a
unit that does not have an object still reports it as missing (None), as
before. Nothing is written to the unit.
"""
import logging
from types import ModuleType, SimpleNamespace
from typing import Any, Dict, List, Optional, Set, Tuple

from flexit_bacnet.bacnet import (
    BACnetError,
    DeviceProperty,
    DeviceState,
    ObjectIdentifier,
    ObjectType,
    ReadValue,
)

_LOGGER = logging.getLogger(__name__)

# the answer had no object-name for the object at all (e.g. a unit or a test
# double that only answers present-value): nothing to compare, keep the hint
_UNANSWERED = object()

# constant name -> (hinted identifier, identifier found by name)
Relocations = Dict[str, Tuple[ObjectIdentifier, ObjectIdentifier]]


async def resolve_objects(client: Any, device_id: int, module: ModuleType) -> Tuple[SimpleNamespace, Relocations]:
    """Return the module's constants with every named object at its identifier on this unit.

    The result has the same attributes as the module (including
    DEVICE_PROPERTIES), so it can be used in its place. The module itself is
    not changed: two units of one product line can have different numbers.
    """
    constants = {name: value for name, value in vars(module).items() if name.isupper()}
    named = {
        name: value for name, value in constants.items()
        if isinstance(value, DeviceProperty) and value.object_name
    }

    unresolved = await _unverified(client, named)

    relocations: Relocations = {}
    if unresolved:
        found = await _find_by_name(
            client,
            device_id,
            object_types={p.object_type for p in unresolved.values()},
            names={p.object_name for p in unresolved.values() if p.object_name},
        )

        for constant, device_property in unresolved.items():
            identifier = found.get(device_property.object_name)
            if identifier is None or identifier == device_property.object_identifier:
                continue

            constants[constant] = device_property.moved_to(*identifier)
            relocations[constant] = (device_property.object_identifier, identifier)
            _LOGGER.info(
                "%s (%s) is at %s on this unit, not at %s",
                constant, device_property.object_name, _format(identifier), _format(device_property.object_identifier),
            )

    constants["DEVICE_PROPERTIES"] = [value for value in constants.values() if isinstance(value, DeviceProperty)]

    return SimpleNamespace(**constants), relocations


async def _unverified(client: Any, named: Dict[str, DeviceProperty]) -> Dict[str, DeviceProperty]:
    """Return the named objects whose name does not match at their hinted identifier."""
    if not named:
        return {}

    by_identifier = {p.object_identifier: p for p in named.values()}
    state = await client.read_multiple([p.reading(ReadValue.OBJECT_NAME) for p in by_identifier.values()])

    unresolved = {}
    for constant, device_property in named.items():
        actual = _object_name(state, device_property.object_identifier)
        if actual is _UNANSWERED:
            continue

        # a PropertyError (unknown-object) or another object in its place
        if actual != device_property.object_name:
            unresolved[constant] = device_property

    return unresolved


async def _find_by_name(
    client: Any, device_id: int, object_types: Set[Any], names: Set[str]
) -> Dict[str, ObjectIdentifier]:
    """Return the identifier of each of names on the unit, searching objects of object_types."""
    device = DeviceProperty(ObjectType.DEVICE, device_id, read_values=[ReadValue.OBJECT_LIST])

    try:
        state = await client.read_multiple([device])
    except BACnetError as exc:
        # e.g. an object-list too large to be sent: keep the hints
        _LOGGER.warning("cannot read the object list to find moved objects: %s", exc)
        return {}

    object_list = dict(state.get(device.object_identifier, ())).get(ReadValue.OBJECT_LIST)
    if not isinstance(object_list, list):
        return {}

    candidates: List[DeviceProperty] = [
        DeviceProperty(identifier[0], identifier[1], read_values=[ReadValue.OBJECT_NAME])
        for identifier in object_list
        if isinstance(identifier, tuple) and identifier[0] in object_types
    ]
    if not candidates:
        return {}

    names_state = await client.read_multiple(candidates)

    found: Dict[str, ObjectIdentifier] = {}
    for identifier in names_state:
        name = _object_name(names_state, identifier)
        if isinstance(name, str) and name in names:
            found[name] = identifier

    return found


def _object_name(state: DeviceState, identifier: ObjectIdentifier) -> Optional[Any]:
    values = dict(state.get(identifier, ()))
    if ReadValue.OBJECT_NAME not in values:
        return _UNANSWERED

    return values[ReadValue.OBJECT_NAME]


def _format(identifier: ObjectIdentifier) -> str:
    object_type, instance = identifier
    return f"{getattr(object_type, 'name', object_type)} {instance}"
