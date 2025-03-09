import base64
import contextlib
from pathlib import Path
import random
import time

import aiofiles
from arclet.alconna import Args
from nonebot import get_driver, on_command
from nonebot_plugin_alconna import (
    Alconna,
    At,
    Image,
    Match,
    Text,
    UniMsg,
    on_alconna,
)
from nonebot_plugin_htmlrender import template_to_pic
from nonebot_plugin_uninfo import Uninfo
from tortoise.exceptions import DoesNotExist

from zhenxun.configs.path_config import DATA_PATH
from zhenxun.models.user_console import UserConsole
from zhenxun.utils.enum import GoldHandle
from zhenxun.utils.message import MessageUtils
from zhenxun.utils.platform import PlatformUtils

from .config import (
    FENCE_COOLDOWN,
    FENCED_PROTECTION,
    GLUE_COOLDOWN,
    PLOCE_BAN,
    QUICK_GLUE_COOLDOWN,
    UNSUBSCRIBE_GOLD,
)
from .database import Sqlite
from .fence import Fencing
from .model import NiuNiuUser
from .niuniu import NiuNiu

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


user_fence_time_map = {}
user_fenced_time_map = {} 
user_gluing_time_map = {}

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
    if not length:
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
    global user_fence_time_map
    at_list = [i.target for i in msg if isinstance(i, At)]
    uid = session.user.id
    with contextlib.suppress(KeyError):
        time_pass = int(time.time() - user_fence_time_map[uid])
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
        if not my_long:
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
        if not opponent_long:
            raise RuntimeError("对方还没有牛牛呢！不能击剑！")
        # 新增被击剑者冷却检查
        if user_fenced_time_map.get(at) is None:
            fenced_time = await NiuNiu.last_fenced_time(at)
        else:
            fenced_time = user_fenced_time_map[at]
        fenced_time_pass = int(time.time() - fenced_time)
        if fenced_time_pass < FENCED_PROTECTION:  # 5分钟保护期
            tips = [
                f"对方刚被击剑过，需要休息{FENCED_PROTECTION - fenced_time_pass}秒才能再次被击剑",  # noqa: E501
                f"对方牛牛还在恢复中，{FENCED_PROTECTION - fenced_time_pass}秒后再来吧",
                f"禁止连续击剑同一用户！请等待{FENCED_PROTECTION - fenced_time_pass}秒",
            ]
            await niuniu_fencing.send(random.choice(tips), reply_message=True)
            return
        result = await Fencing.fencing(my_long, opponent_long, at, uid)
        user_fence_time_map[uid] = time.time()
        user_fenced_time_map[at] = time.time()  # 新增被击剑者冷却
        await niuniu_fencing.send(result, reply_message=True)
    except RuntimeError as e:
        await niuniu_fencing.send(str(e), reply_message=True)


