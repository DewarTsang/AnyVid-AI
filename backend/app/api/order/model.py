from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin


class OrderModel(ModelMixin):
    __tablename__: str = "sys_order"
    __table_args__: dict[str, str] = {"comment": "订单表"}

    order_no: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, comment="订单号", index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sys_user.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID",
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="金额",
    )
    currency: Mapped[str] = mapped_column(String(64), default="cny", nullable=False, comment="货币")
    status: Mapped[str] = mapped_column(
        String(64),
        default="pending",
        nullable=False,
        comment="状态",
    )
    plan_type: Mapped[str] = mapped_column(
        String(64), default="monthly", nullable=False, comment="套餐类型"
    )
    stripe_session_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True, index=True, comment="Stripe Session ID"
    )
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Stripe Payment Intent ID"
    )
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, index=True, comment="支付时间"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(),
        nullable=False,
        comment="创建时间",
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(),
        onupdate=lambda: datetime.now(),
        nullable=False,
        comment="更新时间",
        index=True,
    )
