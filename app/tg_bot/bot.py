import asyncio
import os
from aiogram import Bot, Dispatcher


bot = Bot(token=os.getenv('TOKEN'))
dp =Dispatcher()


async def main():
    await dp.start_polling(bot)


asyncio.run(main())




