import uuid
from datetime import UTC, datetime

import stripe
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth.crud import UserCRUD
from app.api.auth.model import UserModel
from app.api.auth.schema import AuthSchema
from app.api.order.crud import OrderCRUD
from app.api.payment.schema import (
    CreateCheckoutSessionOutSchema,
    CreateCheckoutSessionSchema,
    OrderOutSchema,
)
from app.common.enums import PLANS
from app.config.setting import settings


class PaymentService:
    @classmethod
    async def create_checkout_session_service(
        cls, auth: AuthSchema, data: CreateCheckoutSessionSchema
    ) -> dict:
        secret_key = settings.STRIPE_SECRET_KEY
        price_id = settings.STRIPE_PRICE_ID_MONTHLY
        frontend_url = settings.FRONTEND_URL

        if not secret_key:
            raise HTTPException(status_code=500, detail="支付服务未配置，请设置 STRIPE_SECRET_KEY")
        if not price_id:
            raise HTTPException(
                status_code=500, detail="套餐价格未配置，请设置 STRIPE_PRICE_ID_MONTHLY"
            )

        plan = PLANS.get(data.plan_type)
        if not plan:
            raise HTTPException(status_code=400, detail="无效的套餐类型")

        stripe.api_key = secret_key

        user: UserModel = auth.user

        order_no = cls._generate_order_no(user.id)
        create_dict = {
            "user_id": user.id,
            "order_no": order_no,
            "amount": plan["amount"],
            "currency": plan["currency"],
            "plan_type": data.plan_type,
        }
        await OrderCRUD(auth).create(data=create_dict)

        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price": price_id,
                        "quantity": 1,
                    }
                ],
                mode="payment",
                success_url=f"{frontend_url}?payment=success&order_no={order_no}",
                cancel_url=f"{frontend_url}?payment=cancel&order_no={order_no}",
                client_reference_id=str(user.id),
                customer_email=user.email,
                metadata={
                    "order_no": order_no,
                    "user_id": str(user.id),
                    "plan_type": data.plan_type,
                },
            )

            await OrderCRUD(auth).update_order_stripe_session(order_no, session.id)

            return CreateCheckoutSessionOutSchema(
                checkout_url=session.url, order_no=order_no, session_id=session.id
            ).model_dump()

        except stripe.StripeError as e:
            raise HTTPException(status_code=400, detail=f"创建支付会话失败: {str(e)}")

    @staticmethod
    def _generate_order_no(user_id: int) -> str:
        ts = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        short_uuid = uuid.uuid4().hex[:8]
        return f"SA{ts}{user_id:04d}{short_uuid}"

    @classmethod
    async def complete_order_service(
        cls, session_id: str, payment_intent_id: str, db: AsyncSession
    ) -> dict:
        auth = AuthSchema(db=db)
        order = await OrderCRUD(auth).get(stripe_session_id=session_id, status="pending")

        if not order:
            return None

        now = datetime.now(UTC)

        user = await UserCRUD(auth).get(id=order.user_id)

        current_expire = None
        if user.vip_expire_at:
            try:
                current_expire = datetime.fromisoformat(user.vip_expire_at)
            except ValueError:
                pass

        base_time = datetime.now(UTC)
        if current_expire and current_expire > base_time:
            base_time = current_expire

        from dateutil.relativedelta import relativedelta

        if order.plan_type == "monthly":
            new_expire = base_time + relativedelta(months=1)
        elif order.plan_type == "yearly":
            new_expire = base_time + relativedelta(years=1)
        else:
            new_expire = base_time + relativedelta(months=1)

        await OrderCRUD(auth).update(
            id=order.id,
            data={"status": "paid", "stripe_payment_intent_id": payment_intent_id, "paid_at": now},
        )
        await UserCRUD(auth).update(
            id=order.user_id, data={"is_vip": 1, "vip_expire_at": new_expire}
        )

        return OrderOutSchema.model_validate(order).model_dump()

    @classmethod
    async def get_order_list_service(cls, auth: AuthSchema) -> list[dict]:
        order_list = await OrderCRUD(auth).list(
            user_id=auth.user.id, order_by=[{"created_at": "desc"}]
        )
        order_dict_list = []
        for order in order_list:
            order_dict = OrderOutSchema.model_validate(order).model_dump()
            order_dict_list.append(order_dict)

        return order_dict_list
