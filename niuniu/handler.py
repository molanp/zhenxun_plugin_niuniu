import base64
import contextlib
from pathlib import Path
import random
import time

import aiofiles
from arclet.alconna import Args
from nonebot import get_driver, on_command
from nonebot_plugin_alconna import Alconna, At, Image, Match, Text, UniMsg, on_alconna
from nonebot_plugin_htmlrender import template_to_pic
from nonebot_plugin_uninfo import Uninfo
from tortoise.exceptions import DoesNotExist

from zhenxun.configs.path_config import DATA_PATH
from zhenxun.models.user_console import UserConsole
from zhenxun.plugins.niuniu.utils import UserState
from zhenxun.utils.enum import GoldHandle
from zhenxun.utils.message import MessageUtils
from zhenxun.utils.platform import PlatformUtils

from .config import (
    FENCE_COOLDOWN,
    FENCED_PROTECTION,
    GLUE_COOLDOWN,
    QUICK_GLUE_COOLDOWN,
    UNSUBSCRIBE_GOLD,
)
from .database import Sqlite
from .fence import Fencing
from .model import NiuNiuUser
from .niuniu import NiuNiu
from .niuniu_goods.event_manager import get_current_prop, process_glue_event

niuniu_register = on_alconna(
    Alconna("注册牛牛"),
    priority=5,
    block=True,
)
niuniu_unsubscribe = on_alconna(
    Alconna("注销牛牛"),
    priority=5,
    block=True,
)
niuniu_fencing = on_command(
    "击剑",
    aliases={"JJ", "Jj", "jJ", "jj"},
    priority=5,
    block=True,
)
niuniu_my = on_alconna(
    Alconna("我的牛牛"),
    priority=5,
    block=True,
)
niuniu_length_rank = on_alconna(
    Alconna("牛牛长度排行", Args["num?", int, 10]),
    priority=5,
    block=True,
)
niuniu_deep_rank = on_alconna(
    Alconna("牛牛深度排行", Args["num?", int, 10]),
    priority=5,
    block=True,
)
niuniu_length_rank_all = on_alconna(
    Alconna("牛牛长度总排行", Args["num?", int, 10]),
    priority=5,
    block=True,
)
niuniu_deep_rank_all = on_alconna(
    Alconna("牛牛深度总排行", Args["num?", int, 10]),
    priority=5,
    block=True,
)
niuniu_hit_glue = on_alconna(
    Alconna("打胶"),
    priority=5,
    block=True,
)

niuniu_my_record = on_alconna(
    Alconna("我的牛牛战绩", Args["num?", int, 10]),
    priority=5,
    block=True,
)


driver = get_driver()


@driver.on_startup
async def start():
    old_data_path = Path(__file__).resolve().parent / "data" / "long.json"
    if old_data_path.exists():
        async with aiofiles.open(old_data_path, encoding="utf-8") as f:
            file_data = f.read()
        await Sqlite.json2db(file_data)
        old_data_path.unlink()
    if Path(DATA_PATH / "niuniu" / "data.db").exists():
        await Sqlite.sqlite2db()
    return


@niuniu_register.handle()
async def _(session: Uninfo):
    uid = str(session.user.id)
    if await NiuNiuUser.filter(uid=uid).exists():
        await niuniu_register.send(Text("你已经有过牛牛啦！"), reply_to=True)
        return
    length = await NiuNiu.random_length()
    await NiuNiuUser.create(uid=uid, length=length)
    await NiuNiu.record_length(uid, 0, length, "register")
    await niuniu_register.send(Text(f"牛牛长出来啦！足足有{length}cm呢"), reply_to=True)


@niuniu_unsubscribe.handle()
async def _(session: Uninfo):
    uid = str(session.user.id)
    length = await NiuNiu.get_length(uid)
    if length is None:
        await niuniu_unsubscribe.send(
            Text("你还没有牛牛呢！\n请发送'注册牛牛'领取你的牛牛!"), reply_to=True
        )
        return
    gold = (await UserConsole.get_user(uid)).gold
    if gold < UNSUBSCRIBE_GOLD:
        await niuniu_unsubscribe.send(
            Text(f"你的金币不足{UNSUBSCRIBE_GOLD}，无法注销牛牛！"), reply_to=True
        )
    else:
        await UserConsole.reduce_gold(
            uid, UNSUBSCRIBE_GOLD, GoldHandle.PLUGIN, "niuniu"
        )
        await NiuNiuUser.filter(uid=uid).delete()
        await NiuNiu.record_length(uid, length, 0, "unsubscribe")
        await niuniu_unsubscribe.finish(Text("从今往后你就没有牛牛啦！"), reply_to=True)


