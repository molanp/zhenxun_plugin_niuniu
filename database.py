from datetime import datetime

import aiosqlite
import ujson


class Sqlite:
    @classmethod
    async def init(cls):
        cls.conn = await aiosqlite.connect("data.db")
        await cls._init_table()
        return cls

    @classmethod
    async def _init_table(cls):
        async with cls.conn.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uid TEXT NOT NULL,
                    length INTEGER NOT NULL,
                    sex TEXT NOT NULL,
                    time TEXT NOT NULL
                )
            """)
            await cls.conn.commit()

    @classmethod
    async def json2db(cls, file_data):
        async with cls.conn.cursor() as cursor:
            await cursor.execute("DELETE FROM users")
            await cls.conn.commit()
        mixed_data  = []
        for users in file_data:
            mixed_data.extend(
                {
                    "uid": user_id,
                    "length": user_length,  # 默认长度为 0
                    "sex": "boy" if user_id > 0 else "girl",
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                for user_id, user_length in users.items()
            )

    @classmethod
    async def query(cls, table, columns=None, conditions=None, fetch_one=True):
        """
        根据条件查询数据。

        :param table: 要查询的表名。
        :param columns: 要查询的列名列表，如果不指定则查询所有列。
        :param conditions: 查询条件，字典格式，键为字段名，值为条件值。
        :param fetch_one: 是否只获取单条记录，默认为 True。
        :return: 查询结果的 JSON 格式。
        """
        columns_str = ", ".join(columns) if columns else "*"
        query = f"SELECT {columns_str} FROM {table}"
        if conditions:
            query += " WHERE " + " AND ".join(
                [f"{key} = ?" for key in conditions.keys()]
            )

        async with cls.conn.cursor() as cursor:
            await cursor.execute(
                query, tuple(conditions.values()) if conditions else ()
            )
            result = await cursor.fetchone() if fetch_one else await cursor.fetchall()
            if not result:
                return (
                    ujson.dumps({}, ensure_ascii=False)
                    if fetch_one
                    else ujson.dumps([], ensure_ascii=False)
                )
            column_names = [description[0] for description in cursor.description]
            json_result = (
                dict(zip(column_names, result))
                if fetch_one
                else [dict(zip(column_names, row)) for row in result]
            )
            return ujson.dumps(json_result, ensure_ascii=False)

    @classmethod
    async def insert(cls, table, data, conditions=None):
        """
        插入数据到指定表中。如果提供了条件，则先检查是否存在符合条件的记录，如果存在则不插入。

        :param table: 要插入数据的表名。
        :param data: 要插入的数据，字典格式，键为字段名，值为数据值。
        :param conditions: 插入条件，字典格式，键为字段名，值为条件值。
        :return: 插入成功返回 True，否则返回 False。
        """
        data["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if conditions and await cls.query(table, conditions=conditions, fetch_one=True):
            return False

        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        async with cls.conn.cursor() as cursor:
            await cursor.execute(query, tuple(data.values()))
            await cls.conn.commit()
        return True

    @classmethod
    async def update(cls, table, data, conditions):
        """
        更新符合条件的数据。

        :param table: 要更新数据的表名。
        :param data: 要更新的数据，字典格式，键为字段名，值为数据值。
        :param conditions: 更新条件，字典格式，键为字段名，值为条件值。
        :return: 更新成功的消息。
        """
        set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
        where_clause = " AND ".join([f"{key} = ?" for key in conditions.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        async with cls.conn.cursor() as cursor:
            await cursor.execute(
                query, tuple(list(data.values()) + list(conditions.values()))
            )
            await cls.conn.commit()
        return "Record updated"

    @classmethod
    async def delete(cls, table, conditions):
        """
        删除符合条件的数据。

        :param table: 要删除数据的表名。
        :param conditions: 删除条件，字典格式，键为字段名，值为条件值。
        :return: 删除成功的消息。
        """
        where_clause = " AND ".join([f"{key} = ?" for key in conditions.keys()])
        query = f"DELETE FROM {table} WHERE {where_clause}"
        async with cls.conn.cursor() as cursor:
            await cursor.execute(query, tuple(conditions.values()))
            await cls.conn.commit()
        return "Record deleted"
