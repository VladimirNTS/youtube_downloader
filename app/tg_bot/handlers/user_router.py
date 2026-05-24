from aiogram import Router, types
from aiogram.types import FSInputFile, Message
from aiogram.filters import Command

from app.service.download import DownloaderService, DownloadError


user_private_router = Router()


@user_private_router.message(Command("start"))
async def handle_url(
    message: Message,
    downloader: DownloaderService,  # инжектится через workflow_data
) -> None:
    status = await message.answer("⏳ Принял, качаю...")
    try:
        result = await downloader.download(message.text)
    except DownloadError:
        await status.edit_text("❌ Не смог скачать. Проверьте ссылку.")
        return

    await message.answer_video(
        FSInputFile(result.file_path),
        caption=result.title[:1024],
    )
    await status.delete()
    result.file_path.unlink(missing_ok=True)
