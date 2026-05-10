from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth.schema import (
    AuthSchema,
    LoginOutSchema,
    LoginSchema,
    UserOutSchema,
    UserRegisterSchema,
)
from app.api.auth.service import LoginService, UserService
from app.common.response import ResponseSchema, SuccessResponse
from app.core.dependencies import db_getter, get_current_user
from app.core.logger import log

AuthRouter = APIRouter(prefix="/auth", tags=["认证"])


@AuthRouter.post(
    "/register",
    summary="注册用户",
    description="注册用户",
    response_model=ResponseSchema[UserOutSchema],
)
async def register_user_controller(
    data: UserRegisterSchema,
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    auth = AuthSchema(db=db)
    user_register_result = await UserService.register_user_service(data=data, auth=auth)
    log.info(f"{data.email} 注册用户成功: {user_register_result}")
    return SuccessResponse(data=user_register_result)


@AuthRouter.post(
    "/login",
    summary="用户登录",
    description="用户登录",
    response_model=ResponseSchema[LoginOutSchema],
)
async def login_for_access_token_controller(
    data: LoginSchema,
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse | dict:
    login_reusult = await LoginService.authenticate_user_service(data=data, db=db)
    log.info(f"{data.email} 登录成功: {login_reusult}")
    return SuccessResponse(data=login_reusult)


@AuthRouter.get(
    "/me",
    summary="获取当前用户信息",
    description="获取当前用户信息",
    response_model=ResponseSchema[UserOutSchema],
)
async def get_current_user_controller(
    auth: Annotated[AuthSchema, Depends(get_current_user)],
) -> JSONResponse:
    result_dict = await UserService.get_current_user_info_service(auth=auth)
    log.info(f"获取当前用户信息成功: {result_dict}")
    return SuccessResponse(data=result_dict)
