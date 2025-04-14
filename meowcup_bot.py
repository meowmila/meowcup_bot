import asyncio
import logging
from datetime import datetime, timedelta
import json

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    FSInputFile
)
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest

API_TOKEN = "8193369093:AAGaD0CRTKhx2Ma2vhXiuOHjBkrNCQp23AU"
ADMIN_ID = 947800235

tournaments = []
users = {}
admin_state = {}

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

def save_tournaments():
    with open("tournaments.json", "w", encoding="utf-8") as f:
        json.dump(tournaments, f, ensure_ascii=False, indent=2)

def load_tournaments():
    global tournaments
    try:
        with open("tournaments.json", "r", encoding="utf-8") as f:
            tournaments = json.load(f)
    except FileNotFoundError:
        tournaments = []

def get_date_keyboard():
    today = datetime.today()
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=(today + timedelta(days=i)).strftime("%d.%m.%Y"), callback_data=f"date:{(today + timedelta(days=i)).strftime('%Y-%m-%d')}")]
        for i in range(3)
    ])

def get_type_keyboard(date):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="FREE", callback_data=f"type:{date}:free")],
        [InlineKeyboardButton(text="VIP", callback_data=f"type:{date}:vip")],
    ])

def get_time_keyboard(date, ttype):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="18:00", callback_data=f"time:{date}:{ttype}:18:00")],
        [InlineKeyboardButton(text="21:00", callback_data=f"time:{date}:{ttype}:21:00")],
    ])

def get_stage_keyboard(date, ttype, time):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=stage, callback_data=f"stage:{date}:{ttype}:{time}:{stage}")]
        for stage in ["1/8", "1/4", "1/2"]
    ])

def get_tournament_keyboard(filtered):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t['name'], callback_data=f"show:{t['id']}")]
        for t in filtered
    ]) if filtered else None

def filter_tournaments(date, ttype, time, stage):
    return [t for t in tournaments if t['date'] == date and t['type'] == ttype and t['time'] == time and t['stage'] == stage]

@dp.message(CommandStart())
async def start(message: Message):
    users[message.from_user.id] = message.from_user.full_name
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Турнир", callback_data="start:tournament")]
    ])
    if message.from_user.id == ADMIN_ID:
        kb.inline_keyboard.append([InlineKeyboardButton(text="⚙️ Админ-панель", callback_data="admin:panel")])
    await message.answer("Добро пожаловать в MEOW.CUP!", reply_markup=kb)

@dp.callback_query(F.data == "start:tournament")
async def select_date(call: CallbackQuery):
    await call.message.answer("📅 Выберите дату:", reply_markup=get_date_keyboard())

@dp.callback_query(F.data.startswith("date:"))
async def select_type(call: CallbackQuery):
    date = call.data.split(":")[1]
    await call.message.answer("📂 Выберите тип:", reply_markup=get_type_keyboard(date))

@dp.callback_query(F.data.startswith("type:"))
async def select_time(call: CallbackQuery):
    _, date, ttype = call.data.split(":")
    await call.message.answer("⏰ Выберите время:", reply_markup=get_time_keyboard(date, ttype))

@dp.callback_query(F.data.startswith("time:"))
async def select_stage(call: CallbackQuery):
    _, date, ttype, time = call.data.split(":")
    await call.message.answer("🎯 Выберите стадию:", reply_markup=get_stage_keyboard(date, ttype, time))

@dp.callback_query(F.data.startswith("stage:"))
async def show_filtered_tournaments(call: CallbackQuery):
    _, date, ttype, time, stage = call.data.split(":")
    filtered = filter_tournaments(date, ttype, time, stage)
    keyboard = get_tournament_keyboard(filtered)
    if keyboard:
        await call.message.answer("📋 Турниры:", reply_markup=keyboard)
    else:
        await call.message.answer("❌ Турниров не найдено.")

@dp.callback_query(F.data.startswith("show:"))
async def show_tournament(call: CallbackQuery):
    tid = int(call.data.split(":")[1])
    tour = next((t for t in tournaments if t['id'] == tid), None)
    if not tour:
        return await call.message.answer("⚠️ Турнир не найден.")
    text = (
        f"<b>{tour['name']}</b>\n"
        f"🏆 Приз: {tour['prize']}\n"
        f"🗓️ {tour['date']} {tour['time']}\n"
        f"🎯 Стадия: {tour['stage']}\n"
        f"🔗 Вход: {tour['join']}\n"
    )
    try:
        if tour.get("photo"):
            await call.message.answer_photo(photo=tour["photo"], caption=text)
        else:
            await call.message.answer(text)
    except TelegramBadRequest:
        await call.message.answer(text)

