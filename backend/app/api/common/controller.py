import asyncio
import os
from typing import Annotated

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse

from app.api.common.schema import DownloadInSchema, ParseVideoInSchema
from app.utils.douyin import is_douyin_url

CommonRouter = APIRouter(prefix="")


@CommonRouter.get("/health", summary="检查健康", description="检查健康")
async def health_check_controller():
    return {"status": "ok", "message": "万能视频下载器服务运行中"}


@CommonRouter.post("/parse", summary="解析视频", description="解析视频")
async def parse_video_controller(data: ParseVideoInSchema):
    try:
        from app.utils.douyin import douyin_parser
        from app.utils.downloader import downloader
        loop = asyncio.get_event_loop()
        if is_douyin_url(data.url):
            result = await loop.run_in_executor(None, douyin_parser.parse, data.url)
        else:
            result = await loop.run_in_executor(None, downloader.parse_video, data.url)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(
            status_code=400, detail={"success": False, "error": f"解析失败: {str(e)}"}
        )


@CommonRouter.post("/download")
async def download_video(data: DownloadInSchema):
    try:
        from app.utils.douyin import douyin_parser
        from app.utils.downloader import downloader
        loop = asyncio.get_event_loop()
        if is_douyin_url(data.url):
            result = await loop.run_in_executor(None, douyin_parser.download, data.url)
        else:
            result = await loop.run_in_executor(
                None, downloader.download_video, data.url, data.format_id
            )
        filepath = result["filepath"]
        if not os.path.exists(filepath):
            raise HTTPException(status_code=500, detail="下载的文件不存在")

        return FileResponse(
            path=filepath,
            filename=result["filename"],
            media_type="application/octet-stream",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400, detail={"success": False, "error": f"下载失败: {str(e)}"}
        )


@CommonRouter.post("/direct-url")
async def get_direct_url(data: DownloadInSchema):
    """获取视频直链"""
    try:
        from app.utils.downloader import downloader
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, downloader.get_direct_url, data.url, data.format_id
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(
            status_code=400, detail={"success": False, "error": f"获取直链失败: {str(e)}"}
        )


@CommonRouter.get("/proxy/thumbnail")
async def proxy_thumbnail(url: Annotated[str, Query(description="缩略图URL")]):
    """代理获取视频缩略图，绕过防盗链"""
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": url,
                },
            )
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "image/jpeg")
            return StreamingResponse(
                iter([resp.content]),
                media_type=content_type,
                headers={"Cache-Control": "public, max-age=86400"},
            )
    except Exception:
        raise HTTPException(status_code=502, detail="缩略图加载失败")
