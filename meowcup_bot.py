# MEOW.CUP Bot — Полный финальный код со всеми фишками

import os
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import io
import asyncio

API_TOKEN = os.getenv("BOT_TOKEN") or "8193369093:AAGaD0CRTKhx2Ma2vhXiuOHjBkrNCQp23AU"
ADMIN_ID = 947800235

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# Данные
users = set()
tournaments = []
photos = {}  # key = stage/time/date/label
ctx = {}

class AddTournament(StatesGroup):
    waiting_photo = State()

# Утилиты

def get_upcoming_dates():
    today = datetime.now()
    return [(today + timedelta(days=i)).strftime("%d.%m.%Y") for i in range(3)]

def build_keyboard(buttons, row=2):
    builder = InlineKeyboardBuilder()
    for b in buttons:
        builder.button(text=b, callback_data=b)
    builder.adjust(row)
    return builder.as_markup()

def overlay_text_on_image(image_bytes, text):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
    width, _ = image.size
    text_width = draw.textlength(text, font=font)
    draw.rectangle([(0, 0), (width, 60)], fill=(0, 0, 0, 180))
    draw.text(((width - text_width) / 2, 10), text, fill="white", font=font)
    output = io.BytesIO()
    image.save(output, format='PNG')
    output.seek(0)
    return output

def cleanup_old():
    today = datetime.now().strftime("%d.%m.%Y")
    global tournaments
    tournaments = [t for t in tournaments if t['date'] >= today]

# Команды
@dp.message(F.text == "/start")
async def start_cmd(message: Message):
    users.add(message.from_user.id)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton("🟦 Меню"))
    if message.from_user.id == ADMIN_ID:
        kb.add(types.KeyboardButton("🔧 Панель администратора"))
    await message.answer("Добро пожаловать в MEOW.CUP!", reply_markup=kb)

@dp.message(F.text == "🔧 Панель администратора")
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    kb = build_keyboard(["Добавить турнир", "Загрузить фото кнопки", "Пользователи"])
    await message.answer("Панель администратора:", reply_markup=kb)

@dp.callback_query(F.data == "Пользователи")
async def list_users(call: CallbackQuery):
    await call.message.answer("Пользователей: " + str(len(users)))

@dp.callback_query(F.data == "Загрузить фото кнопки")
async def ask_photo_upload(call: CallbackQuery):
    await call.message.answer("Отправьте фото с подписью = код кнопки (например: 18:00 или 'турнир')")

@dp.message(F.photo & F.caption & (F.from_user.id == ADMIN_ID))
async def photo_button_upload(message: Message):
    photos[message.caption.lower()] = message.photo[-1].file_id
    await message.answer("Фото сохранено под ключом: " + message.caption)

@dp.callback_query(F.data == "Добавить турнир")
async def ask_tournament_data(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Отправь фото с подписью в формате:\n<дата> | <время> | <тип> | <стадия> | <название> | <описание> | <ссылка>")
    await state.set_state(AddTournament.waiting_photo)

@dp.message(AddTournament.waiting_photo & F.photo)
async def handle_add_tournament(message: Message, state: FSMContext):
    if not message.caption:
        await message.answer("Добавь подпись к фото!")
        return
    parts = [p.strip() for p in message.caption.split("|")]
    if len(parts) != 7:
        await message.answer("Неверный формат. Должно быть 7 параметров через |")
        return
    date, time, type_, stage, title, desc, link = parts
    file = await bot.download(message.photo[-1])
    img = overlay_text_on_image(file.read(), title)
    sent = await bot.send_photo(message.chat.id, photo=img)
    tournaments.append({
        "date": date, "time": time, "type": type_.lower(), "stage": stage,
        "title": title, "desc": desc, "link": link, "photo": sent.photo[-1].file_id
    })
    await message.answer("✅ Турнир добавлен!")
    await state.clear()
    cleanup_old()

@dp.message(F.text == "🟦 Меню")
async def open_main_menu(message: Message):
    kb = build_keyboard(["турнир", "ивент", "праки"], row=1)
    pid = photos.get("меню")
    await message.answer_photo(pid, caption="Выберите тип:", reply_markup=kb) if pid else await message.answer("Выберите тип:", reply_markup=kb)

@dp.callback_query()
async def universal_flow(call: CallbackQuery):
    uid = call.from_user.id
    data = call.data

    if data in ["турнир", "ивент", "праки"]:
        ctx[uid] = {"type": data}
        kb = build_keyboard(get_upcoming_dates(), row=1)
        pid = photos.get(data)
        await call.message.answer_photo(pid, caption="Выберите дату:", reply_markup=kb) if pid else await call.message.answer("Выберите дату:", reply_markup=kb)

    elif data in get_upcoming_dates():
        ctx[uid]["date"] = data
        kb = build_keyboard(["18:00", "21:00"])
        pid = photos.get(data)
        await call.message.answer_photo(pid, caption="Выберите время:", reply_markup=kb) if pid else await call.message.answer("Выберите время:", reply_markup=kb)

    elif data in ["18:00", "21:00"]:
        ctx[uid]["time"] = data
        if ctx[uid]['type'] == "праки":
            return await show_titles(call, uid)
        stages = sorted(set(t['stage'] for t in tournaments if t['date'] == ctx[uid]['date'] and t['time'] == data and t['type'] == ctx[uid]['type']))
        if not stages:
            return await show_titles(call, uid)
        kb = build_keyboard(stages)
        await call.message.answer("Выберите стадию:", reply_markup=kb)

    elif data in ["1/8", "1/4", "1/2", "финал"]:
        ctx[uid]['stage'] = data
        kb = build_keyboard(["duo", "squad"])
        await call.message.answer("Выберите формат:", reply_markup=kb)

    elif data in ["duo", "squad"]:
        ctx[uid]['format'] = data
        await show_titles(call, uid)

    elif any(t['title'] == data for t in tournaments):
        t = next(t for t in tournaments if t['title'] == data)
        text = f"<b>{t['title']}</b>\n{t['desc']}\n\nСтадия: {t['stage']} | {t['time']} | {t['date']}\nСлот: {t['type']}"
        kb = build_keyboard(["✍️Написать в лс", "💫Перейти к турниру", "Назад"] if t['type'] == "вип" else ["💫Перейти к турниру", "Назад"])
        await call.message.answer_photo(t['photo'], caption=text, reply_markup=kb)

    elif data == "Назад":
        await open_main_menu(call.message)

async def show_titles(call, uid):
    filters = ctx[uid]
    filtered = [t for t in tournaments if all([
        t['type'] == filters['type'],
        t['date'] == filters['date'],
        t['time'] == filters['time'],
        filters.get('stage') is None or t['stage'] == filters['stage'],
        filters.get('format') is None or t.get('format') == filters['format']
    ])]
    if not filtered:
        await call.message.answer("Нет турниров по этим параметрам")
        return
    kb = build_keyboard([t['title'] for t in filtered], row=1)
    await call.message.answer("Выберите турнир:", reply_markup=kb)

# Запуск
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(dp.start_polling(bot))
