from aiogram import Router, types
from aiogram.filters import Command


user_private_router = Router()


@user_private_router.message(Command("start"))
async def start(message: types.Message):
	await message.answer("hello")
