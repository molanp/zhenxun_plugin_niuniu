import contextlib
from pathlib import Path
import random
import time

import aiofiles
from arclet.alconna import Args
from nonebot import get_driver
from nonebot_plugin_alconna import Alconna, Image, Match, Text, on_alconna
from nonebot_plugin_htmlrender import template_to_pic
from nonebot_plugin_uninfo import Uninfo

from zhenxun.models.user_console import UserConsole
from zhenxun.utils.enum import GoldHandle
from zhenxun.utils.message import MessageUtils

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
niuniu_fencing = on_alconna(
    Alconna("击剑", Args["@user"]),
    aliases={"JJ", "Jj", "jJ"},
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

niuniu_test_gold = on_alconna(
    Alconna(".n"),
    priority=5,
    block=True,
)


@niuniu_test_gold.handle()
async def _(session: Uninfo):
    uid = str(session.user.id)
    await UserConsole.add_gold(uid, 50, GoldHandle.PLUGIN, "niuniu")


group_user_jj = {}
user_hit_glue_time_map = {}

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
# async def _(event: GroupMessageEvent):
#     qq = str(event.user_id)
#     group = str(event.group_id)
#     global group_user_jj
#     try:
#         if group_user_jj[group]:
#             pass
#     except KeyError:
#         group_user_jj[group] = {}
#     try:
#         if group_user_jj[group][qq]:
#             pass
#     except KeyError:
#         group_user_jj[group][qq] = {}
#     try:
#         time_pass = int(time.time() - group_user_jj[group][qq]["time"])
#         if time_pass < 180:
#             time_rest = 180 - time_pass
#             jj_refuse = [
#                 f"才过去了{time_pass}s时间,你就又要击剑了，真是饥渴难耐啊",
#                 f"不行不行，你的身体会受不了的，歇{time_rest}s再来吧",
#                 f"你这种男同就应该被送去集中营！等待{time_rest}s再来吧",
#                 f"打咩哟！你的牛牛会炸的，休息{time_rest}s再来吧",
#             ]
#             await niuniu_fencing.finish(random.choice(jj_refuse), at_sender=True)
#     except KeyError:
#         pass
#     #
#     msg = event.get_message()
#     content = ReadOrWrite("data/long.json")
#     at_list = []
#     for msg_seg in msg:
#         if msg_seg.type == "at":
#             at_list.append(msg_seg.data["qq"])
#     try:
#         my_long = de(str(content[group][qq]))
#         if len(at_list) >= 1:
#             at = str(at_list[0])
#             if len(at_list) >= 2:
#                 result = random.choice(
#                     ["一战多？你的小身板扛得住吗？", "你不准参加Impart┗|｀O′|┛"]
#                 )
#             elif at != qq:
#                 try:
#                     opponent_long = de(str(content[group][at]))
#                     group_user_jj[group][qq]["time"] = time.time()
#                     result = fencing(my_long, opponent_long, at, qq, group, content)
#                 except KeyError:
#                     result = "对方还没有牛牛呢，你不能和ta击剑！"
#             else:
#                 result = "不能和自己击剑哦！"
#         else:
#             result = "你要和谁击剑？你自己吗？"
#     except KeyError:
#         try:
#             del group_user_jj[group][qq]["time"]
#         except KeyError:
#             pass
#         result = "你还没有牛牛呢！不能击剑！"
#     finally:
#         await niuniu_fencing.finish(Message(result), at_sender=True)


@niuniu_my.handle()
async def _(session: Uninfo):
    uid = session.user.id
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
            "name": session.user.name,
            "rank": rank,
            "my_length": user["length"],
            "difference": round(next_length - user["length"], 2),
            "latest_gluing_time": await NiuNiu.latest_gluing_time(uid),
            "comment": await NiuNiu.comment(user["length"]),
        }
    else:
        result = {
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
    image = await NiuNiu.rank(session, match.result, gid)
    await MessageUtils.build_message(image).send()


# @niuniu_deep_rank.handle()
# async def _(event: GroupMessageEvent, arg: Message = CommandArg()):
#     num = arg.extract_plain_text().strip()
#     if str(num).isdigit() and 51 > int(num) > 10:
#         num = int(num)
#     else:
#         num = 10
#     all_users = get_all_users(str(event.group_id))
#     all_user_id = []
#     all_user_data = []
#     for user_id, user_data in all_users.items():
#         if user_data < 0:
#             all_user_id.append(int(user_id))
#             all_user_data.append(float(str(user_data)[1:]))

#     if len(all_user_id) != 0:
#         rank_image = await init_rank(
#             "牛牛深度排行榜-单位cm", all_user_id, all_user_data, event.group_id, num
#         )
#         if rank_image:
#             await niuniu_deep_rank.finish(image(b64=rank_image.pic2bs4()))
#     else:
#         await niuniu_deep_rank.finish(Message("暂无此排行榜数据..."), at_sender=True)


@niuniu_hit_glue.handle()
async def _(session: Uninfo):
    global user_hit_glue_time_map
    uid = str(session.user.id)
    origin_length = await Sqlite.query("users", ["length"], {"uid": uid})
    if not origin_length:
        await niuniu_hit_glue.send(
            Text(random.choice(["你还没有牛牛呢！不能打胶！", "无牛牛，打胶不要的"])),
            reply_to=True,
        )
        return
    new_length = origin_length = origin_length[0]["length"]
    with contextlib.suppress(KeyError):
        time_pass = int(time.time() - user_hit_glue_time_map[uid])
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
    user_hit_glue_time_map[uid] = time.time()
    prob = random.choice([1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, -1, -1, -1])
    reduce_ = None
    if prob == 1:
        new_length, reduce_ = await NiuNiu.gluing(origin_length)
        result = random.choice(
            [
                f"你嘿咻嘿咻一下，促进了牛牛发育，牛牛增加了{reduce_}cm了呢！🎉",
                f"你打了个舒服痛快的🦶呐，牛牛增加了{reduce_}cm呢！💪",
                f"哇哦！你的一🦶让牛牛变长了{reduce_}cm！👏",
                f"你的牛牛感受到了你的热情，增长了{reduce_}cm！🔥",
                f"你的一脚仿佛有魔力，牛牛增长了{reduce_}cm！✨",
            ]
        )
    elif prob == 0:
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
        new_length, reduce_ = await NiuNiu.gluing(origin_length)
        reduce = abs(reduce_)
        if new_length < 0:
            result = random.choice(
                [
                    f"哦吼！？看来你的牛牛凹进去了{reduce}cm呢！😱",
                    f"你突发恶疾！你的牛牛凹进去了{reduce}cm！😨",
                    f"笑死，你因为打🦶过度导致牛牛凹进去了{reduce}cm！🤣🤣🤣",
                    f"你的牛牛仿佛被你一🦶踢进了地缝，凹进去了{reduce}cm！🕳️",
                    f"你的一🦶太重了，牛牛凹进去了{reduce}cm！💥",
                ]
            )
        else:
            result = random.choice(
                [
                    f"阿哦，你过度打🦶，牛牛缩短了{reduce}cm了呢！😢",
                    f"你的牛牛变长了很多，你很激动地继续打🦶，然后牛牛缩短了{reduce}cm呢！🤦‍♂️",
                    f"小打怡情，大打伤身，强打灰飞烟灭！你过度打🦶，牛牛缩短了{reduce}cm捏！💥",
                    f"你的牛牛看起来很受伤，缩短了{reduce}cm！🤕",
                    f"你的打🦶没效果，于是很气急败坏地继续打🦶，然后牛牛缩短了{reduce}cm呢！🤦‍♂️",
                ]
            )

    await Sqlite.update("users", {"length": new_length}, {"uid": uid})
    await Sqlite.insert(
        "records",
        {
            "uid": uid,
            "origin_length": origin_length,
            "diff": reduce_,
            "new_length": new_length,
            "action": "gluing",
        },
    )

    await niuniu_hit_glue.send(Text(result), reply_to=True)
