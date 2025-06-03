import random

from nonebot import get_bot, require
require("nonebot_plugin_uninfo")
from nonebot_plugin_uninfo import Uninfo
from tortoise.functions import Max, Min

from zhenxun.services.log import logger
from zhenxun.utils.image_utils import BuildImage, ImageTemplate
from zhenxun.utils.platform import PlatformUtils

from .model import NiuNiuRecord, NiuNiuUser


class NiuNiuQuick:
    @classmethod
    async def get_length(cls, uid: int | str) -> float | None:
        user = await NiuNiuUser.get_or_none(uid=uid).values("length")
        return user["length"] if user else None

    @classmethod
    async def random_length(cls) -> float:
        users = await NiuNiuUser.all().order_by("length").values("length")

        if not users:
            origin_length = 10.0
        else:
            length_values = [u["length"] for u in users]
            index = min(int(len(length_values) * 0.3), len(length_values) - 1)
            origin_length = float(length_values[index])

        return round(origin_length * 0.9, 2)

    @classmethod
    async def latest_gluing_time(cls, uid: int) -> str:
        record = (
            await NiuNiuRecord.filter(uid=uid, action="gluing")
            .order_by("-time")
            .first()
            .values("time")
        )

        return record["time"] if record else "暂无记录"

    @classmethod
    async def get_nearest_lengths(cls, target_length: float) -> list[float]:
        # 使用ORM聚合查询
        greater_length = (
            await NiuNiuUser.filter(length__gt=target_length)
            .annotate(min_length=Min("length"))
            .values("min_length")
        )

        less_length = (
            await NiuNiuUser.filter(length__lt=target_length)
            .annotate(max_length=Max("length"))
            .values("max_length")
        )

        return [
            greater_length[0]["min_length"] if greater_length else 0,
            less_length[0]["max_length"] if less_length else 0,
        ]

    @classmethod
    async def gluing(cls, origin_length: float) -> tuple[float, float]:
        result = await cls.get_nearest_lengths(origin_length)
        if result[0] != 0 or result[1] != 0:
            new_length = origin_length + result[0] * 0.3 - result[1] * 0.6
            return round(new_length, 2), round(new_length - origin_length, 2)

        if origin_length <= 0:
            prob = random.choice([-1.1, -1, -1, -1, -1, 1, 1, 1, 1])
            diff = prob * 0.1 * origin_length + 1
        else:
            prob = random.choice([1, 1, 1, 1, 1, 0.9, -1, -1, -1, -1, -1, -1.4])
            diff = prob * 0.1 * origin_length - 1
        new_length = origin_length + diff
        return round(new_length, 2), round(new_length - origin_length, 2)

    @classmethod
    async def comment(cls, length: float) -> str:
        if length <= -100:
            return (
                "哇哦!你已经进化成魅魔了!"
                "魅魔在击剑时有20%的几率消耗自身长度吞噬对方牛牛呢!"
            )
        elif -100 < length <= -50:
            return "嗯……好像已经穿过了身体吧……从另一面来看也可以算是凸出来的吧？"
        elif -50 < length <= -25:
            return random.choice(
                [
                    "这名女生,你的身体很健康哦!",
                    "WOW,真的凹进去了好多呢!",
                    "你已经是我们女孩子的一员啦!",
                ]
            )
        elif -25 < length <= -10:
            return random.choice(
                [
                    "你已经是一名女生了呢!",
                    "从女生的角度来说,你发育良好哦!",
                    "你醒啦?你已经是一名女孩子啦!",
                    "唔……可以放进去一根手指了都……",
                ]
            )
        elif -10 < length <= 0:
            return random.choice(
                [
                    "安了安了,不要伤心嘛,做女生有什么不好的啊.",
                    "不哭不哭,摸摸头,虽然很难再长出来,但是请不要伤心啦啊!",
                    "加油加油!我看好你哦!",
                    "你醒啦？你现在已经是一名女孩子啦!",
                    "成为香香软软的女孩子吧!",
                ]
            )
        elif 0 < length <= 10:
            return random.choice(
                [
                    "你行不行啊?细狗!",
                    "虽然短,但是小小的也很可爱呢.",
                    "像一只蚕宝宝.",
                    "长大了.",
                ]
            )
        elif 10 < length <= 25:
            return random.choice(
                [
                    "唔……没话说",
                    "已经很长了呢!",
                ]
            )
        elif 25 < length <= 50:
            return random.choice(
                [
                    "话说这种真的有可能吗？",
                    "厚礼谢!",
                ]
            )
        elif 50 < length <= 100:
            return random.choice(
                [
                    "已经突破天际了嘛……",
                    "唔……这玩意应该不会变得比我高吧？",
                    "你这个长度会死人的……!",
                    "你马上要进化成牛头人了!!",
                    "你是什么怪物,不要过来啊!!",
                ]
            )
        else:
            return (
                "惊世骇俗!你已经进化成牛头人了!"
                "牛头人在击剑时有20%的几率消耗自身长度吞噬对方牛牛呢!"
            )

    @classmethod
    async def rank(
        cls, num: int, session: Uninfo, deep: bool = False, is_all: bool = False
    ) -> BuildImage | str:
        data_list = []
        order = "length" if deep else "-length"

        # 构建基础查询
        query = NiuNiuUser.all().order_by(order)
        uid2name = {}
        bot = get_bot(self_id=session.self_id)
        if not is_all and session.group:
            try:
                group_members = await bot.get_group_member_list(
                    group_id=session.group.id
                )
                user_ids = [
                    int(member["user_id"]) for member in group_members
                ]  # 修复4: 统一为int类型
                query = query.filter(uid__in=user_ids)
                uid2name = {
                    int(member["user_id"]): member["nickname"]
                    for member in group_members
                }
            except Exception as e:
                logger.error("获取群成员失败", "niuniu", e=e)
                return f"获取群成员失败: {e!s}"

        # 执行查询并转换数据
        users = await query.limit(num).values("uid", "length")
        if not users:
            return "当前还没有人有牛牛哦..."

        # 修复5: 直接使用ORM查询结果
        user_id_list = [user["uid"] for user in users]
        index = (
            user_id_list.index(int(session.user.id)) + 1
            if int(session.user.id) in user_id_list
            else "-1（未统计）"
        )

        # 构建表格数据
        for i, user in enumerate(users):
            uid = user["uid"]
            length = user["length"]

            # 获取用户头像
            avatar_bytes = await PlatformUtils.get_user_avatar(
                str(uid), "qq", session.self_id
            )

            # 获取用户昵称
            nickname = (
                uid2name.get(uid)
                or (await bot.get_stranger_info(user_id=uid))["nickname"]
            )

            data_list.append([f"{i + 1}", (avatar_bytes, 30, 30), nickname, length])

        # 生成标题
        title_type = "深度" if deep else "长度"
        scope = "群组内" if session.group else "全局"
        title = f"{title_type}{scope}排行"
        tip = f"你的排名在{scope}第 {index} 位哦!"

        return await ImageTemplate.table_page(
            head_text=title,
            tip_text=tip,
            column_name=["排名", "头像", "名称", "长度"],
            data_list=data_list,
        )
