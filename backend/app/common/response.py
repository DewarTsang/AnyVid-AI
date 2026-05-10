from datetime import date, datetime, time
from typing import Any

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.common.constant import DATE_DISPLAY_FMT, DATETIME_DISPLAY_FMT, TIME_DISPLAY_FMT

_JSON_DATETIME_CUSTOM_ENCODER: dict[type[Any], Any] = {
    datetime: lambda d: d.strftime(DATETIME_DISPLAY_FMT),
    date: lambda d: d.strftime(DATE_DISPLAY_FMT),
    time: lambda t: t.strftime(TIME_DISPLAY_FMT),
}


def jsonable_response_content(content: Any) -> Any:
    return jsonable_encoder(content, custom_encoder=_JSON_DATETIME_CUSTOM_ENCODER)


class ResponseSchema[T](BaseModel):
    """响应模型"""

    success: bool = Field(default=True, description="操作是否成功")
    data: T | None = Field(default=None, description="响应数据")


class SuccessResponse(JSONResponse):
    def __init__(
        self,
        success: bool = True,
        data: Any | None = None,
        status_code: int = status.HTTP_200_OK,
    ) -> None:
        content = ResponseSchema(
            success=success,
            data=data,
        ).model_dump()
        super().__init__(content=jsonable_response_content(content), status_code=status_code)


class ErrorResponse(JSONResponse):
    def __init__(
        self,
        success: bool = False,
        data: Any | None = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ) -> None:
        content = ResponseSchema(
            success=success,
            data=data,
        ).model_dump()
        super().__init__(content=jsonable_response_content(content), status_code=status_code)
