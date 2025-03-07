from datetime import datetime
import os
from pathlib import Path

import aiosqlite

from zhenxun.configs.path_config import DATA_PATH
from zhenxun.services.log import logger


class Sqlite:
    DATABASE_PATH = DATA_PATH / "niuniu" / "data.db"

    @classmethod
    async def init(cls) -> None:
        os.makedirs(DATA_PATH / "niuniu", exist_ok=True)
        old_db_path = Path(__file__).resolve().parent / "data" / "data.db"

        if old_db_path.exists():
            os.replace(old_db_path, cls.DATABASE_PATH)
            os.remove(Path(__file__).resolve().parent / "data")
            logger.info("迁移数据库成功", "niuniu")

        cls.conn = await aiosqlite.connect(cls.DATABASE_PATH)
        await cls.exec("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uid INTEGER NOT NULL,
                    length INTEGER NOT NULL,
                    sex TEXT NOT NULL,
                    time DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
        await cls.exec("""
                CREATE TABLE IF NOT EXISTS records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uid INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    origin_length INTEGER NOT NULL,
                    diff INTEGER NOT NULL,
                    new_length INTEGER NOT NULL,
                    time DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
        await cls.exec("CREATE INDEX IF NOT EXISTS idx_length ON users(length DESC)")

    @classmethod
    async def exec(cls, sql: str, *args) -> list[dict] | None:
        """
        执行自定义 SQL 语句并返回结果。

        :param sql: 要执行的 SQL 语句。
        :param args: SQL 语句中的参数。
        :return: 查询结果的字典列表，如果是非查询语句则返回 None。
        """
        async with cls.conn.cursor() as cursor:
            await cursor.execute(sql, args)
            if "SELECT" in sql.strip().upper():
                results = await cursor.fetchall()
                if not results:
                    return None
                column_names = [description[0] for description in cursor.description]
                return [dict(zip(column_names, row)) for row in results]
            else:
                await cls.conn.commit()
                return None

    @classmethod
    async def json2db(cls, file_data) -> None:
        await cls.exec("DELETE FROM users")
        mixed_data = []
        for groups in file_data:
            mixed_data.extend(
                {
                    "uid": int(user_id),
                    "length": user_length,
                    "sex": "boy" if user_length > 0 else "girl",
                }
                for user_id, user_length in groups.items()
            )
        for i in mixed_data:
            if not await cls.insert("users", i, {"uid": i["uid"]}):
                await cls.update("users", i, {"uid": i["uid"]})

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

    @classmethod
    async def insert(
        cls, table: str, data: dict, conditions: dict | None = None
    ) -> bool:
        """
        插入数据到指定表中。如果提供了条件，则先检查是否存在符合条件的记录，如果存在则不插入。

        :param table: 要插入数据的表名。
        :param data: 要插入的数据，字典格式，键为字段名，值为数据值。
        :param conditions: 插入条件，字典格式，键为字段名，值为条件值。
        :return: 插入成功返回 True，否则返回 False。
        """
        data["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if conditions and await cls.query(table, conditions=conditions):
            return False

        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        async with cls.conn.cursor() as cursor:
            await cursor.execute(query, tuple(data.values()))
            await cls.conn.commit()
        return True

    @classmethod
    async def update(cls, table: str, data: dict, conditions: dict) -> bool:
        """
        更新符合条件的数据。

        :param table: 要更新数据的表名。
        :param data: 要更新的数据，字典格式，键为字段名，值为数据值。
        :param conditions: 更新条件，字典格式，键为字段名，值为条件值。
        :return: True
        """
        data["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        set_clause = ", ".join([f"{key} = ?" for key in data])
        where_clause = " AND ".join([f"{key} = ?" for key in conditions])
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        async with cls.conn.cursor() as cursor:
            await cursor.execute(
                query, tuple(list(data.values()) + list(conditions.values()))
            )
            await cls.conn.commit()
        return True

    @classmethod
    async def delete(cls, table: str, conditions: dict) -> bool:
        """
        删除符合条件的数据。

        :param table: 要删除数据的表名。
        :param conditions: 删除条件，字典格式，键为字段名，值为条件值。
        :return: True
        """
        where_clause = " AND ".join([f"{key} = ?" for key in conditions])
        query = f"DELETE FROM {table} WHERE {where_clause}"
        async with cls.conn.cursor() as cursor:
            await cursor.execute(query, tuple(conditions.values()))
            await cls.conn.commit()
        return True

    @classmethod
    async def fix_inf_data(cls):
        await Sqlite.exec("""
            UPDATE users SET 
            length = CASE
                WHEN length = 'inf' THEN 200 * (0.9 + RANDOM()*0.1)
                WHEN length = '-inf' THEN -200 * (0.9 + RANDOM()*0.1)
                ELSE length
            END
        """)
        # 处理数值型异常
        await Sqlite.exec("""
            UPDATE users SET 
            length = ROUND(COALESCE(NULLIF(length, 'NaN'), 10), 2)
            WHERE typeof(length) != 'real'
        """)
