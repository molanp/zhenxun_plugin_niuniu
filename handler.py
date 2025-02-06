import base64
import contextlib
from pathlib import Path
import random
import time
from typing import Any

import aiofiles
from arclet.alconna import AllParam, Args, CommandMeta
from nonebot import get_driver
from nonebot_plugin_alconna import (
    Alconna,
    At,
    Image,
    Match,
    Text,
    UniMessage,
    on_alconna,
)
from nonebot_plugin_htmlrender import template_to_pic
from nonebot_plugin_uninfo import Uninfo

from zhenxun.models.user_console import UserConsole
from zhenxun.utils.enum import GoldHandle
from zhenxun.utils.message import MessageUtils
from zhenxun.utils.platform import PlatformUtils

from .data_source import NiuNiu
from .database import Sqlite

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
# niuniu_fencing = on_alconna(
#     Alconna("击剑", Args["at?", AllParam], meta=CommandMeta(compact=True)),
#     aliases=("JJ", "Jj", "jJ", "jj"),
#     priority=5,
#     block=True,
# )
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


user_fence_time_map = {}
user_gluing_time_map = {}

driver = get_driver()


@driver.on_startup
async def handle_connect():
    await Sqlite.init()
    old_data_path = Path(__file__).resolve().parent / "data" / "long.json"
    if old_data_path.exists():
        async with aiofiles.open(old_data_path, encoding="utf-8") as f:
            file_data = f.read()
        await Sqlite.json2db(file_data)
        old_data_path.unlink()
    return


@niuniu_register.handle()
async def _(session: Uninfo):
    uid = str(session.user.id)
    length = await NiuNiu.random_length()
    if await Sqlite.insert(
        "users", {"uid": uid, "length": length, "sex": "boy"}, {"uid": uid}
    ):
        await Sqlite.insert(
            "records",
            {
                "uid": uid,
                "origin_length": 0,
                "diff": length,
                "new_length": length,
                "action": "register",
            },
        )
        await niuniu_register.send(
            Text(f"牛牛长出来啦！足足有{length}cm呢"), reply_to=True
        )
    else:
        await niuniu_register.send(Text("你已经有过牛牛啦！"), reply_to=True)


@niuniu_unsubscribe.handle()
async def _(session: Uninfo):
    uid = str(session.user.id)
    length = await Sqlite.query("users", ["length"], {"uid": uid})
    if not length:
        await niuniu_unsubscribe.send(Text("你还没有牛牛呢！"), reply_to=True)
        return
    gold = (await UserConsole.get_user(uid)).gold
    if gold < 50:
        await niuniu_unsubscribe.send(
            Text("你的金币不足，无法注销牛牛！"), reply_to=True
        )
    else:
        await UserConsole.reduce_gold(uid, 50, GoldHandle.PLUGIN, "niuniu")
        await Sqlite.delete("users", {"uid": uid})
        await Sqlite.insert(
            "records",
            {
                "uid": uid,
                "origin_length": round(length[0]["length"]),
                "diff": -round(length[0]["length"]),
                "new_length": 0,
                "action": "unsubscribe",
            },
        )
        await niuniu_unsubscribe.finish(Text("从今往后你就没有牛牛啦！"), reply_to=True)


# @niuniu_fencing.handle()
# async def _(session: Uninfo, match: Match[Any]):
#     global user_fence_time_map
#     uid = session.user.id
#     with contextlib.suppress(KeyError):
#         time_pass = int(time.time() - user_fence_time_map[uid])
#         if time_pass < 180:
#             time_rest = 180 - time_pass
#             jj_refuse = [
#                 f"才过去了{time_pass}s时间,你就又要击剑了，真是饥渴难耐啊",
#                 f"不行不行，你的身体会受不了的，歇{time_rest}s再来吧",
#                 f"你这种男同就应该被送去集中营！等待{time_rest}s再来吧",
#                 f"打咩哟！你的牛牛会炸的，休息{time_rest}s再来吧",
#             ]
#             await niuniu_fencing.send(random.choice(jj_refuse), reply_to=True)
#             return
#     if not match.available:
#         await niuniu_fencing.send("你要和谁击剑？你自己吗？", reply_to=True)
#     else:
#         messages = UniMessage(match.result)
#         at_list = [
#             message.data["qq"]
#             for message in messages
#             if isinstance(message, At)
#         ]
#         await niuniu_fencing.send(Text(str(at_list)))

