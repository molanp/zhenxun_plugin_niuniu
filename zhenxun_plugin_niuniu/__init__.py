from nonebot import on_command
from nonebot.params import CommandArg
from utils.utils import is_number
from utils.message_builder import image
from nonebot.adapters.onebot.v11 import (
    GroupMessageEvent,
    Message)
from .data_source import *
from decimal import Decimal as de
import os
import time
import random

__zx_plugin_name__ = "牛牛大作战"
__plugin_usage__ = """
usage：
    牛子大作战，男同快乐游
    合理安排时间，享受健康生活

    注册牛子 --注册你的牛子
    注销牛子 --销毁你的牛子
    jj [@user] --与注册牛子的人进行击剑，对战结果影响牛子长度
    我的牛子 --查看自己牛子长度
    牛子长度排行 --查看本群正数牛子长度排行
    牛子深度排行 --查看本群负数牛子深度排行
    打胶 --对自己的牛子进行操作，结果随机
""".strip()
__plugin_des__ = "牛子大作战(误"
__plugin_type__ = ("群内小游戏",)
__plugin_cmd__ = ['注册牛子', '击剑', 'jj', 'JJ', 'Jj', 'jJ',
                  '我的牛子', '牛子长度排行', '牛子深度排行', '打胶', '牛牛大作战', "注销牛子"]
__plugin_version__ = 0.6
__plugin_author__ = "molanp"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": __plugin_cmd__,
}

niuzi_register = on_command("注册牛子", priority=5, block=True)
niuzi_delete = on_command("注销牛子", priority=10, block=True)
niuzi_fencing = on_command(
    "jj", aliases={'JJ', 'Jj', 'jJ', '击剑'}, priority=5, block=True)
niuzi_my = on_command("我的牛子", priority=5, block=True)
niuzi_ranking = on_command("牛子长度排行", priority=5, block=True)
niuzi_ranking_e = on_command("牛子深度排行", priority=5, block=True)
niuzi_hit_glue = on_command("打胶", priority=5, block=True)

group_user_jj = {}
group_hit_glue = {}

# 检查文件
data_dir = Path(__file__).resolve().parent / "data"
data_dir.mkdir(parents=True, exist_ok=True)
long_json_file = data_dir / "long.json"
if not long_json_file.exists():
    ReadOrWrite(long_json_file, {})


@niuzi_register.handle()
async def _(event: GroupMessageEvent):
    group = str(event.group_id)
    qq = str(event.user_id)
    content = ReadOrWrite("data/long.json")
    long = random_long()
    try:
        if content[group]:
            pass
    except KeyError:
        content[group] = {}
    try:
        if content[group][qq]:
            await niuzi_register.finish(Message("你已经有过牛子啦！"), at_sender=True)
    except KeyError:
        content[group][qq] = long
        ReadOrWrite("data/long.json", content)
        await niuzi_register.finish(Message(f"牛子长出来啦！足足有{long}cm呢"), at_sender=True)


@niuzi_delete.handle()
async def _(event: GroupMessageEvent):
    group = str(event.group_id)
    qq = str(event.user_id)
    content = ReadOrWrite("data/long.json")
    try:
        del content[group][qq]
        ReadOrWrite("data/long.json", content)
        await niuzi_delete.finish(Message("从今往后你就没有牛子啦！"), at_sender=True)
    except NameError:
        await niuzi_delete.finish(Message("你还没有牛子呢！"), at_sender=True)


@niuzi_fencing.handle()
async def _(event: GroupMessageEvent):
    qq = str(event.user_id)
    group = str(event.group_id)
    global group_user_jj
    try:
        if group_user_jj[group]:
            pass
    except KeyError:
        group_user_jj[group] = {}
    try:
        if group_user_jj[group][qq]:
            pass
    except KeyError:
        group_user_jj[group][qq] = {}
    try:
        time_pass = int(time.time() - group_user_jj[group][qq]["time"])
        if time_pass < 180:
            time_rest = 180 - time_pass
            jj_refuse = [
                f"才过去了{time_pass}s时间,你就又要击剑了，真是饥渴难耐啊",
                f"不行不行，你的身体会受不了的，歇{time_rest}s再来吧",
                f"你这种男同就应该被送去集中营！等待{time_rest}s再来吧",
                f"打咩哟！你的牛牛会炸的，休息{time_rest}s再来吧",
            ]
            await niuzi_fencing.finish(random.choice(jj_refuse), at_sender=True)
    except KeyError:
        pass
    #
    msg = event.get_message()
    content = ReadOrWrite("data/long.json")
    at_list = []
    for msg_seg in msg:
        if msg_seg.type == "at":
            at_list.append(msg_seg.data["qq"])
    try:
        my_long = de(str(content[group][qq]))
        if len(at_list) >= 1:
            at = str(at_list[0])
            if len(at_list) >= 2:
                result = random.choice([
                    "一战多？你的小身板扛得住吗？",
                    "你不准参加Impart┗|｀O′|┛"
                ])
            elif at != qq:
                try:
                    opponent_long = de(str(content[group][at]))
                    group_user_jj[group][qq]["time"] = time.time()
                    result = fencing(my_long, opponent_long,
                                     at, qq, group, content)
                except KeyError:
                    result = "对方还没有牛子呢，你不能和ta击剑！"
            else:
                result = "不能和自己击剑哦！"
        else:
            result = "你要和谁击剑？你自己吗？"
    except KeyError:
        del group_user_jj[group][qq]["time"]
        result = "你还没有牛子呢！不能击剑！"
    finally:
        await niuzi_fencing.finish(Message(result), at_sender=True)