@niuniu_fencing.handle()
async def _(session: Uninfo, msg: UniMsg):
    at_list = [i.target for i in msg if isinstance(i, At)]
    uid = session.user.id
    fence_time_map = await UserState.get("fence_time_map")
    fenced_time_map = await UserState.get("fenced_time_map")
    with contextlib.suppress(KeyError):
        time_pass = int(time.time() - fence_time_map.get(uid, 0))
        if time_pass < FENCE_COOLDOWN:
            time_rest = FENCE_COOLDOWN - time_pass
            jj_refuse = [
                f"才过去了{time_pass}s时间,你就又要击剑了，真是饥渴难耐啊",
                f"不行不行，你的身体会受不了的，歇{time_rest}s再来吧",
                f"你这种男同就应该被送去集中营！等待{time_rest}s再来吧",
                f"打咩哟！你的牛牛会炸的，休息{time_rest}s再来吧",
            ]
            await niuniu_fencing.send(random.choice(jj_refuse), reply_message=True)
            return
    if not at_list:
        await niuniu_fencing.send("你要和谁击剑？你自己吗？", reply_message=True)
        return
    my_long = await NiuNiu.get_length(uid)
    try:
        if my_long is None:
            raise RuntimeError(
                "你还没有牛牛呢！不能击剑！\n请发送'注册牛牛'领取你的牛牛!"
            )
        at = str(at_list[0])
        if len(at_list) >= 2:
            raise RuntimeError(
                random.choice(
                    ["一战多？你的小身板扛得住吗？", "你不准参加Impart┗|｀O′|┛"]
                )
            )
        if at == uid:
            raise RuntimeError("不能和自己击剑哦！")
        opponent_long = await NiuNiu.get_length(at)
        if opponent_long is None:
            raise RuntimeError("对方还没有牛牛呢！不能击剑！")
        # 被击剑者冷却检查
        if fenced_time_map.get(at) is None:
            fenced_time = await NiuNiu.last_fenced_time(at)
        else:
            fenced_time = fenced_time_map[at]
        fenced_time_pass = int(time.time() - fenced_time)
        if fenced_time_pass < FENCED_PROTECTION:  # 5分钟保护期
            tips = [
                f"对方刚被击剑过，需要休息{FENCED_PROTECTION - fenced_time_pass}秒才能再次被击剑",  # noqa: E501
                f"对方牛牛还在恢复中，{FENCED_PROTECTION - fenced_time_pass}秒后再来吧",
                f"禁止连续击剑同一用户！请等待{FENCED_PROTECTION - fenced_time_pass}秒",
            ]
            await niuniu_fencing.send(random.choice(tips), reply_message=True)
            return

        # 处理击剑逻辑
        result = await Fencing.fencing(my_long, opponent_long, at, uid)
        fence_time_map[uid] = time.time()   # 更新本地fence_time_map
        fenced_time_map[at] = time.time()     # 更新本地fenced_time_map

        # 更新数据
        await UserState.update(
            "fence_time_map",
            fence_time_map,
        )
        await UserState.update(
            "fenced_time_map",
            fenced_time_map,
        )
        await niuniu_fencing.send(result, reply_message=True)
    except RuntimeError as e:
        await niuniu_fencing.send(str(e), reply_message=True)


@niuniu_my.handle()
async def _(session: Uninfo):
    uid = int(session.user.id)
    if await NiuNiu.get_length(uid) is None:
        await niuniu_my.send(
            Text("你还没有牛牛呢！\n请发送'注册牛牛'领取你的牛牛!"), reply_to=True
        )
        return

    try:
        current_user = await NiuNiuUser.get(uid=uid)
    except DoesNotExist:
        await niuniu_my.send(Text("未查询到数据..."), reply_to=True)
        return

    # 计算排名逻辑
    rank = await NiuNiuUser.filter(length__gt=current_user.length).count() + 1

    # 构造结果数据
    user = {"uid": current_user.uid, "length": current_user.length, "rank": rank}
    avatar = await PlatformUtils.get_user_avatar(str(uid), "qq", session.self_id)
    avatar = "" if avatar is None else base64.b64encode(avatar).decode("utf-8")

    result = {
        "avatar": f"data:image/png;base64,{avatar}",
        "name": session.user.name,
        "rank": user["rank"],
        "my_length": user["length"],
        "latest_gluing_time": await NiuNiu.latest_gluing_time(uid),
        "comment": await NiuNiu.comment(user["length"]),
    }
    template_dir = Path(__file__).resolve().parent / "templates"
    pic = await template_to_pic(
        template_path=str(template_dir),
        template_name="my_info.html",
        templates=result,
    )
    await niuniu_my.send(Image(raw=pic), reply_to=True)


@niuniu_length_rank.handle()
async def _(session: Uninfo, match: Match[int]):
    if not match.available:
        match.result = 10
    if match.result > 50:
        await MessageUtils.build_message("排行榜人数不能超过50哦...").finish()
    gid = session.group.id if session.group else None
    if not gid:
        await MessageUtils.build_message(
            "私聊中无法查看 '牛牛长度排行'，请发送 '牛牛长度总排行'"
        ).finish()
    image = await NiuNiu.rank(match.result, session)
    await MessageUtils.build_message(image).send()


