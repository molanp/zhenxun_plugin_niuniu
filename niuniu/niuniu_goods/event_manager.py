import random
import time
from typing import Any

from ..config_loader import GlueEvent, PropModel, load_events
from ..niuniu import NiuNiu
from ..utils import UserState
from .goods import get_prop_by_name


async def apply_buff(uid: str, event: Any) -> None:
    """应用 Buff 效果"""
    if not event.buff:
        return  # 如果事件没有 Buff，则直接返回

    # 检查 Buff 是否有效
    if event.buff.effect is not None and event.buff.duration is not None:
        await UserState.set_or_get("buff_map", uid, {
            "effect": event.buff.effect,
            "expire_time": time.time() + event.buff.duration,
        })


def choose_description(
    diff: float,
    positive_descs: list[str] | None,
    negative_descs: list[str] | None,
    no_change_descs: list[str] | None,
) -> tuple[str, bool]:
    """选择随机描述"""
    if diff > 0 and positive_descs:
        return random.choice(positive_descs), False
    elif diff < 0 and negative_descs:
        return random.choice(negative_descs), True
    elif diff == 0 and no_change_descs:
        return random.choice(no_change_descs), False
    return random.choice(positive_descs or negative_descs or ["无描述"]), False


async def process_glue_event(
    uid: str,
    origin_length: float,
    is_rapid: bool,
) -> tuple[str, float, float]:
    """处理打胶事件"""

    events = await adjust_glue_effects(uid)

    # 检查是否有 Buff 效果
    buff = await get_buffs(uid)
    if buff.get("expire_time", 0) > time.time():
        origin_length = origin_length * buff.get("effect", 1)

    # 根据权重选择事件
    event_names = list(events.keys())
    weights = [e.weight for e in events.values()]
    selected = random.choices(event_names, weights=weights, k=1)[0]
    event = events[selected]

    # 处理连续打胶事件
    if is_rapid and event.rapid_effect:
        rapid_effect = event.rapid_effect
        if rapid_effect.coefficient:
            new_length, diff = await NiuNiu.gluing(
                origin_length, rapid_effect.coefficient
            )
        elif rapid_effect.effect:
            new_length = round(abs(origin_length) * rapid_effect.effect, 2)
            diff = new_length - origin_length
        else:
            new_length = origin_length
            diff = 0

        desc_template, need_abs = choose_description(
            diff,
            rapid_effect.positive_descriptions,
            rapid_effect.negative_descriptions,
            rapid_effect.no_change_descriptions,
        )
        result = desc_template.format(
            diff=round(abs(diff) if need_abs else diff, 2),
            new_length=round(new_length, 2),
            ban_time=rapid_effect.ban_time,
        )
    else:
        # 处理普通事件逻辑
        if event.category in ["growth", "special"]:
            new_length, diff = await NiuNiu.gluing(origin_length, event.coefficient)
        elif event.category == "reduce":
            new_length, diff = await NiuNiu.gluing(origin_length, reduce=True)
        elif event.category == "shrinkage":
            new_length = round(abs(origin_length) * event.effect, 2)
            diff = new_length - origin_length
        elif event.category == "arrested":
            new_length = origin_length
            diff = 0
        else:
            raise ValueError(f"Invalid event category: {event.category}")

        # 应用 Buff 效果
        if event.buff:
            await apply_buff(uid, event)

        # 处理连续子事件
        # if event.next_event and event.next_event in events:
        #     result, new_length, diff = await process_glue_event(
        #         uid, new_length, is_rapid
        #     )
        #     return result, new_length, diff

        desc_template, need_abs = choose_description(
            diff,
            event.positive_descriptions,
            event.negative_descriptions,
            event.no_change_descriptions,
        )
        result = desc_template.format(
            diff=round(abs(diff) if need_abs else diff, 2),
            new_length=round(new_length, 2),
            ban_time=event.ban_time,
        )

    return result, new_length, diff


async def use_prop(uid: str, prop_name: str) -> tuple[str, int, int]:
    """使用道具来调整击剑胜率和打胶效果"""
    prop = get_prop_by_name(prop_name)
    if prop is None:
        return "无效的道具", 0, 0

    # 计算过期时间
    expire_time = time.time() + prop.duration

    # 更新道具状态
    await UserState.set_or_get("buff_map", uid, prop.expire_time=expire_time,
    )

    return (
        f"使用了 {prop.name}，效果持续至 {time.ctime(expire_time)}",
        0,
        0,
    )


async def adjust_glue_effects(uid: str) -> dict[str, GlueEvent]:
    events = await load_events()
    buff = await get_buffs(uid)
    glue_effect = buff.get("glue_effect", 1)

    for event in events.values():
        if event.affected_by_props:
           if event.coefficient:
                event.coefficient *= glue_effect
           if event.effect:
                event.effect = event.effect * glue_effect
           if event.category in ["shrinkage", "arrested"]:
                event.weight *= buff.get("glue_negative_weight", 1)
    return events


async def get_buffs(uid: str) -> Any | None:
    """
    获取用户的 buff，如果已过期，则清除并返回空。
    
    :param uid: 用户的唯一标识
    :return: 用户的 buff 信息（未过期）或 None
    """
    # 获取 buff 信息
    buff_info = await UserState.set_or_get("buff_map", uid, default=None)

    # 如果 buff 存在且未过期
    if buff_info and buff_info.expire_time > time.time():
        return buff_info

    # 清除过期道具
    await UserState.del_key("buff_map", uid)

    # 返回空，表示该用户的 buff 已过期
    return None