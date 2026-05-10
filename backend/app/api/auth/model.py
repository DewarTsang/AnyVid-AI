from datetime import UTC, date, datetime

from sqlalchemy import Boolean, Date, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin


class UserModel(ModelMixin):
    __tablename__: str = "sys_user"
    __table_args__: dict[str, str] = {"comment": "用户表"}

    email: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True, comment="邮箱", index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码哈希")
    is_vip: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否VIP")
    vip_expire_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="VIP过期时间"
    )
    daily_summary_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="每日总结次数"
    )
    last_summary_date: Mapped[date | None] = mapped_column(
        Date, nullable=True, comment="最后总结日期"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        comment="创建时间",
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
        comment="更新时间",
        index=True,
    )
