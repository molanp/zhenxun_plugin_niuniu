from .model import PropModel

GOODS = [
    PropModel(
        name="伟哥",
        price=200,
        des="神秘小药丸，下次抽到击剑胜率的概率翻倍，持续10分钟",
        icon="weige.png",
        duration=60*10,
        fencing_weight=1.5,
    ),
    PropModel(
        name="蒙汗药",
        price=250,
        icon="menghanyao.png",
        des="给对方打胶CD加长300s",
    ),
    PropModel(
        name="鱼板",
        price=300,
        icon="yuban.png",
        duration=60*20,
        des="会让人变得香香软软的东西，使用后自己下次打胶变短概率翻倍，遇到负面效果概率翻倍，持续20分钟",
        glue_effect=0.3,
        glue_negative_weight=5,
    ),
    PropModel(
        name="美波里的神奇药水",
        price=500,
        des="谁知道会有什么效果呢",
        icon="meiboli.png",
    )
]

EVENT_BUFF_MAP = [
    PropModel(
        name="冷静期",
        duration=300,
        glue_effect=0.9,
        glue_negative_weight=1.1
    ),
    PropModel(
        name="精神亢奋",
        duration=400,
        glue_effect=1.1
    ),
    PropModel(
        name="樯橹灰飞烟灭",
        duration=500,
        glue_effect=0.3,
        glue_negative_weight=3
    )
]


def get_event_buff(name: str) -> PropModel:
    """
    通过名称获取指定的Buff。

    Args:
        name (str): Buff的名称

    Returns:
        PropModel: 如果找到匹配的Buff，返回该实例
    """
    buff = next((buff for buff in EVENT_BUFF_MAP if buff.name == name), None)
    if buff is None:
        raise ValueError("不存在该事件")
    return buff


def is_prop_in_list(prop_name: str) -> bool:
    """
    判断一个道具是否在道具列表中。

    Args:
        prop_name (str): 道具的名称

    Returns:
        bool: 如果道具在列表中，返回 True；否则返回 False
    """
    return any(prop.name == prop_name for prop in GOODS)


def get_prop_by_name(prop_name: str) -> PropModel | None:
    """
    通过名称获取指定的道具。

    Args:
        prop_name (str): 道具的名称

    Returns:
        PropModel | None: 如果找到匹配的道具，返回该道具实例；否则返回 None
    """
    return next((prop for prop in GOODS if prop.name == prop_name), None)
