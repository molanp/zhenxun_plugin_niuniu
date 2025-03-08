import shutil

import aiosqlite

from zhenxun.configs.path_config import DATA_PATH
from zhenxun.services.log import logger

from .model import NiuNiuRecord, NiuNiuUser


class Sqlite:
    @classmethod
    async def sqlite2db(cls) -> None:
        cls.conn = await aiosqlite.connect(DATA_PATH / "niuniu" / "data.db")
        await NiuNiuUser.migrate_from_sqlite()
        await NiuNiuRecord.migrate_from_sqlite()
        await Sqlite.conn.close()
        logger.info("Sqlite数据库迁移完成", "niuniu")
        shutil.rmtree(DATA_PATH / "niuniu")

    @classmethod
    async def json2db(cls, file_data):
        """迁移JSON数据到ORM"""
        from tortoise.transactions import in_transaction

        async with in_transaction():
            await NiuNiuUser.all().delete()
            users = [
                NiuNiuUser(
                    uid=str(user_id),
                    length=user_length,
                    sex="boy" if user_length > 0 else "girl",
                )
                for group in file_data
                for user_id, user_length in group.items()
            ]
            await NiuNiuUser.bulk_create(users)
        logger.info("JSON数据迁移完成", "niuniu")

    @classmethod
    async def query(
        cls,
        table: str,
        columns: list | None = None,
        conditions: dict | None = None,
        order_by: str | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        """
        根据条件查询数据。

        :param table: 要查询的表名。
        :param columns: 要查询的列名列表，如果不指定则查询所有列。
        :param conditions: 查询条件，字典格式，键为字段名，值为条件值。
        :param order_by: 排序条件，例如 "time DESC"。
        :param limit: 限制结果数量。
        :return: 查询结果的字典列表。
        """
        columns_str = ", ".join(columns) if columns else "*"
        query = f"SELECT {columns_str} FROM {table}"

        if conditions:
            query += " WHERE " + " AND ".join(
                [f"{key} = ?" for key in conditions.keys()]
            )

        if order_by:
            query += f" ORDER BY {order_by}"

        if limit is not None:
            query += f" LIMIT {limit}"

        async with cls.conn.cursor() as cursor:
            await cursor.execute(
                query, tuple(conditions.values()) if conditions else ()
            )
            result = await cursor.fetchall()
            if not result:
                return []
            column_names = [description[0] for description in cursor.description]
            return [dict(zip(column_names, row)) for row in result]
