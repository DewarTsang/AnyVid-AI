from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth.crud import UserCRUD
from app.api.auth.schema import AuthSchema
from app.core.database import async_db_session
from app.core.security import decode_access_token

security = HTTPBearer(auto_error=False)


async def db_getter() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话连接

    返回:
    - AsyncSession: 数据库会话连接
    """
    async with async_db_session() as session:
        async with session.begin():
            yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(db_getter),
) -> dict:
    """必须登录"""
    if not credentials:
        raise HTTPException(status_code=401, detail="请先登录")
    payload = decode_access_token(credentials.credentials)

    auth = AuthSchema(db=db)
    user = await UserCRUD(auth).get_by_id_crud(id=payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    auth.user = user
    return auth


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(db_getter),
) -> dict | None:
    """可选登录：已登录返回用户信息，未登录返回 None"""
    auth = AuthSchema(db=db)
    if not credentials:
        return auth
    try:
        payload = decode_access_token(credentials.credentials)
        user = await UserCRUD(auth).get_by_id_crud(id=payload["sub"])
        auth.user = user
        return auth
    except HTTPException:
        return auth
