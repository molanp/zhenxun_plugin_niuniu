import random
import time

from nonebot_plugin_uninfo import Uninfo

from zhenxun.configs.config import BotSetting
from zhenxun.models.sign_user import SignUser

from .model import NiuNiuUser
from .niuniu import NiuNiu
from .utils import UserState
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
    async def fencing(cls, my_length, oppo_length, at_qq, my_qq) -> str:
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
        my_buff = await get_buffs(my_qq)
        fencing_weight = my_buff.fencing_weight

        # 传递到胜率计算
        win_probability = await cls.calculate_win_probability(
            my_length, oppo_length, fencing_weight
        )

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
    async def calculate_win_probability(
        cls, height_a, height_b, fencing_weight=1.0, min_win=0.05, max_win=0.85
    ):
        # 选手 A 的初始胜率
        p_a = 0.85 * fencing_weight

        # 计算长度比例，考虑允许负数（取绝对值比较大小）
        height_ratio = max(abs(height_a), abs(height_b)) / min(
            abs(height_a), abs(height_b)
        )

        # 根据长度比例计算胜率减少率
        reduction_rate = 0.1 * (height_ratio - 1)

        # 计算 A 的胜率减少量
        reduction = p_a * reduction_rate

        # 调整 A 的胜率
        adjusted_p_a = p_a - reduction

        # 如果 height_a 为负，则反转胜率方向（负数表示对抗优势减弱）
        if height_a < 0:
            adjusted_p_a = 1.0 - adjusted_p_a

        return max(min_win, min(adjusted_p_a, max_win))

    @classmethod
    async def apply_skill(
        cls, my, oppo, increase_length, uid
    ) -> tuple[str, float, float]:
        """
        应用击剑技巧并生成结果字符串。

        Args:
            my (float): 长度1。
            oppo (float): 长度2。
            increase_length (bool): 是否增加长度。
            uid (str): 用户 ID。
        """
        base_change = min(abs(my), abs(oppo)) * 0.1  # 基于较小值计算变化量
        reduce = await cls.fence(base_change)  # 传入基础变化量
        reduce *= await NiuNiu.apply_decay(1)  # 🚨 全局衰减系数

        # 添加动态平衡系数
        balance_factor = 1 - abs(my - oppo) / 100  # 差距越大变化越小
        reduce *= max(0.3, balance_factor)

        # 获取用户 Buff 效果
        buff = await get_buffs(uid)
        if buff:
            reduce *= buff.glue_effect
        reduce = round(reduce, 2)

        if increase_length:
            my += reduce
            oppo -= 0.8 * reduce
            if my < 0:
                result = random.choice(
                    [
                        f"哦吼!？你的牛牛在长大欸!长大了{reduce}cm!",
                        f"牛牛凹进去的深度变浅了欸!变浅了{reduce}cm!",
                    ]
                )
            else:
                result = (
                    f"你以绝对的长度让对方屈服了呢!你的长度增加{reduce}cm,"
                    f"对方减少了{round(0.8 * reduce, 2)}cm!"
                    f"你当前长度为{round(my, 2)}cm!"
                )
        else:
            my -= reduce
            oppo += 0.8 * reduce
            if my < 0:
                result = random.choice(
                    [
                        f"哦吼!？看来你的牛牛因为击剑而凹进去了呢🤣🤣🤣!凹进去了{reduce}cm!",
                        f"由于对方击剑技术过于高超,造成你的牛牛凹了进去呢😰!凹进去了{reduce}cm!",
                        f"好惨啊,本来就不长的牛牛现在凹进去了呢😂!凹进去了{reduce}cm!",
                    ]
                )
            else:
                result = (
                    f"对方以绝对的长度让你屈服了呢!你的长度减少{reduce}cm,"
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

    @classmethod
    async def with_bot(cls, session: Uninfo, user_id: str) -> str:
        """
        获取 bot 实例

        Args:
            session (Uninfo): 会话对象
            user_id (str): 用户 ID

        Returns:
            str: 击剑结果
        """
        bot = await NiuNiu.get_length(session.self_id)
        user = await NiuNiu.get_length(user_id)
        assert user is not None
        if bot is not None:
            await NiuNiuUser.filter(uid=session.self_id).delete()
        sign_user = await SignUser.get_or_none(user_id=user_id)
        impression = 0 if sign_user is None else sign_user.impression
        if impression >= 50:
            _, new_user, _ = await cls.apply_skill(user, 0, True, user_id)
            r = random.choice(
                [
                    "{nickname}喜欢你，你的长度增加了{diff}cm呢！",
                ]
            )
        else:
            _, new_user, _ = await cls.apply_skill(user, 0, False, user_id)
            r = random.choice(
                [
                    "你弄疼{nickname}了，给你头咬掉，牛牛长度变短{diff}cm",
                    "{nickname}感到恶心，脚踩了你的牛牛，牛牛长度变短{diff}cm",
                    "你被{nickname}的牛牛戳到了，牛牛长度变短{diff}cm",
                    "{nickname}偷偷给你下了药，你的牛牛长度变短了{diff}cm",
                ]
            )
        await NiuNiuUser.filter(uid=user_id).update(length=user)
        await NiuNiu.record_length(user_id, user, new_user, "fencing")
        await UserState.update("fence_time_map", user_id, time.time() + random.randrange(120, 300))
        return r.format(
            nickname=BotSetting.self_nickname,
            diff=new_user - user,
        )