@niuzi_my.handle()
async def _(event: GroupMessageEvent):
    qq = str(event.user_id)
    group = str(event.group_id)
    content = ReadOrWrite("data/long.json")
    try:
        my_long = content[group][qq]
        values = sorted(content[group], reverse=True)
        rank = 1
        previous_value = None
        sex_long = "深" if my_long < 0 else "长"
        sex = "♀️" if my_long < 0 else "♂️"
        for value in values:
            difference = 0 if previous_value is None else previous_value - value
            if value <= my_long:
                result = f"📛{str(event.sender)}<{qq}>的牛子信息\n⭕排名:#{rank}\n⭕性别:{sex}\n⭕{sex_long}度:{value}cm\n⭕与上一名差距:{difference}cm\n⭕备注: "
                break
            else:
                rank += 1
                previous_value = value
        if my_long <= -100:
            result += f"wtf？你已经进化成魅魔了！魅魔在击剑时有20%的几率消耗自身长度吞噬对方牛子呢。",
        elif -100 < my_long <= -50:
            result += f"嗯....好像已经穿过了身体吧..从另一面来看也可以算是凸出来的吧?"
        elif -50 < my_long <= -25:
            result += random.choice([
                f"这名女生，你的身体很健康哦！",
                f"WOW,真的凹进去了好多呢！",
                f"你已经是我们女孩子的一员啦！"
            ])
        elif -25 < my_long <= -10:
            result += random.choice([
                f"你已经是一名女生了呢，",
                f"从女生的角度来说，你发育良好(,",
                f"你醒啦？你已经是一名女孩子啦！",
                f"唔...可以放进去一根手指了都..."
            ])
        elif -10 < my_long <= 0:
            result += random.choice([
                f"安了安了，不要伤心嘛，做女生有什么不好的啊。",
                f"不哭不哭，摸摸头，虽然很难再长出来，但是请不要伤心啦啊！",
                f"加油加油！我看好你哦！",
                f"你醒啦？你现在已经是一名女孩子啦！"
            ])
        elif 0 < my_long <= 10:
            result += random.choice([
                f"你行不行啊？细狗！",
                f"虽然短，但是小小的也很可爱呢。",
                f"像一只蚕宝宝。"
            ])
        elif 10 < my_long <= 25:
            result += random.choice([
                f"唔...没话说",
                f"已经很长了呢！"
            ])
        elif 25 < my_long <= 50:
            result += random.choice([
                f"话说这种真的有可能吗？",
                f"厚礼谢！"
            ])
        elif 50 < my_long <= 100:
            result += random.choice([
                f"已经突破天际了嘛...",
                f"唔...这玩意应该不会变得比我高吧？",
                f"你这个长度会死人的...！",
                f"你马上要进化成牛头人了！！",
                f"你是什么怪物，不要过来啊！！"
            ])
        elif 100 < my_long:
            result += f"惊世骇俗！你已经进化成牛头人了！牛头人在击剑时有20%的几率消耗自身长度吞噬对方牛子呢。"
    except KeyError:
        result = "你还没有牛子呢！"
    finally:
        await niuzi_my.finish(Message(result), at_sender=True)


