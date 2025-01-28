# import random
# import ujson
# import os
# import base64
# import asyncio
# import time
# from PIL import Image
# from io import BytesIO
# from pathlib import Path
# from models.group_member_info import GroupInfoUser
# from utils.image_utils import BuildMat
# from configs.path_config import IMAGE_PATH
# from typing import List, Union
# import numpy as np
# from concurrent.futures import ThreadPoolExecutor
import random

from nonebot_plugin_uninfo import Uninfo

from zhenxun.models.friend_user import FriendUser
from zhenxun.models.group_member_info import GroupInfoUser
from zhenxun.models.sign_log import SignLog
from zhenxun.models.sign_user import SignUser
from zhenxun.models.user_console import UserConsole
from zhenxun.services.log import logger
from zhenxun.utils.image_utils import BuildImage, ImageTemplate
from zhenxun.utils.platform import PlatformUtils

from .database import Sqlite


class NiuNiu:
    @classmethod
    async def get_length(cls, uid: str) -> str | None:
        data = Sqlite.query("users", columns=["length"], conditions={"uid": uid})
        return data[0]["length"] if isinstance(data, list) else None

    @classmethod
    async def random_length(cls) -> str:
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
        return str(round(origin_length * 0.9, 2))

    @classmethod
    async def latest_gluing_time(cls, uid: str) -> str:
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
        cls, session: Uninfo, num: int, group_id: str | None = None, deep: bool = False
    ) -> BuildImage | str:
        """牛牛排行

        参数:
            session: Uninfo
            num: 排行榜数量
            group_id: 群组id

        返回:
            BuildImage: 构造图片
        """
        user_length_map = []
        data_list = []
        order = "length ASC" if deep else "length DESC"
        if group_id:
            user_ids = await GroupInfoUser.get_all_uid(group_id=group_id)
            print("group_id", group_id)
            print("user_ids", user_ids)
            if user_ids:
                user_data = await Sqlite.query(
                    table="users",
                    columns=["uid", "length"],
                    order_by=order,
                    limit=num,
                )
                for user in user_data:
                    uid = user["uid"]
                    length = user["length"]
                    if uid in user_ids:
                        print("add", uid, length)
                        user_length_map.append([uid, length])
        else:
            user_data = await Sqlite.query(
                table="users",
                columns=["uid", "length"],
                order_by=order,
                limit=num,
            )
            user_length_map.extend([user["uid"], user["length"]] for user in user_data)
        if not user_length_map:
            return "当前还没有人有牛牛哦..."
        user_id_list = [sublist[0] for sublist in user_length_map]

        if session.user.id in user_id_list:
            index = user_id_list.index(session.user.id) + 1
        else:
            index = "-1（未统计）"

        column_name = ["排名", "头像", "名称", "长度"]
        friend_list = await FriendUser.filter(
            user_id__in=user_id_list
        ).values_list("user_id", "user_name")
        uid2name = {f[0]: f[1] for f in friend_list}
        for i, (uid, length) in enumerate(user_length_map):
            bytes = await PlatformUtils.get_user_avatar(uid, "qq", session.self_id)
            data_list.append(
                [
                    f"{i + 1}",
                    (bytes, 30, 30),
                    uid2name.get(uid, "未知用户"),
                    length,
                ]
            )

        if group_id:
            title = "长度群组内排行"
            tip = f"你的排名在本群第 {index} 位哦!"
        else:
            title = "长度全局排行"
            tip = f"你的排名在全局第 {index} 位哦!"

        return await ImageTemplate.table_page(title, tip, column_name, data_list)


# def pic2b64(pic: Image) -> str:
#     """
#     说明:
#         PIL图片转base64
#     参数:
#         :param pic: 通过PIL打开的图片文件
#     """
#     buf = BytesIO()
#     pic.save(buf, format="PNG")
#     base64_str = base64.b64encode(buf.getvalue()).decode()
#     return "base64://" + base64_str


# def random_long():
#     """
#     注册随机牛牛长度
#     """
#     return de(str(f"{random.randint(1,9)}.{random.randint(00,99)}"))


# def hit_glue(l):
#     l -= de(1)
#     return de(abs(de(random.random())*l/de(2))).quantize(de("0.00"))


# def fence(rd):
#     """

#     根据比例减少/增加牛牛长度
#     Args:
#         rd (decimal): 精确计算decimal类型或float,int
#     """
#     rd -= de(time.localtime().tm_sec % 10)
#     if rd > 1000000:
#         return de(rd - de(random.uniform(0.13, 0.34))*rd)
#     return de(abs(rd*de(random.random()))).quantize(de("0.00"))


# def round_numbers(data, num_digits=2):
#     """
#     递归地四舍五入所有数字

