from collections.abc import AsyncIterable
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.sse import EventSourceResponse, ServerSentEvent

from app.api.auth.schema import AuthSchema
from app.api.summarize.schema import ChatInSchema, SummarizeInSchema
from app.api.summarize.service import SummarizeService
from app.core.dependencies import get_optional_user

SummarizeRouter = APIRouter(prefix="", tags=["AI 总结"])


@SummarizeRouter.post(
    "/summarize",
    summary="AI 视频总结",
    description="AI 视频总结",
    response_class=EventSourceResponse,
)
async def summarize_video_controller(
    data: SummarizeInSchema, auth: Annotated[AuthSchema, Depends(get_optional_user)]
) -> AsyncIterable[ServerSentEvent]:
    async for item in SummarizeService.summarize_video_service(data, auth):
        yield ServerSentEvent(
            event=item.event,
            raw_data=item.raw_data,
        )


@SummarizeRouter.post(
    "/chat", summary="AI 视频问答", description="AI 视频问答", response_class=EventSourceResponse
)
async def chat_with_video_controller(
    data: ChatInSchema, auth: Annotated[AuthSchema, Depends(get_optional_user)]
) -> AsyncIterable[ServerSentEvent]:
    async for item in SummarizeService.chat_with_video_service(data, auth):
        yield ServerSentEvent(
            event=item.event,
            raw_data=item.raw_data,
        )
