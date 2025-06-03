from pathlib import Path

from nonebot.plugin import PluginMetadata

from zhenxun.configs.path_config import IMAGE_PATH
from zhenxun.configs.utils import PluginExtraData
from zhenxun.services.log import logger
from zhenxun.services.plugin_init import PluginInit

from .config import ICON_PATH
from .handler import (
    niuniu_deep_rank,  # noqa: F401
    niuniu_deep_rank_all,  # noqa: F401
    niuniu_fencing,  # noqa: F401
    niuniu_hit_glue,  # noqa: F401
    niuniu_length_rank,  # noqa: F401
    niuniu_length_rank_all,  # noqa: F401
    niuniu_my,  # noqa: F401
    niuniu_my_record,  # noqa: F401
    niuniu_register,  # noqa: F401
    niuniu_unsubscribe,  # noqa: F401
)
from .shop import *  # noqa: F403

__plugin_meta__ = PluginMetadata(
    name="牛牛大作战",
    description="牛牛大作战，男同快乐游",
    usage="""
    牛牛大作战，男同快乐游
    合理安排时间，享受健康生活

    注册牛牛 --注册你的牛牛
    注销牛牛 --销毁你的牛牛(花费500金币)
    击剑/jj [@user] --与注册牛牛的人进行击剑，对战结果影响牛牛长度
    我的牛牛 --查看自己牛牛长度
    我的牛牛战绩 --查看自己牛牛战绩
    牛牛长度排行 --查看本群正数牛牛长度排行
    牛牛深度排行 --查看本群负数牛牛深度排行
    牛牛长度总排行 --查看正数牛牛长度排行总榜
    牛牛深度总排行 --查看负数牛牛深度排行总榜
    打胶 --对自己的牛牛进行操作，结果随机
    """.strip(),
    extra=PluginExtraData(
        author="molanp",
        version="1.2.rc2",
        menu_type="群内小游戏",
    ).dict(),
)


RESOURCE_FILES = [
    IMAGE_PATH / "shop_icon" / "weige.png",
    IMAGE_PATH / "shop_icon" / "meiboli.png",
    IMAGE_PATH / "shop_icon" / "menghanyao.png",
    IMAGE_PATH / "shop_icon" / "yuban.png",
]

GOOD_FILES = [
    ICON_PATH / "weige.png",
    ICON_PATH / "meiboli.png",
    ICON_PATH / "menghanyao.png",
    ICON_PATH / "yuban.png"
]


class MyPluginInit(PluginInit):
    async def install(self):
        for res_file in RESOURCE_FILES + GOOD_FILES:
            res = Path(__file__).parent / res_file.name
            if res.exists():
                if res_file.exists():
                    res_file.unlink()
                res.rename(res_file)
                logger.info(f"更新 NIUNIU 资源文件成功 {res} -> {res_file}")

    async def remove(self):
        for res_file in RESOURCE_FILES + GOOD_FILES:
            if res_file.exists():
                res_file.unlink()
                logger.info(f"删除 NIUNIU 资源文件成功 {res_file}")