#     Args:
#         data (any): 要处理的数据
#         num_digits (int, optional): 四舍五入的小数位数. Defaults to 2.

#     Returns:
#         any: 处理后的数据
#     """
#     if isinstance(data, dict):
#         with ThreadPoolExecutor() as executor:
#             processed_values = list(executor.map(lambda v: round_numbers(v, num_digits), data.values()))
#         return {k: processed_values[i] for i, k in enumerate(data.keys())}
#     elif isinstance(data, list):
#         with ThreadPoolExecutor() as executor:
#             processed_items = list(executor.map(lambda item: round_numbers(item, num_digits), data))
#         return processed_items
#     elif isinstance(data, (int, float)):
#         return round(data, num_digits)
#     elif isinstance(data, np.ndarray):
#         return np.round(data, num_digits)
#     else:
#         return data


# def ReadOrWrite(file, w=None):
#     """
#     读取或写入文件

#     Args:
#         file (string): 文件路径,相对于脚本
#         w (any, optional): 写入内容,不传入则读. Defaults to None.

#     Returns:
#         any: 文件内容(仅读取)
#     """
#     file_path = Path(__file__).resolve().parent / file
#     if w is not None:
#         # 对要写入的内容进行四舍五入处理
#         w_rounded = round_numbers(w)
#         with file_path.open("w", encoding="utf-8") as f:
#             f.write(ujson.dumps(w_rounded, indent=4, ensure_ascii=False))
#         return True
#     else:
#         with file_path.open("r", encoding="utf-8") as f:
#             return ujson.loads(f.read().strip())


# def get_all_users(group):
#     """
#     获取全部用户及长度
#     """
#     return ReadOrWrite("data/long.json")[group]


# def fencing(my_length, oppo_length, at_qq, my_qq, group, content={}):
#     """
#     确定击剑比赛的结果。

#     Args:
#         my_length (decimal): 我的当前长度,decimal 类型以确保精度。
#         oppo_length (decimal): 对手的当前长度,decimal 类型以确保精度。
#         at_qq (str): 被 @ 的人的 QQ 号码。
#         my_qq (str): 我的 QQ 号码。
#         group (str): 当前群号码。
#         content (dict): 用于存储长度的数据。
#     """
#     # 定义损失和吞噬比例
#     loss_limit = de(0.25)
#     devour_limit = de(0.27)

#     # 生成一个随机数
#     probability = random.randint(1, 100)

#     # 根据不同情况执行不同的击剑逻辑
#     if oppo_length <= -100 and my_length > 0 and 10 < probability <= 20:
#         oppo_length *= de(0.85)
#         my_length -= min(abs(loss_limit * my_length), abs(de(1.5)*my_length))
#         result = f"对方身为魅魔诱惑了你,你同化成魅魔!当前长度{my_length}cm!"

#     elif oppo_length >= 100 and my_length > 0 and 10 < probability <= 20:
#         oppo_length *= de(0.85)
#         my_length -= min(abs(devour_limit * my_length), abs(de(1.5)*my_length))
#         result = f"对方以牛头人的荣誉摧毁了你的牛牛!当前长度{my_length}cm!"

#     elif my_length <= -100 and oppo_length > 0 and 10 < probability <= 20:
#         my_length *= de(0.85)
#         oppo_length -= min(abs(loss_limit * oppo_length),
#                            abs(de(1.5)*oppo_length))
#         result = f"你身为魅魔诱惑了对方,吞噬了对方部分长度!当前长度{my_length}cm!"

#     elif my_length >= 100 and oppo_length > 0 and 10 < probability <= 20:
#         my_length *= de(0.85)
#         oppo_length -= min(abs(devour_limit * oppo_length),
#                            abs(de(1.5)*oppo_length))
#         result = f"你以牛头人的荣誉摧毁了对方的牛牛!当前长度{my_length}cm!"

#     else:
#         # 通过击剑技巧来决定结果
#         result, my_length, oppo_length = determine_result_by_skill(
#             my_length, oppo_length)

#     # 更新数据并返回结果
#     update_data(group, my_qq, oppo_length, at_qq, my_length, content)
#     return result


# def calculate_win_probability(height_a, height_b):
#     # 选手 A 的初始胜率为 90%
#     p_a = de(0.9)
#     # 计算长度比例
#     height_ratio = max(height_a, height_b) / min(height_a, height_b)

#     # 根据长度比例计算胜率减少率
#     reduction_rate = de(0.1) * (height_ratio - 1)

#     # 计算 A 的胜率减少量
#     reduction = p_a * reduction_rate

#     # 调整 A 的胜率
#     adjusted_p_a = p_a - reduction

#     # 返回调整后的胜率
#     return max(adjusted_p_a, de(0.01))


# def determine_result_by_skill(my_length, oppo_length):
#     """
#     根据击剑技巧决定结果。

