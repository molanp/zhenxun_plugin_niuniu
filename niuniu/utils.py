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
    async def set_or_get(cls, name: str, key: Any = None, data: Any = None, default = None) -> Any:
        """
        设置键值对或获取字典内容:
        - 如果提供了 `data`，则更新字典中的 `key`。
        - 如果仅提供 `key`，则返回对应键的值。
        - 如果未提供 `key` 和 `data`，则返回整个字典内容。
        """
        async with cls._lock:
            if name not in cls._state:
                raise KeyError(f"Dictionary '{name}' not found in UserState")

            if data is not None:  # 更新键值对
                cls._state[name][key] = data
                return data
            elif key is not None:  # 获取键值
                return cls._state[name].get(key, default)
            else:  # 获取整个字典
                return cls._state[name]

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