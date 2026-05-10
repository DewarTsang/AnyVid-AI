from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from .model import UserModel


class AuthSchema(BaseModel):
    model_config: ConfigDict = ConfigDict(arbitrary_types_allowed=True)

    user: UserModel | None = Field(default=None, description="用户信息")
    db: AsyncSession = Field(description="数据库会话")


class UserCreateSchema(BaseModel):
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., description="密码")


class UserUpdateSchema(BaseModel):
    pass


class UserOutSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="用户ID")
    email: EmailStr = Field(..., description="邮箱")
    is_vip: bool = Field(default=False, description="是否VIP")
    vip_expire_at: datetime | None = Field(default=None, description="VIP过期时间")


class UserRegisterSchema(BaseModel):
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., description="密码")


class LoginSchema(BaseModel):
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., description="密码")


class LoginOutSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    token: str = Field(..., description="JWT访问令牌")
    user: UserOutSchema = Field(..., description="用户信息")
