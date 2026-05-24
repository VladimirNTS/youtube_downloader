from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class DownloadResult:
    file_path: Path
    title: str
    duration: int
    filesize: int


class DownloaderService:
    """
    Сервис скачивания видео. Всю блокирующую работу выносит
    в отдельный ThreadPoolExecutor, чтобы не мешать Event Loop.
    """

    def __init__(
        self,
        download_dir: Path,
        max_workers: int = 4,
    ) -> None:
        self._download_dir = download_dir
        self._download_dir.mkdir(parents=True, exist_ok=True)
        # Ограничиваем количество одновременных скачиваний.
        # Больше 4-8 смысла не имеет: упрёмся в сеть/диск/RAM.
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="ytdlp-worker",
        )

    async def download(
        self,
        url: str,
        progress_hook: Callable[[dict[str, Any]], None] | None = None,
    ) -> DownloadResult:
        """
        Асинхронная обёртка. Внутри — честный синхронный yt-dlp,
        но исполняется в отдельном потоке.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._executor,
            self._blocking_download,
            url,
            progress_hook,
        )

    def _blocking_download(
        self,
        url: str,
        progress_hook: Callable[[dict[str, Any]], None] | None,
    ) -> DownloadResult:
        """Этот метод выполняется ВНЕ event loop, в рабочем потоке."""
        ydl_opts: dict[str, Any] = {
            # Лучшее mp4 до 1080p + лучший m4a, смёрженные в mp4.
            "format": "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
            "merge_output_format": "mp4",
            "outtmpl": str(self._download_dir / "%(id)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,  # свой хук, стандартный stdout не нужен
            "concurrent_fragment_downloads": 4,
            "retries": 3,
        }
        if progress_hook is not None:
            ydl_opts["progress_hooks"] = [progress_hook]

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = Path(ydl.prepare_filename(info))
        except DownloadError as e:
            logger.warning("yt-dlp error for %s: %s", url, e)
            raise

        return DownloadResult(
            file_path=file_path,
            title=info.get("title", "video"),
            duration=int(info.get("duration") or 0),
            filesize=file_path.stat().st_size,
        )

    async def shutdown(self) -> None:
        self._executor.shutdown(wait=True, cancel_futures=False)