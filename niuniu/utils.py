import asyncio
from typing import Any, ClassVar


class UserState:
    _state: ClassVar[dict[str, dict[Any, Any]]] = {
        "buff_map": {},
        "fence_time_map": {},
        "fenced_time_map": {},
        "gluing_time_map": {},
    }
    _lock: ClassVar[asyncio.Lock] = asyncio.Lock()

    @classmethod
    def _get_state(cls, name: str) -> dict[Any, Any]:
        if name not in cls._state:
            raise KeyError(f"Dictionary '{name}' not found in UserState")
        return cls._state[name]

    @classmethod
    def _update_key(cls, dic: dict[Any, Any], key: Any, data: Any) -> Any:
        dic[key] = data
        return data

    @classmethod
    def _get_key(cls, dic: dict[Any, Any], key: Any, default: Any) -> Any:
        return dic.get(key, default)

    @classmethod
    async def update(cls, name: str, key: Any, data: Any) -> Any:
        async with cls._lock:
            dictionary = cls._get_state(name)
            return cls._update_key(dictionary, key, data)

    @classmethod
    async def get(cls, name: str, key: Any = None, default: Any = None) -> Any:
        # No lock needed for read-only, unless consistency is required
        dictionary = cls._get_state(name)
        return dictionary if key is None else cls._get_key(dictionary, key, default)

    @classmethod
    async def del_key(cls, name: str, key: Any = None) -> None:
        """
        删除字典中的某个键或清空字典:
        - 如果提供了 `key`，则删除对应键。
        - 如果未提供 `key`，则清空整个字典。
        """
        async with cls._lock:
            if name not in cls._state:
                raise KeyError(f"Dictionary '{name}' not found in UserState")

            if key is None:
                cls._state[name].clear()  # 清空字典
            elif key in cls._state[name]:
                del cls._state[name][key]  # 删除指定键
            else:
                raise KeyError(f"Key '{key}' not found in dictionary '{name}'")
