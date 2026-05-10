from typing import Annotated

import stripe
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth.schema import AuthSchema
from app.api.payment.schema import (
    CreateCheckoutSessionOutSchema,
    CreateCheckoutSessionSchema,
    OrderOutSchema,
)
from app.api.payment.service import PaymentService
from app.common.response import ResponseSchema, SuccessResponse
from app.config.setting import settings
from app.core.dependencies import db_getter, get_current_user
from app.core.logger import log

PaymentRouter = APIRouter(prefix="/payment", tags=["支付"])


@PaymentRouter.post(
    "/create-checkout",
    summary="创建支付会话",
    description="创建支付会话",
    response_model=ResponseSchema[CreateCheckoutSessionOutSchema],
)
async def create_checkout_session_controller(
    data: CreateCheckoutSessionSchema, auth: Annotated[AuthSchema, Depends(get_current_user)]
) -> dict:
    result = await PaymentService.create_checkout_session_service(auth, data)
    log.info(f"创建支付会话 {result['session_id']} 成功")
    return SuccessResponse(data=result)


@PaymentRouter.post(
    "/webhook",
    summary="Stripe Webhook 回调处理",
    description="Stripe Webhook 回调处理",
)
async def stripe_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> dict:
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    if not webhook_secret:
        return JSONResponse(status_code=400, content={"error": "Webhook secret not configured"})

    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "Invalid payload"})
    except stripe.SignatureVerificationError:
        return JSONResponse(status_code=400, content={"error": "Invalid signature"})

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        if session["payment_status"] == "paid":
            payment_intent_id = session["payment_intent"] or ""
            result = await PaymentService.complete_order_service(
                session["id"], payment_intent_id, db
            )
            if result:
                log.info(f"[Payment] Order {result['order_no']} completed successfully")
            else:
                log.info(f"[Payment] Session {session['id']} already processed or not found")

    elif event["type"] == "checkout.session.async_payment_succeeded":
        session = event["data"]["object"]
        payment_intent_id = session["payment_intent"] or ""
        await PaymentService.complete_order_service(session["id"], payment_intent_id, db)

    return JSONResponse(status_code=200, content={"received": True})


@PaymentRouter.get(
    "/orders",
    summary="获取订单列表",
    description="获取订单列表",
    response_model=ResponseSchema[list[OrderOutSchema]],
)
async def list_orders_controller(auth: Annotated[AuthSchema, Depends(get_current_user)]) -> dict:
    result_dict = await PaymentService.get_order_list_service(auth)
    return SuccessResponse(data=result_dict)