#     Args:
#         my_length (decimal): 我的当前长度。
#         oppo_length (decimal): 对手的当前长度。

#     Returns:
#         str: 包含结果的字符串。
#     """
#     # 生成一个随机数
#     probability = random.randint(0, 100)

#     # 根据不同情况决定结果
#     if 0 < probability <= calculate_win_probability(my_length, oppo_length)*100:
#         return apply_skill(my_length, oppo_length, True)
#     else:
#         return apply_skill(my_length, oppo_length, False)


# def apply_skill(my, oppo, increase_length1):
#     """
#     应用击剑技巧并生成结果字符串。

#     Args:
#         my (decimal): 长度1。
#         oppo (decimal): 长度2。
#         increase_length1 (bool): my是否增加长度。

#     Returns:
#         str: 包含结果的数组。
#     """
#     reduce = fence(oppo)
#     if increase_length1:
#         my += reduce
#         oppo -= de(0.8)*reduce
#         if my < 0:
#             result = random.choice([
#                 f"哦吼!？你的牛牛在长大欸!长大了{reduce}cm!",
#                 f"牛牛凹进去的深度变浅了欸!变浅了{reduce}cm!"
#             ])
#         else:
#             result = f"你以绝对的长度让对方屈服了呢!你的长度增加{reduce}cm,当前长度{my}cm!"
#     else:
#         my -= reduce
#         oppo += de(0.8)*reduce
#         if my < 0:
#             result = random.choice([
#                 f"哦吼!？看来你的牛牛因为击剑而凹进去了呢🤣🤣🤣!凹进去了{reduce}cm!",
#                 f"由于对方击剑技术过于高超,造成你的牛牛凹了进去呢😰!凹进去了{reduce}cm!",
#                 f"好惨啊,本来就不长的牛牛现在凹进去了呢😂!凹进去了{reduce}cm!"
#             ])
#         else:
#             result = f"对方以绝对的长度让你屈服了呢!你的长度减少{reduce}cm,当前长度{my}cm!"
#     return result, my, oppo


# def update_data(group, my_qq, my_length, at_qq, oppo_length, content):
#     """
#     更新数据。

#     Args:
#         group (str): 群号。
#         my_qq (str): 我的 QQ 号。
#         my_length (decimal): 我的当前长度。
#         at_qq (str): 被 @ 的 QQ 号。
#         oppo_length (decimal): 对手的当前长度。
#         content (dict): 数据存储。
#     """
#     # 这里需要根据实际需求进行数据更新
#     content[group][my_qq] = my_length
#     content[group][at_qq] = oppo_length
#     ReadOrWrite("data/long.json", content)
#     return True


# async def init_rank(
#     title: str, all_user_id: List[int], all_user_data: List[float], group_id: int, total_count: int = 10
# ) -> BuildMat:
#     """
#     说明:
#         初始化通用的数据排行榜
#     参数:
#         :param title: 排行榜标题
#         :param all_user_id: 所有用户的qq号
#         :param all_user_data: 所有用户需要排行的对应数据
#         :param group_id: 群号,用于从数据库中获取该用户在此群的昵称
#         :param total_count: 获取人数总数
#     """
#     _uname_lst = []
#     _num_lst = []
#     for i in range(len(all_user_id) if len(all_user_id) < total_count else total_count):
#         _max = max(all_user_data)
#         max_user_id = all_user_id[all_user_data.index(_max)]
#         all_user_id.remove(max_user_id)
#         all_user_data.remove(_max)
#         try:
#           # 暂未找到nonebot方法获取群昵称
#             user_name = max_user_id
#         except AttributeError:
#             user_name = f"{max_user_id}"
#         _uname_lst.append(user_name)
#         _num_lst.append(_max)
#     _uname_lst.reverse()
#     _num_lst.reverse()
#     return await asyncio.get_event_loop().run_in_executor(
#         None, _init_rank_graph, title, _uname_lst, _num_lst
#     )


# def _init_rank_graph(
#     title: str, _uname_lst: List[str], _num_lst: List[Union[int, float]]
# ) -> BuildMat:
#     """
#     生成排行榜统计图
#     :param title: 排行榜标题
#     :param _uname_lst: 用户名列表
#     :param _num_lst: 数值列表
#     """
#     image = BuildMat(
#         y=_num_lst,
#         y_name="* 可以在命令后添加数字来指定排行人数 至多 50 *",
#         mat_type="barh",
#         title=title,
#         x_index=_uname_lst,
#         display_num=True,
#         x_rotate=30,
#         background=[
#             f"{IMAGE_PATH}/background/create_mat/{x}"
#             for x in os.listdir(f"{IMAGE_PATH}/background/create_mat")
#         ],
#         bar_color=["*"],
#     )
#     image.gen_graph()
#     return image
