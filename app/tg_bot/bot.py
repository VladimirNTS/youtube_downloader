import asyncio
import os
from aiogram import Bot, Dispatcher

from app.tg_bot.handlers.user_router import user_private_router


bot = Bot(token=os.getenv('TOKEN'))
dp = Dispatcher()
dp.include_router(user_private_router)




