from pydantic import BaseModel, Field


class SummarizeInSchema(BaseModel):
    url: str = Field(..., description="视频链接")
    language: str = Field(default="zh", description="语言")


class ChatInSchema(BaseModel):
    url: str = Field(..., description="视频链接")
    question: str = Field(..., description="问题")
    subtitle_text: str = Field(default="", description="字幕")
