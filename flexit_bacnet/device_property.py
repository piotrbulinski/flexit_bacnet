from flexit_bacnet.typing import ObjectIdentifier

PRESENT_VALUE = 'presentValue'


class DeviceProperty:
    def __init__(self, object_type: str, instance_id: int, value_map: dict[int, str] | None = None,
                 read_values: list[str] | None = None, priority: int | None = None):
        self.object_type = object_type
        self.instance_id = instance_id
        self.value_map = value_map
        self.read_values = read_values if read_values is not None else [PRESENT_VALUE]
        self.priority = priority

    @property
    def object_identifier(self) -> ObjectIdentifier:
        return self.object_type, self.instance_id

    @property
    def object_path(self) -> str:
        return f'{self.object_type}:{self.instance_id}'
