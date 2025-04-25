import asyncio
import jso
import os
from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv
load_dotenv()  

from texts import FAQ, REQUISE  # Убедись, что эти файлы существуют

BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_ID = -1002562650840
ADMIN_ID = [6446030996, 448888074, 1111339115]
CHANNEL_ID = -1002083919862  # сюда вставь chat_id канала
PRICE_MESSAGE_ID = 7
THREADS_FILE = "threads.json"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

finish_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Завершить загрузку", callback_data="finish_post")]
])

class PostState(StatesGroup):
    title = State()
    place = State()
    price = State()
    cashback = State()
    photo = State()

def load_threads() -> dict[int, int]:
    if os.path.exists(THREADS_FILE):
        with open(THREADS_FILE, "r") as f:
            return {int(k): v for k, v in json.load(f).items()}
    return {}

def save_threads(data: dict[int, int]):
    with open(THREADS_FILE, "w") as f:
        json.dump(data, f)

user_threads: dict[int, int] = load_threads()

@dp.message(CommandStart())
async def hendler_start(message: Message):
    kb = [
        [KeyboardButton(text='Прайс')],
        [KeyboardButton(text='Реквизиты')],
        [KeyboardButton(text='Составить пост')],
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("Добро пожаловать! Напиши свой вопрос и дождитесь ответа админисратова или выберите действие:", reply_markup=keyboard)

@dp.message(Command('help'))
async def hendler_help(message: Message):
    text = FAQ
    await message.answer(text=text, parse_mode="HTML")


@router.message(lambda message: message.text == "Прайс")
async def price(message: Message):
    await bot.forward_message(
        chat_id=message.chat.id,
        from_chat_id=CHANNEL_ID,
        message_id=PRICE_MESSAGE_ID
    )

@router.message(lambda message: message.text == "Реквизиты")
async def banklist(message: Message):
    await message.answer(REQUISE)

@router.message(lambda message: message.text == "Составить пост")
async def create_post(message: Message, state: FSMContext):
    await message.answer("Введите название товара:")
    await state.set_state(PostState.title)

@router.message(PostState.title)
async def post_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("На каком маркетплейсе вы продаете")
    await state.set_state(PostState.place)

@router.message(PostState.place)
async def post_place(message: Message, state: FSMContext):
    await state.update_data(place=message.text)
    await message.answer("Введите стоимость на маркетплейсе в рублях:")
    await state.set_state(PostState.price)

@router.message(PostState.price)
async def post_price(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите цену числом без пробелов и символов (например, 1490):")
        return
    await state.update_data(price=message.text)
    await message.answer("Введите сумму кешбэка в рублях:")
    await state.set_state(PostState.cashback)

@router.message(PostState.cashback)
async def post_cashback(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите кешбэк числом без пробелов и символов (например, 300):")
        return
    await state.update_data(cashback=message.text)
    await message.answer("Теперь прикрепите фото к посту:")
    await state.set_state(PostState.photo)

@router.message(PostState.photo, ~F.photo)
async def wrong_input_in_photo(message: Message):
    await message.answer("❗️Пожалуйста, прикрепите *фотографию* товара.\n"
                         "Это можно сделать, используя 📎 и выбрав *Фото*.\n")


@router.message(PostState.photo, F.photo)
async def post_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    if len(photos) == 1:
        await message.answer(
            "🖼 Фото добавлены. Далее: отправьте ещё или нажмите кнопку ниже для завершения.",
            reply_markup=finish_kb
        )

@router.callback_query(F.data == "finish_post")
async def handle_finish(callback: CallbackQuery, state: FSMContext):
    await callback.answer()  # скрыть "загрузка..." у пользователя
    data = await state.get_data()
    photos = data.get("photos", [])

    if not photos:
        await callback.message.answer("Сначала добавьте хотя бы одно фото.")
        return

    price = int(data["price"])
    cashback = int(data["cashback"])
    new_price = price - cashback
    username = callback.from_user.username or callback.from_user.first_name

    text = (
        f"<b>{data['title']}</b> \n"
        f"<b>{data['place']}</b> \n\n"
        f"<b>Цена на маркетплейсе:</b> {data['price']}₽ ❌ \n"
        f"<b>Цена для вас:</b> {new_price}₽ ✅ \n"
        f"<b>Кешбэк:</b> {data['cashback']}₽ 🔥 \n\n"
        f"🖊️ <b>Для получения инструкции по выкупу пиши</b> @{username}"
    )

    user_id = callback.from_user.id
    if user_id not in user_threads:
        topic_title = f"{username} {user_id}"
        new_topic = await bot.create_forum_topic(chat_id=GROUP_ID, name=topic_title)
        thread_id = new_topic.message_thread_id
        user_threads[user_id] = thread_id
        save_threads(user_threads)
        await bot.send_message(chat_id=GROUP_ID, text=f"Новый пользователь: @{username} (id: {user_id})", message_thread_id=thread_id)

    thread_id = user_threads[user_id]
    media_group = [InputMediaPhoto(media=file_id) for file_id in photos]
    await bot.send_media_group(chat_id=GROUP_ID, media=media_group, message_thread_id=thread_id)

    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Пост принят", callback_data=f"approve_{user_id}")],
        [InlineKeyboardButton(text="❌ Пост отклонён", callback_data=f"reject_{user_id}")]
    ])
    await bot.send_message(chat_id=GROUP_ID, text=text, message_thread_id=thread_id, reply_markup=buttons)
    await state.clear()
    await callback.message.answer("Готово! Пост отправлен на модерацию.")


@router.callback_query(F.data.startswith("approve_"))
async def approve_post(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_ID:
        return
    user_id = int(callback.data.split("_")[1])
    try:
        await bot.send_message(chat_id=user_id, text="✅ Ваш пост принят! Ожидайте размещения. Если остались вопросы можете задать их здесь.")
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception as e:
        print(f"Ошибка при отправке принятия пользователю {user_id}: {e}")
        await callback.answer("Не удалось отправить сообщение пользователю.")

@router.callback_query(F.data.startswith("reject_"))
async def reject_post(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_ID:
        return
    user_id = int(callback.data.split("_")[1])
    try:
        await bot.send_message(chat_id=user_id, text="❌ Ваш пост был отклонен. Попробуйте подать его заново или напишите администратору.")
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.answer("Пользователю отправлено сообщение об отклонении.")
    except Exception as e:
        print(f"Ошибка при отправке отказа пользователю {user_id}: {e}")
        await callback.answer("Не удалось отправить сообщение пользователю.")

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
    if message.from_user.id not in ADMIN_ID:
        return
    thread_id = message.message_thread_id
    for uid, tid in user_threads.items():
        if tid == thread_id:
            try:
                await bot.forward_message(
        chat_id=uid,
        from_chat_id=CHANNEL_ID,
        message_id=PRICE_MESSAGE_ID
    )
            except Exception as e:
                print(f"Ошибка при отправке прайса пользователю {uid}: {e}")
            break

@router.message(F.chat.id == GROUP_ID, F.is_topic_message, Command("р"))
async def handle_requis_command(message: Message):
    if message.from_user.id not in ADMIN_ID:
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
