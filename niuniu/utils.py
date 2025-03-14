from typing import Any, ClassVar


class UserState:
    _state: ClassVar[dict[str, dict[Any, Any]]] = {
        "buff_map": {},
        "prop_map": {},
        "fence_time_map": {},
        "fenced_time_map": {},
        "gluing_time_map": {},
    }

    @classmethod
    async def update(cls, name: str, value: dict[Any, Any]) -> None:
        if name in cls._state:
            cls._state[name] = value
        else:
            raise KeyError(f"Key '{name}' not found in UserState")

    @classmethod
    async def get(cls, name: str) -> dict[Any, Any]:
        if name in cls._state:
            return cls._state[name]
        else:
            raise KeyError(f"Key '{name}' not found in UserState")

