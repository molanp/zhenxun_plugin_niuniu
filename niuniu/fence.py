import random
import time

from zhenxun.plugins.niuniu.niuniu import NiuNiu


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
            my_length (decimal): 我的当前长度
            oppo_length (decimal): 对手的当前长度
            at_qq (str): 被 @ 的人的 QQ 号码。
            my_qq (str): 我的 QQ 号码。
        """
        origin_my = my_length
        origin_oppo = oppo_length
        # 定义损失和吞噬比例
        loss_limit = 0.25
        devour_limit = 0.27

        # 生成一个随机数
        probability = random.randint(1, 100)

        # 根据不同情况执行不同的击剑逻辑
        if oppo_length <= -100 and my_length > 0 and 10 < probability <= 20:
            oppo_length *= 0.65 + min(abs(loss_limit * my_length), abs(1.5 * my_length))
            my_length -= min(abs(loss_limit * my_length), abs(1.5 * my_length))
            result = f"对方身为魅魔诱惑了你,你同化成魅魔!当前长度{my_length}cm!"
        elif oppo_length >= 100 and my_length > 0 and 10 < probability <= 20:
            oppo_length *= 0.65 + min(
                abs(devour_limit * my_length), abs(1.5 * my_length)
            )
            my_length -= min(abs(devour_limit * my_length), abs(1.5 * my_length))
            result = f"对方以牛头人的荣誉摧毁了你的牛牛!当前长度{round(my_length, 2)}cm!"
        elif my_length <= -100 and oppo_length > 0 and 10 < probability <= 20:
            my_length *= 0.65 + min(
                abs(loss_limit * oppo_length), abs(1.5 * oppo_length)
            )
            oppo_length -= min(abs(loss_limit * oppo_length), abs(1.5 * oppo_length))
            result = f"你身为魅魔诱惑了对方,吞噬了对方部分长度!当前长度{my_length}cm!"
        elif my_length >= 100 and oppo_length > 0 and 10 < probability <= 20:
            my_length *= 0.65 + min(
                abs(devour_limit * oppo_length), abs(1.5 * oppo_length)
            )
            oppo_length -= min(abs(devour_limit * oppo_length), abs(1.5 * oppo_length))
            result = f"你以牛头人的荣誉摧毁了对方的牛牛!当前长度{round(my_length, 2)}cm!"
        else:
            # 通过击剑技巧来决定结果
            result, my_length, oppo_length = await cls.determine_result_by_skill(
                my_length, oppo_length
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
    async def calculate_win_probability(cls, height_a, height_b):
        # 选手 A 的初始胜率为 85%
        p_a = 0.85
        # 计算长度比例
        height_ratio = max(height_a, height_b) / min(height_a, height_b)

        # 根据长度比例计算胜率减少率
        reduction_rate = 0.1 * (height_ratio - 1)

        # 计算 A 的胜率减少量
        reduction = p_a * reduction_rate

        # 调整 A 的胜率
        adjusted_p_a = p_a - reduction

        # 返回调整后的胜率
        return max(adjusted_p_a, 0.01)

    @classmethod
    async def determine_result_by_skill(cls, my_length, oppo_length):
        """
        根据击剑技巧决定结果。

        Args:
            my_length (decimal): 我的当前长度。
            oppo_length (decimal): 对手的当前长度。

        Returns:
            str: 包含结果的字符串。
        """
        # 生成一个随机数
        probability = random.randint(0, 100)

        # 根据不同情况决定结果
        if (
            0
            < probability
            <= await cls.calculate_win_probability(my_length, oppo_length) * 100
        ):
            return await cls.apply_skill(my_length, oppo_length, True)
        else:
            return await cls.apply_skill(my_length, oppo_length, False)

    @classmethod
    async def apply_skill(cls, my, oppo, increase_length):
        """
        应用击剑技巧并生成结果字符串。

        Args:
            my (decimal): 长度1。
            oppo (decimal): 长度2。
            increase_length (bool): my是否增加长度。

        Returns:
            str: 包含结果的数组。
        """
        reduce = await cls.fence(oppo)
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
                result = f"你以绝对的长度让对方屈服了呢!你的长度增加{reduce}cm,对方减少了{0.8*reduce}cm!你当前长度为{round(my, 2)}cm!"  # noqa: E501
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
                result = f"对方以绝对的长度让你屈服了呢!你的长度减少{reduce}cm,当前长度{round(my, 2)}cm!"  # noqa: E501
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
        await NiuNiu.update_length(my_qq, new_my)
        await NiuNiu.record_length(my_qq, origin_my, new_my, "fencing")
        await NiuNiu.update_length(at_qq, new_oppo)
        await NiuNiu.record_length(at_qq, origin_oppo, new_oppo, "fenced")
