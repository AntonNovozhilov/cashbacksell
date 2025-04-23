import asyncio
import json
import os
from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup

from texts import PRICES, REQUISE  # Убедись, что эти файлы существуют

BOT_TOKEN = "7852251789:AAEnXwI73mCpWCDAgNFF9f_HKVPlLMHv5xc"
GROUP_ID = -1002562650840
ADMIN_ID = 448888074

THREADS_FILE = "threads.json"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)


def load_threads() -> dict[int, int]:
    if os.path.exists(THREADS_FILE):
        with open(THREADS_FILE, "r") as f:
            return {int(k): v for k, v in json.load(f).items()}
    return {}

def save_threads(data: dict[int, int]):
    with open(THREADS_FILE, "w") as f:
        json.dump(data, f)

user_threads: dict[int, int] = load_threads()


@router.message(CommandStart())
async def start_dialog(message: Message):
    await message.answer("Привет! Напиши мне сообщение, и я передам его администратору.\n\nПрайс\nРеквизиты")


@router.message(lambda message: message.text == "Прайс")
async def price(message: Message):
    await message.answer(PRICES)


@router.message(lambda message: message.text == "Реквизиты")
async def banklist(message: Message):
    await message.answer(REQUISE)

@router.message(F.chat.type == "private")
async def handle_user_message(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        return
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    if user_id not in user_threads:
        topic_title = f"{username} {user_id}"
        new_topic = await bot.create_forum_topic(chat_id=GROUP_ID, name=topic_title)
        thread_id = new_topic.message_thread_id
        user_threads[user_id] = thread_id
        save_threads(user_threads)
        await bot.send_message(chat_id=GROUP_ID, text=f"Админ, подключись к диалогу с @{username} (id: {user_id})", message_thread_id=thread_id)
    await bot.forward_message(chat_id=GROUP_ID, from_chat_id=message.chat.id, message_id=message.message_id, message_thread_id=user_threads[user_id])


@router.message(F.chat.id == GROUP_ID, F.is_topic_message, Command("п"))
async def handle_price_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    thread_id = message.message_thread_id
    for uid, tid in user_threads.items():
        if tid == thread_id:
            try:
                await bot.send_message(chat_id=uid, text=PRICES)
            except Exception as e:
                print(f"Ошибка при отправке прайса пользователю {uid}: {e}")
            break


@router.message(F.chat.id == GROUP_ID, F.is_topic_message, Command("р"))
async def handle_requis_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    thread_id = message.message_thread_id
    for uid, tid in user_threads.items():
        if tid == thread_id:
            try:
                await bot.send_message(chat_id=uid, text=REQUISE)
            except Exception as e:
                print(f"Ошибка при отправке реквизитов пользователю {uid}: {e}")
            break


@router.message(F.chat.id == GROUP_ID, F.is_topic_message)
async def handle_group_reply(message: Message):
    thread_id = message.message_thread_id
    for uid, tid in user_threads.items():
        if tid == thread_id:
            try:
                if message.text:
                    await bot.send_message(chat_id=uid, text=message.text)
                elif message.photo:
                    await bot.send_photo(chat_id=uid, photo=message.photo[-1].file_id, caption=message.caption or "")
            except Exception as e:
                print(f"Ошибка при отправке пользователю {uid}: {e}")
            break

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