@niuniu_length_rank_all.handle()
async def _(session: Uninfo, match: Match[int]):
    if not match.available:
        match.result = 10
    if match.result > 50:
        await MessageUtils.build_message("排行榜人数不能超过50哦...").finish()
    image = await NiuNiu.rank(match.result, session, is_all=True)
    await MessageUtils.build_message(image).send()


@niuniu_deep_rank.handle()
async def _(session: Uninfo, match: Match[int]):
    if not match.available:
        match.result = 10
    if match.result > 50:
        await MessageUtils.build_message("排行榜人数不能超过50哦...").finish()
    gid = session.group.id if session.group else None
    if not gid:
        await MessageUtils.build_message(
            "私聊中无法查看 '牛牛深度排行'，请发送 '牛牛深度总排行'"
        ).finish()
    image = await NiuNiu.rank(match.result, session, True)
    await MessageUtils.build_message(image).send()


@niuniu_deep_rank_all.handle()
async def _(session: Uninfo, match: Match[int]):
    if not match.available:
        match.result = 10
    if match.result > 50:
        await MessageUtils.build_message("排行榜人数不能超过50哦...").finish()
    image = await NiuNiu.rank(match.result, session, True, is_all=True)
    await MessageUtils.build_message(image).send()


@niuniu_hit_glue.handle()
async def hit_glue(session: Uninfo):
    uid = session.user.id
    origin_length = await NiuNiu.get_length(uid)
    current_prop = await get_current_prop(uid)
    if origin_length is None:
        await niuniu_hit_glue.send(
            Text(
                random.choice(
                    [
                        "你还没有牛牛呢！不能打胶！\n请发送'注册牛牛'",
                        "无牛牛，打胶不要的!\n请发送'注册牛牛'",
                    ]
                )
            ),
            reply_to=True,
        )
        return

    # 检查冷却时间
    is_rapid_glue = False
    with contextlib.suppress(KeyError):
        time_pass = abs(
            int(time.time() - (await UserState.get("gluing_time_map")).get(uid, 0))
        )
        if time_pass < QUICK_GLUE_COOLDOWN:
            is_rapid_glue = True
        if time_pass < GLUE_COOLDOWN:
            time_rest = GLUE_COOLDOWN - time_pass
            glue_refuse = [
                f"才过去了{time_pass}s时间,你就又要打🦶了，身体受得住吗",
                f"不行不行，你的身体会受不了的，歇{time_rest}s再来吧",
                f"休息一下吧，会炸膛的！{time_rest}s后再来吧",
                f"打咩哟，你的牛牛会爆炸的，休息{time_rest}s再来吧",
            ]
            await niuniu_hit_glue.send(random.choice(glue_refuse), reply_to=True)
            return

    # 更新冷却时间
    await UserState.update(
        "gluing_time_map",
        {**await UserState.get("gluing_time_map"), uid: time.time()},
    )

    # 处理事件
    result, new_length, diff = await process_glue_event(
        uid, origin_length, is_rapid_glue, current_prop
    )

    # 更新数据
    await NiuNiu.update_length(uid, new_length)
    await NiuNiu.record_length(uid, origin_length, new_length, "gluing")

    # 发送结果
    await niuniu_hit_glue.send(Text(result), reply_to=True)


@niuniu_my_record.handle()
async def my_record(session: Uninfo, match: Match[int]):
    uid = session.user.id
    num = match.result if match.available else 10
    records = await NiuNiu.get_user_records(uid, num)

    if not records:
        await niuniu_my_record.send(Text("你还没有任何牛牛战绩哦~"), reply_to=True)
        return

    # 获取用户头像
    avatar_bytes = await PlatformUtils.get_user_avatar(str(uid), "qq", session.self_id)
    avatar = base64.b64encode(avatar_bytes).decode("utf-8") if avatar_bytes else ""

    # 构建模板数据
    result = {
        "avatar": f"data:image/png;base64,{avatar}",
        "name": session.user.name,
        "records": [
            {
                "action_icon": {
                    "fencing": "🎮",
                    "fenced": "🎯",
                    "register": "📝",
                    "gluing": "💦",
                    "unsubscribe": "❌",
                    "drug": "💊",
                }.get(record["action"], record["action"]),
                "action": {
                    "fencing": "击剑",
                    "fenced": "被击剑",
                    "gluing": "打胶",
                    "register": "注册牛牛",
                    "unsubscribe": "注销牛牛",
                    "drug": "使用药水",
                }.get(record["action"], record["action"]),
                "time": record["time"],
                "origin": record["origin_length"],
                "new": record["new_length"],
                "diff": f"+{record['diff']}" if record["diff"] > 0 else record["diff"],
                "diff_color": "positive"
                if record["diff"] > 0
                else "negative"
                if record["diff"] < 0
                else "neutral",
            }
            for record in records
        ],
    }

    # 渲染模板
    template_dir = Path(__file__).resolve().parent / "templates"
    pic = await template_to_pic(
        template_path=str(template_dir),
        template_name="record_info.html",
        templates=result,
    )
    await niuniu_my_record.send(Image(raw=pic), reply_to=True)

