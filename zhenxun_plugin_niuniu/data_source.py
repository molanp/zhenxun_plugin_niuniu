import random
import ujson
import os
import base64
import asyncio
from PIL import Image
from io import BytesIO
from decimal import Decimal as de
from models.group_member_info import GroupInfoUser
from utils.image_utils import BuildMat
from configs.path_config import IMAGE_PATH
from typing import List, Union

path = os.path.dirname(__file__)

def pic2b64(pic: Image) -> str:
    """
    说明:
        PIL图片转base64
    参数:
        :param pic: 通过PIL打开的图片文件
    """
    buf = BytesIO()
    pic.save(buf, format="PNG")
    base64_str = base64.b64encode(buf.getvalue()).decode()
    return "base64://" + base64_str

def random_long():
    """
    注册随机牛子长度
    """
    return de(str(f"{random.randint(1,9)}.{random.randint(00,99)}"))

def fence(rd):
    """
    根据比例减少/增加牛子长度
    Args:
        rd (decimal): 精确计算decimal类型或float,int
    """
    return de(abs(float(rd)*random.random())).quantize(de("0.00"))

def readInfo(file, info=None):
    """
    读取文件信息
    """
    with open(os.path.join(path, file), "r", encoding="utf-8") as f:
        context = f.read()
        if info != None:
            with open(os.path.join(path, file), "w", encoding="utf-8") as f:
                f.write(ujson.dumps(info, indent=4, ensure_ascii=False))
            return {"data": ujson.loads(context.strip())}
        else:
            return ujson.loads(context.strip())

def get_all_users(group):
    """
    获取全部用户及长度
    """
    group = readInfo("data/long.json")[group]
    return group

def fencing(my, oppo, at, qq, group, content):
    """
    击剑判断

    Args:
        my (decimal): 精确计算decimal类型或float,int
        oppo (decimal): 精确计算decimal类型或float,int
        at (str): 被at的人qq号
        qq (str): 自己的qq号
        group (str): 当前群号
        content (dic): 数据
    """
    probability = random.randint(1, 100)
    if oppo <= -100 and my > 0 and 10 < probability <= 20:
        oppo = oppo - 0.25*my
        my = 0 - my/2
        result = f"对方身为魅魔诱惑了你，你同化成魅魔！当前深度{my}cm!"
        content[group][qq] = my
        content[group][at] = oppo
        readInfo('data/long.json', content)
    elif oppo >= 100 and my > 0 and 10 < probability <= 20:
        oppo = oppo + 0.5*my
        my = 0
        result = f"对方以牛头人的荣誉吞噬了你的全部长度！当前长度{my}cm!"
        content[group][qq] = my
        content[group][at] = oppo
        readInfo('data/long.json', content)
    elif my <= -100 and oppo > 0 and 10 < probability <= 20:
        my = my - 0.25*oppo
        oppo = 0 - oppo/2
        result = f"你身为魅魔诱惑了对方，吞噬了对方全部长度！当前长度{my}cm!"
        content[group][qq] = my
        content[group][at] = oppo
        readInfo('data/long.json', content)
    elif my >= 100 and oppo > 0 and 10 < probability <= 20:
        my = my + 0.5*oppo
        oppo = 0
        result = f"你以牛头人的荣誉吞噬了对方的全部长度！当前长度{oppo}cm!"
        content[group][qq] = my
        content[group][at] = oppo
        readInfo('data/long.json', content)
    else:
        if oppo > my:
            probability = random.randint(1, 100)
            if 0 < probability <= 69:
                reduce = fence(my)
                my = my - reduce
                if my < 0:
                    result = random.choice([
                        f"哦吼！？看来你的牛子因为击剑而凹进去了呢！凹进去了{format(reduce,'.2f')}cm！",
                        f"由于对方击剑技术过于高超，造成你的牛子凹了进去呢！凹进去了深{format(reduce,'.2f')}cm哦！",
                        f"好惨啊，本来就不长的牛子现在凹进去了呢！凹进去了{format(reduce,'.2f')}cm呢！"
                    ])
                else:
                    result = f"对方以绝对的长度让你屈服了呢！你的长度减少{format(reduce,'.2f')}cm，当前长度{format(my,'.2f')}cm！"
                oppo = oppo + reduce
                content[group][qq] = my
                content[group][at] = oppo
                readInfo('data/long.json', content)

            else:
                reduce = fence(oppo)
                oppo = oppo - reduce
                my = my + reduce
                if my < 0:
                    result = random.choice([
                        f"哦吼！？你的牛子在长大欸！长大了{format(reduce,'.2f')}cm！",
                        f"牛子凹进去的深度变浅了欸！变浅了{format(reduce,'.2f')}cm！"
                    ])
                else:
                    result = f"虽然你不够长，但是你逆袭了呢！你的长度增加{format(reduce,'.2f')}cm，当前长度{format(my,'.2f')}cm！"
                content[group][qq] = my
                content[group][at] = oppo
                readInfo('data/long.json', content)
        elif my > oppo:
            probability = random.randint(1, 100)
            if 0 < probability <= 80:
                reduce = fence(oppo)
                oppo = oppo - reduce
                my = my + reduce
                if my < 0:
                    result = random.choice([
                        f"哦吼！？你的牛子在长大欸！长大了{format(reduce,'.2f')}cm！",
                        f"牛子凹进去的深度变浅了欸！变浅了{format(reduce,'.2f')}cm！"
                    ])
                else:
                    result = f"你以绝对的长度让对方屈服了呢！你的长度增加{format(reduce,'.2f')}cm，当前长度{format(my,'.2f')}cm！"
                content[group][qq] = my
                content[group][at] = oppo
                readInfo('data/long.json', content)
            else:
                reduce = fence(my)
                my = my - reduce
                if my < 0:
                    result = random.choice([
                        f"哦吼！？看来你的牛子因为击剑而凹进去了呢！目前深度{format(reduce,'.2f')}cm！",
                        f"由于对方击剑技术过于高超，造成你的牛子凹了进去呢！当前深度{format(reduce,'.2f')}cm！",
                        f"好惨啊，本来就不长的牛子现在凹进去了呢！凹进去了{format(reduce,'.2f')}cm！"
                    ])
                else:
                    result = f"虽然你比较长，但是对方逆袭了呢！你的长度减少{format(reduce,'.2f')}cm，当前长度{format(my,'.2f')}cm！"
                oppo = oppo + reduce
                content[group][qq] = my
                content[group][at] = oppo
                readInfo('data/long.json', content)
        else:
            probability = random.randint(1, 100)
            reduce = fence(oppo)
            if 0 < probability <= 50:
                oppo = oppo - reduce
                my = my + reduce
                if my < 0:
                    result = random.choice([
                        f"哦吼！？你的牛子在长大欸！长大了{format(reduce,'.2f')}cm！",
                        f"牛子凹进去的深度变浅了欸！变浅了{format(reduce,'.2f')}cm！"
                    ])
                else:
                    result = f"你以技艺的高超让对方屈服啦！你的长度增加{format(reduce,'.2f')}cm，当前长度{format(my,'.2f')}cm！"
                content[group][qq] = my
                content[group][at] = oppo
                readInfo('data/long.json', content)
            else:
                my = my - reduce
                if my < 0:
                    result = random.choice([
                        f"哦吼！？看来你的牛子因为击剑而凹进去了呢！目前深度{format(reduce,'.2f')}cm！",
                        f"由于对方击剑技术过于高超，造成你的牛子凹了进去呢！当前深度{format(reduce,'.2f')}cm！",
                        f"好惨啊，本来就不长的牛子现在凹进去了呢！凹进去了{format(reduce,'.2f')}cm！"
                    ])
                else:
                    result = f"由于对方击剑技术过于高超，你的长度减少{format(reduce,'.2f')}cm，当前长度{format(my,'.2f')}cm！"
                oppo = oppo + reduce
                content[group][qq] = my
                content[group][at] = oppo
                readInfo('data/long.json', content)
    return result

