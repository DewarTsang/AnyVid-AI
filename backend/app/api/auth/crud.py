from typing import Any

from app.core.base_crud import CRUDBase

from .model import UserModel
from .schema import AuthSchema, UserCreateSchema, UserUpdateSchema


class UserCRUD(CRUDBase[UserModel, UserCreateSchema, UserUpdateSchema]):
    def __init__(self, auth: AuthSchema) -> None:
        self.auth = auth
        super().__init__(UserModel, auth)

    async def get_by_id_crud(
        self, id: int, preload: list[str | Any] | None = None
    ) -> UserModel | None:
        return await self.get(
            preload=preload,
            id=id,
        )

    async def get_by_email_crud(
        self, email: str, preload: list[str | Any] | None = None
    ) -> UserModel | None:
        return await self.get(
            preload=preload,
            email=email,
        )
