from pydantic import BaseModel, Field


class ParseVideoInSchema(BaseModel):
    url: str = Field(..., description="视频链接")


class DownloadInSchema(BaseModel):
    url: str = Field(..., description="视频链接")
    format_id: str = Field(default="bestvideo+bestaudio/best")
