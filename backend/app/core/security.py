from datetime import UTC, datetime, timedelta

import jwt
from fastapi import HTTPException

from app.api.auth.model import UserModel
from app.config.setting import settings


def create_access_token(user: UserModel) -> str:
    payload_dict = {
        "sub": str(user.id),
        "email": user.email,
        "exp": datetime.now(UTC) + timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.now(UTC),
    }
    return jwt.encode(
        payload=payload_dict,
        key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    if not token:
        raise HTTPException(detail="认证不存在,请重新登录", status_code=401)

    try:
        payload = jwt.decode(jwt=token, key=settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        online_user_info = payload.get("sub")
        if not online_user_info:
            raise HTTPException(detail="无效认证,请重新登录", status_code=401)

        return payload

    except (jwt.InvalidSignatureError, jwt.DecodeError):
        raise HTTPException(detail="无效认证,请重新登录", status_code=401)

    except jwt.ExpiredSignatureError:
        raise HTTPException(detail="认证已过期,请重新登录", status_code=401)

    except jwt.InvalidTokenError:
        raise HTTPException(detail="token已失效,请重新登录", status_code=401)
