import time

from nonebot_plugin_alconna import At, UniMsg

from zhenxun.plugins.niuniu.niuniu_goods.event_manager import use_prop
from zhenxun.plugins.niuniu.niuniu_goods.goods import GOODS
from zhenxun.plugins.niuniu.utils import UserState
from zhenxun.utils.decorator.shop import shop_register


def create_handler(good):
    if good.name != "蒙汗药":
        async def handler(user_id: str): # type: ignore
            await use_prop(user_id, good.name)
        return handler
    else:
        async def handler(message: UniMsg):
            at_list = [i.target for i in message if isinstance(i, At)]
            uid = at_list[0]
            await UserState.update(
                "gluing_time_map",
                {**await UserState.get("gluing_time_map"), uid: time.time() + 300},
            )
        return handler

for good in GOODS:
    shop_register(
        name=good.name,
        price=good.price,
        des=good.des,
        load_status=True,
        icon=good.icon,
        partition="牛牛商店",
    )(create_handler(good))

    if good.name == "蒙汗药":
        @shop_register.before_handle(name=good.name)
        async def before_handle(message: UniMsg):
            at_list = [i.target for i in message if isinstance(i, At)]
            if len(at_list) > 1:
                return "你的蒙汗药只能对一位玩家使用哦!"
            if not at_list:
                return "不能对自己使用哦!请@一位玩家"
