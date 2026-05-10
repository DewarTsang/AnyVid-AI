from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth.crud import UserCRUD
from app.api.auth.schema import (
    AuthSchema,
    LoginOutSchema,
    LoginSchema,
    UserOutSchema,
    UserRegisterSchema,
)
from app.core.security import create_access_token
from app.utils.hash_bcrpy_util import PwdUtil


class UserService:
    @classmethod
    async def register_user_service(cls, auth: AuthSchema, data: UserRegisterSchema) -> dict:
        email_ok = await UserCRUD(auth).get_by_email_crud(email=data.email)
        if email_ok:
            raise HTTPException(detail="该邮箱已注册", status_code=400)

        password_hash = PwdUtil.set_password_hash(password=data.password)
        create_dict = data.model_dump(exclude_unset=True, exclude={"password"})
        create_dict["password_hash"] = password_hash

        result = await UserCRUD(auth).create(data=create_dict)
        return UserOutSchema.model_validate(result).model_dump()

    @classmethod
    async def get_current_user_info_service(cls, auth: AuthSchema) -> dict:
        # 获取用户基本信息
        if not auth.user or not auth.user.id:
            raise HTTPException(detail="用户不存在", status_code=400)
        user = await UserCRUD(auth).get_by_id_crud(id=auth.user.id)
        user_dict = UserOutSchema.model_validate(user).model_dump()
        return user_dict


class LoginService:
    @classmethod
    async def authenticate_user_service(cls, data: LoginSchema, db: AsyncSession) -> dict:
        auth = AuthSchema(db=db)
        user = await UserCRUD(auth).get_by_email_crud(email=data.email)
        if not user:
            raise HTTPException(detail="邮箱或密码错误", status_code=400)

        if not PwdUtil.verify_password(
            plain_password=data.password, password_hash=user.password_hash
        ):
            raise HTTPException(detail="邮箱或密码错误", status_code=400)

        token = create_access_token(user=user)
        return LoginOutSchema(
            token=token, user=UserOutSchema.model_validate(user).model_dump()
        ).model_dump()
