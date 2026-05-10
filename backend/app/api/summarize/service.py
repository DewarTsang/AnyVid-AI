import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth.crud import UserCRUD
from app.api.auth.schema import AuthSchema
from app.api.summarize.schema import ChatInSchema, SummarizeInSchema

FREE_DAILY_SUMMARY_LIMIT = 3


@dataclass
class SSEMessage:
    event: str
    raw_data: str


class SummarizeService:
    _extractor = None
    _summarizer = None

    @classmethod
    async def _check_summary_permission(cls, auth: AuthSchema) -> tuple[bool, int, str]:
        user = auth.user
        if not user:
            return False, 0, "请先登录后使用 AI 总结功能"

        allowed, remaining = await cls.check_and_increment_summary(user.id, auth.db)
        if not allowed:
            return (
                False,
                0,
                f"今日免费 AI 总结次数已用完（每日 {FREE_DAILY_SUMMARY_LIMIT} 次），开通 VIP 可无限使用",
            )

        return True, remaining, None

    @classmethod
    async def check_and_increment_summary(cls, user_id: int, db: AsyncSession) -> tuple[bool, int]:
        today = datetime.now(UTC).date()
        auth = AuthSchema(db=db)
        user = await UserCRUD(auth).get_by_id_crud(user_id)

        if not user:
            return False, 0

        if user.is_vip and user.vip_expire_at:
            expire = user.vip_expire_at
            if expire > datetime.now(UTC):
                return True, -1

        if user.last_summary_date != today:
            await UserCRUD(auth).update(
                id=user_id, data={"daily_summary_count": 1, "last_summary_date": today}
            )
            return True, FREE_DAILY_SUMMARY_LIMIT - 1

        current = user.daily_summary_count
        if current >= FREE_DAILY_SUMMARY_LIMIT:
            return False, 0

        await UserCRUD(auth).update(
            id=user_id,
            data={
                "daily_summary_count": current + 1,
            },
        )
        return True, FREE_DAILY_SUMMARY_LIMIT - current - 1

    @classmethod
    async def summarize_video_service(
        cls, data: SummarizeInSchema, auth: AuthSchema
    ) -> AsyncIterator[SSEMessage]:
        user = auth.user
        allowed, remaining, message = await cls._check_summary_permission(auth)
        if not allowed:
            yield SSEMessage(
                raw_data=json.dumps(
                    {"message": message, "need_login": user is None, "need_vip": user is not None},
                    ensure_ascii=False,
                ),
                event="error",
            )
            return

        try:
            loop = asyncio.get_event_loop()
            extractor = cls._get_extractor()
            subtitle_data = await loop.run_in_executor(None, extractor.extract, data.url)

            yield SSEMessage(
                raw_data=json.dumps(subtitle_data, ensure_ascii=False),
                event="subtitle",
            )

            if not subtitle_data["has_subtitle"]:
                yield SSEMessage(
                    raw_data=json.dumps(
                        {"message": "该视频没有可用的字幕，无法生成总结"}, ensure_ascii=False
                    ),
                    event="error",
                )
                return

            full_text = subtitle_data["full_text"]
            summarizer = cls._get_summarizer()

            for token in summarizer.summarize_stream(full_text, data.language):
                yield SSEMessage(raw_data=json.dumps(token, ensure_ascii=False), event="summary")

            mindmap_md = await loop.run_in_executor(
                None, summarizer.generate_mindmap, full_text, data.language
            )

            yield SSEMessage(
                raw_data=json.dumps({"markdown": mindmap_md}, ensure_ascii=False),
                event="mindmap",
            )

            quota_info = {"remaining": remaining, "limit": FREE_DAILY_SUMMARY_LIMIT}
            yield SSEMessage(
                raw_data=json.dumps(quota_info, ensure_ascii=False),
                event="quota",
            )

            yield SSEMessage(raw_data="[DONE]", event="done")

        except Exception as e:
            yield SSEMessage(
                raw_data=json.dumps({"message": f"总结失败: {str(e)}"}, ensure_ascii=False),
                event="error",
            )

    @classmethod
    def _get_extractor(cls):
        """延迟初始化 SubtitleExtractor"""
        if cls._extractor is None:
            from app.utils.summarizer import SubtitleExtractor

            cls._extractor = SubtitleExtractor()

        return cls._extractor

    @classmethod
    def _get_summarizer(cls):
        """延迟初始化 VideoSummarizer"""

        if cls._summarizer is None:
            from app.utils.summarizer import VideoSummarizer

            try:
                cls._summarizer = VideoSummarizer()

            except ValueError as e:
                raise HTTPException(status_code=500, detail=str(e))

        return cls._summarizer

    @classmethod
    async def chat_with_video_service(
        cls, data: ChatInSchema, auth: AuthSchema
    ) -> AsyncIterator[SSEMessage]:
        try:
            if not data.subtitle_text.strip():
                loop = asyncio.get_event_loop()
                extractor = cls._get_extractor()
                subtitle_data = await loop.run_in_executor(None, extractor.extract, data.url)
                if not subtitle_data["has_subtitle"]:
                    yield SSEMessage(
                        raw_data=json.dumps(
                            {"message": "该视频没有可用的字幕，无法回答问题"}, ensure_ascii=False
                        ),
                        event="error",
                    )
                    return
                subtitle_text = subtitle_data["full_text"]
            else:
                subtitle_text = data.subtitle_text

            summarizer = cls._get_summarizer()
            for token in summarizer.chat_stream(subtitle_text, data.question):
                yield SSEMessage(raw_data=json.dumps(token, ensure_ascii=False), event="answer")

            yield SSEMessage(raw_data="[DONE]", event="done")

        except Exception as e:
            yield SSEMessage(
                raw_data=json.dumps({"message": f"回答失败: {str(e)}"}, ensure_ascii=False),
                event="error",
            )
