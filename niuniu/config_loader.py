from pathlib import Path

from pydantic import BaseModel
import yaml


class Buff(BaseModel):
    """
    Buff 模型，用于存储 Buff 的持续时间和效果系数。

    Attributes:
        duration (int): Buff 持续时间（秒）
        effect (float): 长度变化系数（>1 增加, <1 减少）
    """

    duration: int = 0
    """Buff 持续时间（秒）"""
    effect: float = 1
    """长度变化系数(>1增加, <1减少)"""


class RapidEffect(BaseModel):
    """
    连续打胶效果模型，用于存储连续打胶事件的描述文本、系数和禁用时间。

    Attributes:
        positive_descriptions (list[str]): 事件增加文本
        no_change_descriptions (list[str] | None): 事件不变文本
        negative_descriptions (list[str] | None): 事件减少文本
        coefficient (float): 系数
        effect (float): 效果系数
        ban_time (int): 禁用时间（秒）
    """

    positive_descriptions: list[str]
    """事件增加文本"""
    no_change_descriptions: list[str] | None = None
    """事件不变文本"""
    negative_descriptions: list[str] | None = None
    """事件减少文本"""
    coefficient: float = 1
    """增加比例系数"""
    effect: float = 1
    """效果系数"""
    ban_time: int = 0
    """小黑屋时间"""


class GlueEvent(BaseModel):
    """
    打胶事件模型，用于存储打胶事件的详细配置。

    Attributes:
        weight (int): 事件权重
        positive_descriptions (list[str]): 事件增加文本
        no_change_descriptions (list[str] | None): 事件不变文本
        negative_descriptions (list[str] | None): 事件减少文本
        coefficient (float): 系数
        effect (float): 效果系数
        ban_time (int): 禁用时间（秒）
        category (str): 事件类型
        buff (Buff | None): Buff 效果
        next_event (str | None): 连续子事件
        rapid_effect (RapidEffect | None): 连续打胶效果
        affected_by_props (bool): 是否受到道具影响
    """

    weight: float
    """事件权重"""
    positive_descriptions: list[str]
    """事件增加文本"""
    no_change_descriptions: list[str] | None = None
    """事件不变文本"""
    negative_descriptions: list[str] | None = None
    """事件减少文本"""
    coefficient: float = 1
    """增加比例系数"""
    effect: float = 1
    """效果系数"""
    ban_time: int = 0
    """小黑屋时间"""
    category: str
    """事件类型"""
    buff: Buff | None = None
    """Buff"""
    next_event: str | None = None
    """连续子事件"""
    rapid_effect: RapidEffect | None = None
    """连续打胶效果"""
    affected_by_props: bool = True
    """是否受到道具影响"""


class PropModel(BaseModel):
    """
    道具模型，用于存储道具的持续时间、击剑胜率倍数、打胶效果倍数和打胶触发负面事件的概率倍数。

    Attributes:
        name (str): 道具的名称
        des (str): 道具的简介
        price (int): 道具的价格
        icon (str): 道具的图标
        duration (int): Buff 持续时间（秒）
        fencing_weight (float): 击剑胜率的倍数
        glue_effect (float): 打胶效果的倍数
        glue_negative_weight (float): 打胶触发负面事件的倍数
    """
    name: str
    """道具的名称"""
    des: str = ""
    """道具的简介"""
    price: int
    """道具的价格"""
    icon: str = ""
    """道具的图标"""
    duration: int = 0
    """Buff 持续时间（秒）"""
    fencing_weight: float = 1
    """击剑胜率的倍数"""
    glue_effect: float = 1
    """打胶效果的倍数"""
    glue_negative_weight: float = 1
    """打胶触发负面事件的倍数"""


def load_events() -> dict[str, GlueEvent]:
    """
    加载事件配置文件，返回一个包含打胶事件的字典。

    Returns:
        dict[str, GlueEvent]: 包含打胶事件的字典，键为事件名称，值为 GlueEvent 实例
    """
    config_path = Path(__file__).parent / "events.yaml"
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return {key: GlueEvent(**value) for key, value in config["glue_events"].items()}
