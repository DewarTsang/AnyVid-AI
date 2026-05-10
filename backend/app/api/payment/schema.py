from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CreateCheckoutSessionSchema(BaseModel):
    plan_type: str = Field(default="monthly", description="套餐类型")


class CreateCheckoutSessionOutSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    checkout_url: str = Field(..., description="会话链接")
    order_no: str = Field(..., description="订单号")
    session_id: str = Field(..., description="会话ID")


class OrderOutSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_no: str = Field(..., description="订单号")
    amount: Decimal = Field(..., description="金额")
    currency: str = Field(..., description="币种")
    status: str = Field(..., description="状态")
    created_at: datetime = Field(..., description="创建时间")
    paid_at: datetime = Field(..., description="支付时间")
