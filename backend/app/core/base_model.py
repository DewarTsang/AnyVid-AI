from sqlalchemy import Integer
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class MappedBase(AsyncAttrs, DeclarativeBase):
    __abstract__: bool = True


class ModelMixin(MappedBase):
    __abstract__: bool = True

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="主键ID",
        index=True,
    )
