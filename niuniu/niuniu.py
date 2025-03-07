from datetime import datetime
import random

from nonebot import get_bot
from nonebot_plugin_uninfo import Uninfo

from zhenxun.utils.image_utils import BuildImage, ImageTemplate
from zhenxun.utils.platform import PlatformUtils

from .database import Sqlite


class NiuNiu:
    @classmethod
    async def get_length(cls, uid: int | str) -> float | None:
        data = await Sqlite.query("users", columns=["length"], conditions={"uid": uid})
        return data[0]["length"] if data else None

    @classmethod
    async def record_length(
        cls, uid: int | str, origin_length: float, new_length: float, action: str
    ):
        await Sqlite.insert(
            "records",
            {
                "uid": uid,
                "origin_length": round(origin_length, 2),
                "new_length": round(new_length, 2),
                "diff": round(new_length - origin_length, 2),
                "action": action,
            },
        )

    @classmethod
    async def update_length(cls, uid: int | str, new_length: float):
        await Sqlite.update(
            "users",
            {"length": new_length, "sex": "boy" if new_length > 0 else "girl"},
            {"uid": uid},
        )

    @classmethod
    async def apply_decay(cls, current_length: float) -> float:
        """动态衰减核心算法"""
        decay_rate = 0.02  # 基础衰减率

        # 动态调整规则
        if current_length > 50:
            decay_rate += min(
                0.1, (current_length - 50) * 0.005
            )  # 超50部分每cm+0.5%衰减
        elif current_length < -50:
            decay_rate -= max(-0.1, (current_length + 50) * 0.005)  # 负值反向衰减

        # 保证衰减方向正确
        if current_length > 0:
            return max(0, current_length * (1 - decay_rate))  # 正向衰减不下穿0
        else:
            return min(0, current_length * (1 + decay_rate))  # 负向衰减不上穿0

    @classmethod
    async def random_length(cls) -> float:
        sql = "SELECT length FROM users ORDER BY length"
        results = await Sqlite.exec(sql)

        if not results:
            origin_length = 10
        else:
            length_values = [row["length"] for row in results]
            n = len(length_values)

            if n == 1:
                origin_length = length_values[0]
            index = int(n * 0.3)
            origin_length = float(length_values[index])
        return round(origin_length * 0.9, 2)

    @classmethod
    async def latest_gluing_time(cls, uid: int) -> str:
        data = await Sqlite.query(
            "records",
            columns=["time"],
            conditions={"uid": uid, "action": "gluing"},
            order_by="time DESC",
            limit=1,
        )
        return data[0]["time"] if data else "暂无记录"

    @classmethod
    async def get_nearest_lengths(cls, target_length: float) -> list[float]:
        # 查询比 target_length 大的最小值
        sql_greater = """
            SELECT MIN(length) AS length FROM users
            WHERE length > ?
        """
        result_greater = await Sqlite.exec(sql_greater, target_length)

        # 查询比 target_length 小的最大值
        sql_less = """
            SELECT MAX(length) AS length FROM users
            WHERE length < ?
        """
        result_less = await Sqlite.exec(sql_less, target_length)

        # 提取结果
        greater_length = (
            result_greater[0]["length"]
            if result_greater and result_greater[0]["length"] is not None
            else 0
        )
        less_length = (
            result_less[0]["length"]
            if result_less and result_less[0]["length"] is not None
            else 0
        )

        return [greater_length, less_length]

    @classmethod
    async def last_fenced_time(cls, uid: int | str) -> float:
        """获取最后一次被击剑时间"""
        data = await Sqlite.query(
            "records",
            columns=["time"],
            conditions={"uid": uid, "action": "fenced"},
            order_by="time DESC",
            limit=1,
        )
        return (
            datetime.strptime(data[0]["time"], "%Y-%m-%d %H:%M:%S").timestamp()
            if data
            else 0
        )

    @classmethod
    async def gluing(cls, origin_length: float, discount: float = 1) -> tuple[float, float]:
        result = await cls.get_nearest_lengths(origin_length)
        if result[0] != 0 or result[1] != 0:
            growth_factor = max(0.5, 1 - abs(origin_length) / 200)  # 长度越大增长越慢
            new_length = (
                origin_length + (result[0] * 0.3 - result[1] * 0.3) * growth_factor * discount
            )
            return round(new_length, 2), round(new_length - origin_length, 2)

        if origin_length <= 0:
            prob = random.choice([-0.8, -0.6, -0.6, -0.4, -0.4, 0.4, 0.4, 0.6, 0.6])
            diff = prob * 0.1 * origin_length + 1
        else:
            prob = random.choice([0.8, 0.6, 0.4, 0.2, 0, -0.2, -0.4, -0.6, -0.8, -1.0])
            diff = prob * 0.1 * origin_length - 1
        raw_new_length = origin_length + diff
        new_length = await cls.apply_decay(raw_new_length)
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
        """牛牛排行

        参数:
            bot: Bot
            num: 排行榜数量
            session: Uninfo
            deep: 是否深度排行
            is_all: 是否显示所有用户
        返回:
            BuildImage: 构造图片
        """
        user_length_map = []
        uid2name = {}
        data_list = []
        order = "length ASC" if deep else "length DESC"
        bot = get_bot(self_id=session.self_id)
        if not is_all and session.group:
            user_ids = {
                user["user_id"]: user["nickname"]
                for user in await bot.get_group_member_list(group_id=session.group.id)
            }
            uid2name = user_ids.copy()
            if user_ids:
                user_data = await Sqlite.query(
                    table="users",
                    columns=["uid", "length"],
                    order_by=order,
                )
                for user in user_data:
                    uid = user["uid"]
                    length = user["length"]
                    if uid in user_ids and (
                        (deep and length <= 0) or (not deep and length >= 0)
                    ):
                        user_length_map.append([uid, length])
                        if len(user_length_map) == num:
                            break
        else:
            user_data = await Sqlite.query(
                table="users",
                columns=["uid", "length"],
                order_by=order,
            )
            for user in user_data:
                if (deep and user["length"] <= 0) or (not deep and user["length"] > 0):
                    user_length_map.append([user["uid"], user["length"]])
                    if len(user_length_map) == num:
                        break
        if not user_length_map:
            return "当前还没有人有牛牛哦..."
        user_id_list = [sublist[0] for sublist in user_length_map]

        if int(session.user.id) in user_id_list:
            index = user_id_list.index(int(session.user.id)) + 1
        else:
            index = "-1（未统计）"

        column_name = ["排名", "头像", "名称", "长度"]
        for i, (uid, length) in enumerate(user_length_map):
            bytes = await PlatformUtils.get_user_avatar(str(uid), "qq", session.self_id)
            data_list.append(
                [
                    f"{i + 1}",
                    (bytes, 30, 30),
                    uid2name.get(uid)
                    or (await bot.get_stranger_info(user_id=uid))["nickname"],
                    length,
                ]
            )
        title_1 = "深度" if deep else "长度"
        if session.group:
            title = f"{title_1}群组内排行"
            tip = f"你的排名在本群第 {index} 位哦!"
        else:
            title = f"{title_1}全局排行"
            tip = f"你的排名在全局第 {index} 位哦!"

        return await ImageTemplate.table_page(title, tip, column_name, data_list)

    @classmethod
    async def get_user_records(cls, uid: int | str, num: int = 10) -> list[dict]:
        """
        获取指定用户的战绩记录

        :param uid: 用户ID
        :param num: 记录数量
        :return: 记录列表
        """
        return await Sqlite.query(
            table="records",
            columns=["action", "origin_length", "new_length", "diff", "time"],
            conditions={"uid": uid},
            order_by="time DESC",
            limit=num,
        )