#     return
        #
        # msg = event.get_message()
        # content = ReadOrWrite("data/long.json")
        # at_list = []
        # for msg_seg in msg:
        #     if msg_seg.type == "at":
        #         at_list.append(msg_seg.data["qq"])
        # try:
        #     my_long = de(str(content[group][qq]))
        #     if len(at_list) >= 1:
        #         at = str(at_list[0])
        #         if len(at_list) >= 2:
        #             result = random.choice(
        #                 ["一战多？你的小身板扛得住吗？", "你不准参加Impart┗|｀O′|┛"]
        #             )
        #         elif at != qq:
        #             try:
        #                 opponent_long = de(str(content[group][at]))
        #                 group_user_jj[group][qq]["time"] = time.time()
        #                 result = fencing(my_long, opponent_long, at, qq, group, content)
        #             except KeyError:
        #                 result = "对方还没有牛牛呢，你不能和ta击剑！"
        #         else:
        #             result = "不能和自己击剑哦！"
        # except KeyError:
        #     pass
        #     result = "你还没有牛牛呢！不能击剑！"
        # finally:
        #     await niuniu_fencing.finish(Message(result), at_sender=True)


@niuniu_my.handle()
async def _(session: Uninfo):
    uid = int(session.user.id)
    if not await Sqlite.query("users", ["length"], {"uid": uid}):
        await niuniu_my.send(Text("你还没有牛牛呢！"), reply_to=True)
        return

    sql = """
    WITH RankedUsers AS (
        SELECT
            uid,
            length,
            (SELECT COUNT(*)
             FROM users u2
             WHERE u2.length > u1.length) + 1 AS rank
        FROM
            users u1
    )
    SELECT
        ru.uid,
        ru.length,
        ru.rank,
        (SELECT u3.uid FROM RankedUsers u3 WHERE u3.rank = ru.rank - 1) AS next_uid,
        (
            SELECT u3.length FROM RankedUsers u3 WHERE u3.rank = ru.rank - 1
        ) AS next_length,
        (SELECT u3.rank FROM RankedUsers u3 WHERE u3.rank = ru.rank - 1) AS next_rank
    FROM
        RankedUsers ru
    WHERE
        ru.uid = ?
    """

    results = await Sqlite.exec(sql, uid)
    if not results:
        await niuniu_my.send(Text("未查询到数据..."), reply_to=True)
        return
    user = results[0]
    if user.get("next_uid"):
        rank = user["rank"]
        next_uid = user["next_uid"]  # noqa: F841
        next_length = user["next_length"]
        next_rank = user["next_rank"]  # noqa: F841
        result = {
            "avatar": f"data:image/png;base64,{base64.b64encode(await PlatformUtils.get_user_avatar(uid, 'qq', session.self_id)).decode('utf-8')}",
            "name": session.user.name,
            "rank": rank,
            "my_length": user["length"],
            "difference": round(next_length - user["length"], 2),
            "latest_gluing_time": await NiuNiu.latest_gluing_time(uid),
            "comment": await NiuNiu.comment(user["length"]),
        }
    else:
        result = {
            "avatar": f"data:image/png;base64,{base64.b64encode(await PlatformUtils.get_user_avatar(uid, 'qq', session.self_id)).decode('utf-8')}",
            "name": session.user.name,
            "rank": user["rank"],
            "my_length": user["length"],
            "difference": 0,
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
async def _(bot, session: Uninfo, match: Match[int]):
    if not match.available:
        match.result = 10
    if match.result > 50:
        await MessageUtils.build_message("排行榜人数不能超过50哦...").finish()
    gid = session.group.id if session.group else None
    if not gid:
        await MessageUtils.build_message(
            "私聊中无法查看 '牛牛长度排行'，请发送 '牛牛长度总排行'"
        ).finish()
    image = await NiuNiu.rank(bot, match.result, session)
    await MessageUtils.build_message(image).send()


@niuniu_length_rank_all.handle()
async def _(bot, session: Uninfo, match: Match[int]):
    if not match.available:
        match.result = 10
    if match.result > 50:
        await MessageUtils.build_message("排行榜人数不能超过50哦...").finish()
    image = await NiuNiu.rank(bot, match.result, session, is_all=True)
    await MessageUtils.build_message(image).send()


@niuniu_deep_rank.handle()
async def _(bot, session: Uninfo, match: Match[int]):
    if not match.available:
        match.result = 10
    if match.result > 50:
        await MessageUtils.build_message("排行榜人数不能超过50哦...").finish()
    gid = session.group.id if session.group else None
    if not gid:
        await MessageUtils.build_message(
            "私聊中无法查看 '牛牛深度排行'，请发送 '牛牛深度总排行'"
        ).finish()
    image = await NiuNiu.rank(bot, match.result, session, True)
    await MessageUtils.build_message(image).send()


@niuniu_deep_rank_all.handle()
async def _(bot, session: Uninfo, match: Match[int]):
    if not match.available:
        match.result = 10
    if match.result > 50:
        await MessageUtils.build_message("排行榜人数不能超过50哦...").finish()
    image = await NiuNiu.rank(bot, match.result, session, is_all=True)
    await MessageUtils.build_message(image).send()


@niuniu_hit_glue.handle()
async def _(session: Uninfo):
    global user_gluing_time_map
    uid = session.user.id
    origin_length = await Sqlite.query("users", ["length"], {"uid": uid})
    if not origin_length:
        await niuniu_hit_glue.send(
            Text(random.choice(["你还没有牛牛呢！不能打胶！", "无牛牛，打胶不要的"])),
            reply_to=True,
        )
        return
    new_length = origin_length = origin_length[0]["length"]
    with contextlib.suppress(KeyError):
        time_pass = int(time.time() - user_gluing_time_map[uid])
        if time_pass < 180:
            time_rest = 180 - time_pass
            glue_refuse = [
                f"才过去了{time_pass}s时间,你就又要打🦶了，身体受得住吗",
                f"不行不行，你的身体会受不了的，歇{time_rest}s再来吧",
                f"休息一下吧，会炸膛的！{time_rest}s后再来吧",
                f"打咩哟，你的牛牛会爆炸的，休息{time_rest}s再来吧",
            ]
            await niuniu_hit_glue.send(random.choice(glue_refuse), reply_to=True)
            return
    user_gluing_time_map[uid] = time.time()
    prob = random.choice([1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0])
    diff = 0
    if prob == 1:
        new_length, diff = await NiuNiu.gluing(origin_length)
    if diff > 0:
        result = random.choice(
            [
                f"你嘿咻嘿咻一下，促进了牛牛发育，牛牛增加了{diff}cm了呢！🎉",
                f"你打了个舒服痛快的🦶呐，牛牛增加了{diff}cm呢！💪",
                f"哇哦！你的一🦶让牛牛变长了{diff}cm！👏",
                f"你的牛牛感受到了你的热情，增长了{diff}cm！🔥",
                f"你的一脚仿佛有魔力，牛牛增长了{diff}cm！✨",
            ]
        )
    elif diff == 0:
        result = random.choice(
            [
                "你打了个🦶，但是什么变化也没有，好奇怪捏~🤷‍♂️",
                "你的牛牛刚开始变长了，可过了一会又回来了，什么变化也没有，好奇怪捏~🤷‍♀️",
                "你的一🦶仿佛被牛牛躲开了，没有任何变化！😄",
                "你的牛牛看起来很开心，但没有变化！😊",
                "你的一🦶仿佛被牛牛用尾巴挡住了，没有任何变化！💃",
            ]
        )
    else:
        diff_ = abs(diff)
        if new_length < 0:
            result = random.choice(
                [
                    f"哦吼！？看来你的牛牛凹进去了{diff_}cm呢！😱",
                    f"你突发恶疾！你的牛牛凹进去了{diff_}cm！😨",
                    f"笑死，你因为打🦶过度导致牛牛凹进去了{diff_}cm！🤣🤣🤣",
                    f"你的牛牛仿佛被你一🦶踢进了地缝，凹进去了{diff_}cm！🕳️",
                    f"你的一🦶用力过度了，牛牛凹进去了{diff_}cm！💥",
                ]
            )
        else:
            result = random.choice(
                [
                    f"阿哦，你过度打🦶，牛牛缩短了{diff_}cm了呢！😢",
                    f"你的牛牛变长了很多，你很激动地继续打🦶，然后牛牛缩短了{diff_}cm呢！🤦‍♂️",
                    f"小打怡情，大打伤身，强打灰飞烟灭！你过度打🦶，牛牛缩短了{diff_}cm捏！💥",
                    f"你的牛牛看起来很受伤，缩短了{diff_}cm！🤕",
                    f"你的打🦶没效果，于是很气急败坏地继续打🦶，然后牛牛缩短了{diff_}cm呢！🤦‍♂️",
                ]
            )

    await Sqlite.update(
        "users",
        {"length": new_length, "sex": "boy" if new_length > 0 else "girl"},
        {"uid": uid},
    )
    await Sqlite.insert(
        "records",
        {
            "uid": uid,
            "origin_length": origin_length,
            "diff": diff,
            "new_length": new_length,
            "action": "gluing",
        },
    )

    await niuniu_hit_glue.send(Text(result), reply_to=True)