@niuzi_ranking.handle()
async def _(event: GroupMessageEvent, arg: Message = CommandArg()):
    num = arg.extract_plain_text().strip()
    if is_number(num) and 51 > int(num) > 10:
        num = int(num)
    else:
        num = 10
    all_users = get_all_users(str(event.group_id))
    all_user_id = []
    all_user_data = []
    for user_id, user_data in all_users.items():
        if user_data > 0:
            all_user_id.append(int(user_id))
            all_user_data.append(user_data)

    if len(all_user_id) != 0:
        rank_image = await init_rank("牛子长度排行榜-单位cm", all_user_id, all_user_data, event.group_id, num)
        if rank_image:
            await niuzi_ranking.finish(image(b64=rank_image.pic2bs4()))
    else:
        await niuzi_ranking.finish(Message("暂无此排行榜数据...", at_sender=True))


@niuzi_ranking_e.handle()
async def _(event: GroupMessageEvent, arg: Message = CommandArg()):
    num = arg.extract_plain_text().strip()
    if is_number(num) and 51 > int(num) > 10:
        num = int(num)
    else:
        num = 10
    all_users = get_all_users(str(event.group_id))
    all_user_id = []
    all_user_data = []
    for user_id, user_data in all_users.items():
        if user_data < 0:
            all_user_id.append(int(user_id))
            all_user_data.append(float(str(user_data)[1:]))

    if len(all_user_id) != 0:
        rank_image = await init_rank("牛子深度排行榜-单位cm", all_user_id, all_user_data, event.group_id, num)
        if rank_image:
            await niuzi_ranking_e.finish(image(b64=rank_image.pic2bs4()))
    else:
        await niuzi_ranking_e.finish(Message("暂无此排行榜数据..."), at_sender=True)


@niuzi_hit_glue.handle()
async def _(event: GroupMessageEvent):
    qq = str(event.user_id)
    group = str(event.group_id)
    global group_hit_glue
    try:
        if group_hit_glue[group]:
            pass
    except KeyError:
        group_hit_glue[group] = {}
    try:
        if group_hit_glue[group][qq]:
            pass
    except KeyError:
        group_hit_glue[group][qq] = {}
    try:
        time_pass = int(time.time() - group_hit_glue[group][qq]["time"])
        if time_pass < 180:
            time_rest = 180 - time_pass
            glue_refuse = [
                f"才过去了{time_pass}s时间,你就又要打🦶了，身体受得住吗",
                f"不行不行，你的身体会受不了的，歇{time_rest}s再来吧",
                f"休息一下吧，会炸膛的！{time_rest}s后再来吧",
                f"打咩哟，你的牛牛会爆炸的，休息{time_rest}s再来吧"
            ]
            await niuzi_hit_glue.finish(random.choice(glue_refuse), at_sender=True)
    except KeyError:
        pass
    try:
        content = ReadOrWrite("data/long.json")
        my_long = de(str(content[group][qq]))
        group_hit_glue[group][qq]["time"] = time.time()
        probability = random.randint(1, 100)
        if 0 < probability <= 40:
            reduce = random_long()
            my_long += abs(reduce*de(my_long/10))
            result = random.choice([
                f"你嘿咻嘿咻一下，促进了牛子发育，牛子增加{reduce}cm了呢！",
                f"你打了个舒服痛快的🦶呐，牛子增加了{reduce}cm呢！"
            ])
        elif 40 < probability <= 60:
            result = random.choice([
                "你打了个🦶，但是什么变化也没有，好奇怪捏~",
                "你的牛子刚开始变长了，可过了一会又回来了，什么变化也没有，好奇怪捏~"
            ])
        else:
            reduce = random_long()
            my_long -= abs(reduce*de(my_long/10))
            if my_long < 0:
                result = random.choice([
                    f"哦吼！？看来你的牛子凹进去了{reduce}cm呢！",
                    f"你突发恶疾！你的牛子凹进去了{reduce}cm！",
                    f"笑死，你因为打🦶过度导致牛子凹进去了{reduce}cm！🤣🤣🤣"
                ])
            else:
                result = random.choice([
                    f"阿哦，你过度打🦶，牛子缩短{reduce}cm了呢！",
                    f"你的牛子变长了很多，你很激动地继续打🦶，然后牛子缩短了{reduce}cm呢！",
                    f"小打怡情，大打伤身，强打灰飞烟灭！你过度打🦶，牛子缩短了{reduce}cm捏！"
                ])
        content[group][qq] = my_long
        ReadOrWrite("data/long.json", content)
    except KeyError:
        del group_hit_glue[group][qq]["time"]
        result = random.choice([
            "你还没有牛子呢！不能打胶！",
            "无牛子，打胶不要的"
        ])
    finally:
        await niuzi_hit_glue.finish(Message(result), at_sender=True)
