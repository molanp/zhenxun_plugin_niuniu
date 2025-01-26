from nonebot.plugin import PluginMetadata

from zhenxun.configs.utils import PluginExtraData

from .handler import (
    niuniu_deep_rank,  # noqa: F401
    niuniu_delete,  # noqa: F401
    niuniu_fencing,  # noqa: F401
    niuniu_hit_glue,  # noqa: F401
    niuniu_length_rank,  # noqa: F401
    niuniu_my,  # noqa: F401
    niuniu_register,  # noqa: F401
)

__plugin_meta__ = PluginMetadata(
    name="牛牛大作战",
    description="牛牛大作战，男同快乐游",
    usage="""
    牛牛大作战，男同快乐游
    合理安排时间，享受健康生活

    注册牛牛 --注册你的牛牛
    注销牛牛 --销毁你的牛牛(花费10金币)
    jj [@user] --与注册牛牛的人进行击剑，对战结果影响牛牛长度
    我的牛牛 --查看自己牛牛长度
    牛牛长度排行 --查看本群正数牛牛长度排行
    牛牛深度排行 --查看本群负数牛牛深度排行
    打胶 --对自己的牛牛进行操作，结果随机
    """.strip(),
    extra=PluginExtraData(
        author="molanp",
        menu_type="群内小游戏",
    ).dict(),
)
