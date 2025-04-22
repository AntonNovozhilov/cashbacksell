import asyncio
import os
import logging

from aiogram import (
    Bot,
    Dispatcher,
    Router,
    types, F
)
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv

from fsp import PostForm
from aiogram.fsm.context import FSMContext
from texts import PRICE, PRICES, REQUISE

load_dotenv()


TOKEN = os.getenv('TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
bot = Bot(TOKEN)
dp = Dispatcher()
router = Router()


@dp.message(CommandStart())
async def hendler_start(message: types.Message):
    kb = [
        [types.KeyboardButton(text='Прайс')],
        [types.KeyboardButton(text='Реквизиты')],
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("Добро пожаловать! Выберите действие:", reply_markup=keyboard)

@dp.message(Command('help'))
async def hendler_help(message: types.Message):
    text = 'Этот бот создан для подачи заявок на размещение. Инструкция'
    await message.answer(text=text)

@dp.message(lambda message: message.text=='Прайс')
async def price(message: types.Message):
    await message.answer(PRICES)

@dp.message(lambda message: message.text=='Реквизиты')
async def banklist(message: types.Message):
    await message.answer(REQUISE)

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)


if __name__=='__main__':
    asyncio.run(main())