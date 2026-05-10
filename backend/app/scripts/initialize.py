import asyncio
import json
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.path_conf import SCRIPT_DIR
from app.core.database import async_db_session, create_tables
from app.core.logger import log


class InitializeData:
    def __init__(self) -> None:
        self.prepare_init_models = []

    async def __init_create_table(self) -> None:
        try:
            await create_tables()
        except asyncio.exceptions.TimeoutError:
            log.error("❌️ 数据库表结构初始化超时")
            raise
        except Exception as e:
            log.error(f"❌️ 数据库表结构初始化失败: {e!s}")
            raise

    async def __init_data(self, db: AsyncSession) -> None:
        for model in self.prepare_init_models:
            table_name = model.__tablename__

            count_result = await db.execute(select(func.count()).select_from(model))
            existing_count = count_result.scalar()
            if existing_count and existing_count > 0:
                log.warning(
                    f"⚠️  跳过 {table_name} 表数据初始化（表已存在 {existing_count} 条记录）"
                )
                continue

            data = await self.__get_data(table_name)
            if not data:
                log.warning(f"⚠️  跳过 {table_name} 表，无初始化数据")
                continue

            try:
                objs = [model(**item) for item in data]

                db.add_all(objs)
                await db.flush()
                log.info(f"✅️ 已向 {table_name} 表写入初始化数据")

            except Exception as e:
                log.error(f"❌️ 初始化 {table_name} 表数据失败: {e!s}")
                raise

    def __create_objects_with_children(self, data: list[dict], model_class: type) -> list:
        def create_object(obj_data: dict) -> Any:
            children_data = obj_data.pop("children", [])

            obj = model_class(**obj_data)

            if children_data:
                obj.children = [create_object(child) for child in children_data]

            return obj

        objs = [create_object(item) for item in data]

        return objs

    async def __get_data(self, filename: str) -> list[dict]:
        json_path = SCRIPT_DIR / f"{filename}.json"
        if not json_path.exists():
            return []

        try:
            with open(json_path, encoding="utf-8") as f:
                return json.loads(f.read())
        except json.JSONDecodeError as e:
            log.error(f"❌️ 解析 {json_path} 失败: {e!s}")
            raise
        except Exception as e:
            log.error(f"❌️ 读取 {json_path} 失败: {e!s}")
            raise

    async def init_db(self) -> None:
        await self.__init_create_table()

        async with async_db_session() as session:
            async with session.begin():
                await self.__init_data(session)