@niuniu_my.handle()
async def _(session: Uninfo):
    uid = int(session.user.id)
    if not await NiuNiu.get_length(uid):
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

    # 获取前一名用户
    next_user = (
        await NiuNiuUser.filter(length__lt=current_user.length)
        .order_by("length")
        .first()
    )

    # 构造结果数据
    user = {
        "uid": current_user.uid,
        "length": current_user.length,
        "rank": rank,
        "next_uid": next_user.uid if next_user else None,
        "next_length": next_user.length if next_user else None,
        "next_rank": rank - 1 if next_user else None,
    }
    avatar = await PlatformUtils.get_user_avatar(str(uid), "qq", session.self_id)
    avatar = "" if avatar is None else base64.b64encode(avatar).decode("utf-8")
    if user.get("next_uid"):
        rank = user["rank"]
        next_uid = user["next_uid"]  # noqa: F841
        next_length = user["next_length"]
        next_rank = user["next_rank"]  # noqa: F841
        result = {
            "avatar": f"data:image/png;base64,{avatar}",
            "name": session.user.name,
            "rank": rank,
            "my_length": user["length"],
            "difference": round(next_length - user["length"], 2),
            "latest_gluing_time": await NiuNiu.latest_gluing_time(uid),
            "comment": await NiuNiu.comment(user["length"]),
        }
    else:
        result = {
            "avatar": f"data:image/png;base64,{avatar}",
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
    global user_gluing_time_map
    uid = session.user.id
    origin_length = await NiuNiu.get_length(uid)
    if not origin_length:
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
    new_length = origin_length
    is_rapid_glue = False
    with contextlib.suppress(KeyError):
        time_pass = abs(int(time.time() - user_gluing_time_map[uid]))
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
    user_gluing_time_map[uid] = time.time()
    if is_rapid_glue:
        prob_pool = [1, 1, 0, 0, 0, 0, -1, -1, -1, -1, 3, 2, 2, 2]
    else:
        prob_pool = [1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, -1, -1, 3, 2, 2, 4]

    prob = random.choice(prob_pool)
    diff = 0
    if is_rapid_glue and prob == 1:
        new_length, diff = await NiuNiu.gluing(origin_length, 0.1)
        result = random.choice(
            [
                f"这么着急？牛牛只微微增长了{diff}cm...🤏",
                f"bro你搞这么快只会适得其反！牛牛只增加{diff}cm！😰",
                f"牛牛还没冷却好！勉强增长{diff}cm！😖",
            ]
        )
        await NiuNiu.update_length(uid, new_length)
        await NiuNiu.record_length(uid, origin_length, new_length, "gluing")
        await niuniu_hit_glue.send(Text(result), reply_to=True)
        return
    if prob == 1:
        new_length, diff = await NiuNiu.gluing(origin_length)
    elif prob == 3 and origin_length > 0:
        new_length = round(origin_length - (origin_length / 2), 2)
        result = random.choice(
            [
                f"由于你在换蛋期打胶，你的牛牛断掉了呢！当前长度{new_length}cm!🤯",
                f"bro换蛋期就不要打胶了！你的牛牛萎缩了{abs(diff)}cm！💩",
            ]
        )
        await NiuNiu.update_length(uid, new_length)
        await NiuNiu.record_length(uid, origin_length, new_length, "gluing")
        await niuniu_hit_glue.send(Text(result), reply_to=True)
        return
    elif prob == 2:
        result = f"打胶时被窗外的路人发现了，对方报警了，你被抓走了！关进小黑屋里{PLOCE_BAN}s!"  # noqa: E501
        user_gluing_time_map[uid] = time.time() + PLOCE_BAN
        await niuniu_hit_glue.send(Text(result), reply_to=True)
        return
    elif prob == 4:
        new_length, diff = await NiuNiu.gluing(origin_length, 1.2)
        result = f"你收到了群主私发的女装，冲！！！牛牛长大了{diff}cm！👗"
        await NiuNiu.update_length(uid, new_length)
        await NiuNiu.record_length(uid, origin_length, new_length, "gluing")
        await niuniu_hit_glue.send(Text(result), reply_to=True)
        return
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
                "你准备🦌的时候发现今天是疯狂星期四，先V我50!😄",
                "你的牛牛看起来很开心，但没有变化！😊",
                "你在打胶时，感觉这个世界似乎发生了什么变化🤔",
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
                    f"🦌的时候突然响起了届かない恋！你听了之后想起了自己的往事, 伤心之余发觉牛牛缩短了{diff_}cm。"  # noqa: E501
                    f"你的牛牛变长了很多，你很激动地继续打🦶，然后牛牛缩短了{diff_}cm呢！🤦‍♂️",
                    f"小打怡情，大打伤身，强打灰飞烟灭！你过度打🦶，牛牛缩短了{diff_}cm捏！💥",
                    f"你的牛牛看起来很受伤，缩短了{diff_}cm！🤕",
                    f"你的打🦶没效果，于是很气急败坏地继续打🦶，然后牛牛缩短了{diff_}cm呢！🤦‍♂️",
                    f"🦌太多次导致身体虚弱，牛牛长度减少了{diff_}cm!",
                ]
            )

    await NiuNiu.update_length(uid, new_length)
    await NiuNiu.record_length(uid, origin_length, new_length, "gluing")

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
                }.get(record["action"], record["action"]),
                "action": {
                    "fencing": "击剑",
                    "fenced": "被击剑",
                    "gluing": "打胶",
                    "register": "注册牛牛",
                    "unsubscribe": "注销牛牛",
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
