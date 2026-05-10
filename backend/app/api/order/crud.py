from fastapi import HTTPException

from app.api.auth.schema import AuthSchema
from app.api.order.model import OrderModel
from app.api.order.schema import OrderCreateSchema, OrderUpdateSchema
from app.core.base_crud import CRUDBase


class OrderCRUD(CRUDBase[OrderModel, OrderCreateSchema, OrderUpdateSchema]):
    def __init__(self, auth: AuthSchema):
        self.auth = auth
        super().__init__(OrderModel, auth)

    async def update_order_stripe_session(
        self, order_no: str, session_id: str
    ) -> OrderModel | None:
        order = await self.get(order_no=order_no)
        if not order:
            raise HTTPException(detail="订单不存在", status_code=400)
        return await self.update(id=order.id, data={"stripe_session_id": session_id})
