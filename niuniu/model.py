from typing import ClassVar

from tortoise import fields
from tortoise.transactions import in_transaction

from zhenxun.services.db_context import Model


class NiuNiuUser(Model):
    id = fields.IntField(pk=True, generated=True, auto_increment=True)
    """自增id"""
    uid = fields.CharField(255, description="用户唯一标识符")
    """用户id"""
    length = fields.FloatField(description="用户长度")
    """用户长度"""
    sex = fields.CharField(255, description="用户性别", default="boy")
    """用户性别"""
    time = fields.DatetimeField(auto_now_add=True)
    """创建时间"""

    class Meta:  # pyright: ignore [reportIncompatibleVariableOverride]
        table = "niuniu_users"
        table_description = "牛牛大作战用户数据表"
        indexes: ClassVar = [("uid", "length")]

    async def save(self, *args, **kwargs) -> None:
        """保存时自动计算性别"""
        self.sex = "girl" if self.length <= 0 else "boy"
        await super().save(*args, **kwargs)

    @classmethod
    async def migrate_from_sqlite(cls):
        """从旧表迁移用户数据"""
        from .database import Sqlite

        async with in_transaction():
            old_data = await Sqlite.query("users")
            for item in old_data:
                await cls.update_or_create(
                    uid=str(item["uid"]),
                    defaults={
                        "length": item["length"],
                        "sex": item["sex"],
                        "time": item["time"],
                    },
                )


class NiuNiuRecord(Model):
    id = fields.IntField(pk=True, generated=True, auto_increment=True)
    """自增id"""
    uid = fields.CharField(255, description="用户唯一标识符")
    """用户id"""
    action = fields.TextField(description="动作名称")
    """动作名称"""
    origin_length = fields.FloatField(description="操作前长度")
    """操作前长度"""
    diff = fields.FloatField(description="长度变化")
    """长度变化"""
    new_length = fields.FloatField(description="操作后长度")
    """操作后长度"""
    time = fields.DatetimeField(auto_now_add=True)
    """创建时间"""

    class Meta:  # pyright: ignore [reportIncompatibleVariableOverride]
        table = "niuniu_record"
        table_description = "牛牛大作战日志表"
        indexes: ClassVar = [("uid", "action")]

    async def save(self, *args, **kwargs) -> None:
        """保存时自动计算长度差值"""
        if self.new_length is not None and self.origin_length is not None:
            self.diff = round(self.new_length - self.origin_length, 2)
        await super().save(*args, **kwargs)

    @classmethod
    async def migrate_from_sqlite(cls):
        """从旧表迁移记录数据"""
        from .database import Sqlite

        async with in_transaction():
            old_data = await Sqlite.query("records")
            for item in old_data:
                await cls.create(
                    uid=str(item["uid"]),
                    action=item["action"],
                    origin_length=item["origin_length"],
                    new_length=item["new_length"],
                    time=item["time"],
                )
