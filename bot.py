import asyncio
import os
import logging

from aiogram import (
    Bot,
    Dispatcher,
    types
)
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from dotenv import load_dotenv

from fsp import PostForm
from texts import PRICE

load_dotenv()


TOKEN = os.getenv('TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
bot = Bot(TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def hendler_start(message: types.Message):
    text = f'''Приветствую, {message.chat.username}.\n
Напишите свой вопрос и наш менеджер ответит вам в ближайшее время!
'''
    await message.answer(text=text)

@dp.message(Command('help'))
async def hendler_help(message: types.Message):
    text = 'Этот бот создан для подачи заявок на размещение. Инструкция'
    await message.answer(text=text)

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)


if __name__=='__main__':
    asyncio.run(main())