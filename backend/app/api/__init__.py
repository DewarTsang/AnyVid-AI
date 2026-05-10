from fastapi import APIRouter

from app.api.auth.controller import AuthRouter
from app.api.common.controller import CommonRouter
from app.api.payment.controller import PaymentRouter
from app.api.summarize.controller import SummarizeRouter

router = APIRouter(prefix="")

router.include_router(AuthRouter)
router.include_router(PaymentRouter)
router.include_router(SummarizeRouter)
router.include_router(CommonRouter)