async def init_rank(
    title: str, all_user_id: List[int], all_user_data: List[float], group_id: int, total_count: int = 10
) -> BuildMat:
    """
    说明:
        初始化通用的数据排行榜
    参数:
        :param title: 排行榜标题
        :param all_user_id: 所有用户的qq号
        :param all_user_data: 所有用户需要排行的对应数据
        :param group_id: 群号，用于从数据库中获取该用户在此群的昵称
        :param total_count: 获取人数总数
    """
    _uname_lst = []
    _num_lst = []
    for i in range(len(all_user_id) if len(all_user_id) < total_count else total_count):
        _max = max(all_user_data)
        max_user_id = all_user_id[all_user_data.index(_max)]
        all_user_id.remove(max_user_id)
        all_user_data.remove(_max)
        try:
            user_name = (
                await GroupInfoUser.get_member_info(max_user_id, group_id)
            ).user_name
        except AttributeError:
            user_name = f"{max_user_id}"
        _uname_lst.append(user_name)
        _num_lst.append(_max)
    _uname_lst.reverse()
    _num_lst.reverse()
    return await asyncio.get_event_loop().run_in_executor(
        None, _init_rank_graph, title, _uname_lst, _num_lst
    )

def _init_rank_graph(
    title: str, _uname_lst: List[str], _num_lst: List[Union[int, float]]
) -> BuildMat:
    """
    生成排行榜统计图
    :param title: 排行榜标题
    :param _uname_lst: 用户名列表
    :param _num_lst: 数值列表
    """
    image = BuildMat(
        y=_num_lst,
        y_name="* 可以在命令后添加数字来指定排行人数 至多 50 *",
        mat_type="barh",
        title=title,
        x_index=_uname_lst,
        display_num=True,
        x_rotate=30,
        background=[
            f"{IMAGE_PATH}/background/create_mat/{x}"
            for x in os.listdir(f"{IMAGE_PATH}/background/create_mat")
        ],
        bar_color=["*"],
    )
    image.gen_graph()
    return image
