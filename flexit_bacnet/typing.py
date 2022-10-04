from typing import Tuple, Any, List, Dict

ObjectIdentifier = Tuple[str, int]
ObjectProperties = List[Tuple[str, Any]]
DeviceState = Dict[ObjectIdentifier, ObjectProperties]
