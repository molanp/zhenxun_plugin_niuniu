import time

from .niuniu import NiuNiu
from .niuniu_goods.event_manager import use_prop
from .niuniu_goods.goods import GOODS
from .utils import UserState
from zhenxun.services.log import logger
from zhenxun.utils.decorator.shop import NotMeetUseConditionsException, shop_register


def create_handler(good):
    if good.name == "蒙汗药":

        async def handler(user_id: str, at_users: list[str]): # type: ignore
            if len(at_users) > 1:
                raise NotMeetUseConditionsException("你的蒙汗药只能对一位玩家使用哦!")
            if not at_users:
                raise NotMeetUseConditionsException("@人了吗？你要对你自己使用吗？")
            if at_users[0] == user_id:
                raise NotMeetUseConditionsException("不能对自己使用哦!请@一位玩家")
            uid = at_users[0]
            logger.info(f"{uid} 被 {user_id} 使用了蒙汗药")
            await UserState.set_or_get(
                "gluing_time_map", uid, 
                (
                   await UserState.set_or_get(
                      "gluing_time_map",
                      uid,
                      default=time.time()
                      ))+300)

    elif good.name == "美波里的神奇药水":
        async def handler(user_id: str): # type: ignore
            origin_length = await NiuNiu.get_length(user_id)
            if origin_length is None:
                raise NotMeetUseConditionsException("你没有牛牛数据哦!")
            new_length = origin_length * -1
            await NiuNiu.update_length(user_id, new_length)
            await NiuNiu.record_length(user_id, origin_length, new_length, "drug")
            return "你使用了美波里的神奇药水，性别发生了逆转"
    else:

        async def handler(user_id: str):  # type: ignore
            await use_prop(user_id, good.name)

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