@dp.callback_query(F.data == "admin:panel")
async def admin_panel(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return await call.answer("Нет доступа", show_alert=True)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить турнир", callback_data="admin:add")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin:broadcast")],
        [InlineKeyboardButton(text="🗑 Очистить прошедшие", callback_data="admin:clean")],
        [InlineKeyboardButton(text="📥 Экспорт JSON", callback_data="admin:export")]
    ])
    await call.message.answer("⚙️ Админ-панель:", reply_markup=kb)

@dp.callback_query(F.data == "admin:export")
async def export_tournaments(call: CallbackQuery):
    save_tournaments()
    file = FSInputFile("tournaments.json")
    await call.message.answer_document(file, caption="📤 Экспорт турниров в JSON")

@dp.callback_query(F.data == "admin:clean")
async def clean_tournaments(call: CallbackQuery):
    now = datetime.now().date()
    before = len(tournaments)
    tournaments[:] = [t for t in tournaments if datetime.strptime(t['date'], "%Y-%m-%d").date() >= now]
    save_tournaments()
    await call.message.answer(f"🧹 Удалено {before - len(tournaments)} старых турниров.")

@dp.callback_query(F.data == "admin:add")
async def start_add_tournament(call: CallbackQuery):
    admin_state[call.from_user.id] = {"step": "name", "data": {}}
    await call.message.answer("Введите название турнира:")

@dp.message(F.text)
async def handle_admin_input(message: Message):
    if message.from_user.id != ADMIN_ID or message.from_user.id not in admin_state:
        return

    step = admin_state[message.from_user.id]["step"]
    data = admin_state[message.from_user.id]["data"]

    if step == "name":
        data["name"] = message.text
        admin_state[message.from_user.id]["step"] = "date"
        await message.answer("Дата (ГГГГ-ММ-ДД):")
    elif step == "date":
        data["date"] = message.text
        admin_state[message.from_user.id]["step"] = "time"
        await message.answer("Время:")
    elif step == "time":
        data["time"] = message.text
        admin_state[message.from_user.id]["step"] = "type"
        await message.answer("Тип (free/vip):")
    elif step == "type":
        data["type"] = message.text
        admin_state[message.from_user.id]["step"] = "stage"
        await message.answer("Стадия:")
    elif step == "stage":
        data["stage"] = message.text
        admin_state[message.from_user.id]["step"] = "prize"
        await message.answer("Приз:")
    elif step == "prize":
        data["prize"] = message.text
        admin_state[message.from_user.id]["step"] = "join"
        await message.answer("Ссылка на вход:")
    elif step == "join":
        data["join"] = message.text
        admin_state[message.from_user.id]["step"] = "photo"
        await message.answer("Фото или 'нет':")
    elif step == "photo":
        if message.photo:
            file_id = message.photo[-1].file_id
        elif message.text.lower() == "нет":
            file_id = None
        else:
            await message.answer("Пришлите фото или напишите 'нет'")
            return
        data["photo"] = file_id
        data["id"] = len(tournaments) + 1
        tournaments.append(data)
        save_tournaments()
        await message.answer("✅ Турнир добавлен!")
        del admin_state[message.from_user.id]

@dp.message(F.photo)
async def handle_photo(message: Message):
    if message.from_user.id == ADMIN_ID and message.from_user.id in admin_state:
        await handle_admin_input(message)

@dp.callback_query(F.data == "admin:broadcast")
async def broadcast_text(call: CallbackQuery):
    admin_state[call.from_user.id] = {"step": "broadcast"}
    await call.message.answer("✉️ Введите текст для рассылки:")

@dp.message(F.text)
async def handle_broadcast(message: Message):
    if message.from_user.id == ADMIN_ID and admin_state.get(message.from_user.id, {}).get("step") == "broadcast":
        count = 0
        for uid in users:
            try:
                await bot.send_message(uid, message.text)
                count += 1
            except:
                continue
        await message.answer(f"📬 Отправлено {count} сообщений.")
        del admin_state[message.from_user.id]

async def main():
    logging.basicConfig(level=logging.INFO)
    load_tournaments()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
