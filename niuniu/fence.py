import random
import time

from .utils import UserState

from .model import NiuNiuUser
from .niuniu import NiuNiu
from .niuniu_goods.event_manager import get_buffs


class Fencing:
    @classmethod
    async def fence(cls, rd):
        """
        根据比例减少/增加牛牛长度
        Args:
            rd (float, int): 随机数
        Returns:
            float: 四舍五入后的结果
        """
        rd -= time.localtime().tm_sec % 10
        return round(abs(rd + random.uniform(0.13, 0.24) * rd) * 0.3, 2)

    @classmethod
    async def fencing(cls, my_length, oppo_length, at_qq, my_qq):
        """
        确定击剑比赛的结果。

        Args:
            my_length (float): 我的当前长度
            oppo_length (float): 对手的当前长度
            at_qq (str): 被 @ 的人的 QQ 号码。
            my_qq (str): 我的 QQ 号码。
        """
        origin_my = my_length
        origin_oppo = oppo_length
        # 获取用户当前道具的击剑加成
        my_buff = await apply_buff(my_qq)
        fencing_weight = my_buff.get("fencing_weight", 1.0)

        # 传递到胜率计算
        win_probability = await cls.calculate_win_probability(
            my_length, oppo_length, fencing_weight
        )

        # 计算击剑获胜概率
        win_probability = await cls.calculate_win_probability(my_length, oppo_length)

        # 根据胜率决定胜负
        result = random.choices(
            ["win", "lose"], weights=[win_probability, 1 - win_probability], k=1
        )[0]

        if result == "win":
            result, my_length, oppo_length = await cls.apply_skill(
                my_length, oppo_length, True, my_qq
            )
        else:
            result, my_length, oppo_length = await cls.apply_skill(
                my_length, oppo_length, False, at_qq
            )

        # 更新数据并返回结果
        await cls.update_data(
            {
                "my_qq": my_qq,
                "at_qq": at_qq,
                "new_my": my_length,
                "new_oppo": oppo_length,
                "origin_my": origin_my,
                "origin_oppo": origin_oppo,
            }
        )
        return result

    @classmethod
    async def calculate_win_probability(cls, height_a, height_b, fencing_weight=1.0):
        # 选手 A 的初始胜率为 85%
        p_a = 0.85 * fencing_weight
        # 计算长度比例
        height_ratio = max(height_a, height_b) / min(height_a, height_b)

        # 根据长度比例计算胜率减少率
        reduction_rate = 0.1 * (height_ratio - 1)

        # 计算 A 的胜率减少量
        reduction = p_a * reduction_rate

        # 调整 A 的胜率
        adjusted_p_a = p_a - reduction

        # 返回调整后的胜率
        return max(adjusted_p_a, 0.10)

    @classmethod
    async def apply_skill(cls, my, oppo, increase_length, uid):
        """
        应用击剑技巧并生成结果字符串。

        Args:
            my (float): 长度1。
            oppo (float): 长度2。
            increase_length (bool): 是否增加长度。
            uid (str): 用户 ID。

        Returns:
            str: 包含结果的字符串。
        """
        base_change = min(abs(my), abs(oppo)) * 0.1  # 基于较小值计算变化量
        reduce = await cls.fence(base_change)  # 传入基础变化量
        reduce *= await NiuNiu.apply_decay(1)  # 🚨 全局衰减系数

        # 添加动态平衡系数
        balance_factor = 1 - abs(my - oppo) / 100  # 差距越大变化越小
        reduce *= max(0.3, balance_factor)

        # 获取用户 Buff 效果
        buff = await get_buffs(uid)
        if buff and buff.get("expire_time", 0) > time.time():
            reduce *= buff.get("effect", 1)

        if increase_length:
            my += reduce
            oppo -= 0.8 * reduce
            if my < 0:
                result = random.choice(
                    [
                        f"哦吼!？你的牛牛在长大欸!长大了{round(reduce, 2)}cm!",
                        f"牛牛凹进去的深度变浅了欸!变浅了{round(reduce, 2)}cm!",
                    ]
                )
            else:
                result = (
                    f"你以绝对的长度让对方屈服了呢!你的长度增加{round(reduce, 2)}cm,"
                    f"对方减少了{round(0.8 * reduce, 2)}cm!你当前长度为{round(my, 2)}cm!"
                )
        else:
            my -= reduce
            oppo += 0.8 * reduce
            if my < 0:
                result = random.choice(
                    [
                        f"哦吼!？看来你的牛牛因为击剑而凹进去了呢🤣🤣🤣!凹进去了{round(reduce, 2)}cm!",
                        f"由于对方击剑技术过于高超,造成你的牛牛凹了进去呢😰!凹进去了{round(reduce, 2)}cm!",
                        f"好惨啊,本来就不长的牛牛现在凹进去了呢😂!凹进去了{round(reduce, 2)}cm!",
                    ]
                )
            else:
                result = (
                    f"对方以绝对的长度让你屈服了呢!你的长度减少{round(reduce, 2)}cm,"
                    f"当前长度{round(my, 2)}cm!"
                )
        return result, my, oppo

    @classmethod
    async def update_data(cls, data: dict):
        """
        更新数据

        Args:
            data (dict): 数据
        """
        my_qq = data["my_qq"]
        at_qq = data["at_qq"]
        new_my = round(data["new_my"], 2)
        new_oppo = round(data["new_oppo"], 2)
        origin_my = round(data["origin_my"], 2)
        origin_oppo = round(data["origin_oppo"], 2)
        await NiuNiuUser.filter(uid=my_qq).update(length=new_my)
        await NiuNiu.record_length(my_qq, origin_my, new_my, "fencing")
        await NiuNiuUser.filter(uid=at_qq).update(length=new_oppo)
        await NiuNiu.record_length(at_qq, origin_oppo, new_oppo, "fenced")
