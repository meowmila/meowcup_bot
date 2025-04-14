# MEOW.CUP - Полноценный бот для Telegram на aiogram 3 + Render Webhook

import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, InputFile
from aiogram.filters import CommandStart, Command
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import setup_application
from aiohttp import web

API_TOKEN = "8193369093:AAGaD0CRTKhx2Ma2vhXiuOHjBkrNCQp23AU"
WEBHOOK_URL = "https://meowcup-bot.onrender.com/webhook"
ADMIN_ID = 947800235

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

users = set()
tournaments = []
user_state = {}

@dp.message(CommandStart())
async def start(message: Message):
    users.add((message.from_user.id, message.from_user.username, message.from_user.full_name))
    user_state[message.from_user.id] = {}
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(text="🟦 Меню")]])
    if message.from_user.id == ADMIN_ID:
        kb.keyboard.append([KeyboardButton(text="🔧 Панель администратора")])
    await message.answer("Добро пожаловать в MEOW.CUP!", reply_markup=kb)

@dp.message(F.text == "🟦 Меню")
async def menu_handler(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏆 Турнир", callback_data="type_tournament"),
         InlineKeyboardButton(text="🎉 Ивент", callback_data="type_event")]
    ])
    await message.answer("🔹 Выберите тип мероприятия:", reply_markup=kb)

@dp.message(F.text == "🔧 Панель администратора")
@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔ Доступ запрещён")
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text="📋 Список турниров")],
        [KeyboardButton(text="➕ Добавить турнир")],
        [KeyboardButton(text="🗑 Удалить турнир")],
        [KeyboardButton(text="📢 Рассылка")],
        [KeyboardButton(text="👥 Пользователи")]
    ])
    await message.answer("🔧 Админ-панель:", reply_markup=kb)

@dp.message(F.text == "📋 Список турниров")
async def list_tournaments(message: Message):
    if not tournaments:
        return await message.answer("Список турниров пуст")
    text = "📋 Турниры:\n"
    for i, t in enumerate(tournaments, 1):
        text += f"{i}. {t['Название']} | {t['Дата']} | {t['Формат']} | {t['Тип']}\n"
    await message.answer(text)

@dp.message(F.text == "👥 Пользователи")
async def user_list(message: Message):
    if not users:
        return await message.answer("Пользователей пока нет")
    text = "👥 Пользователи:\n"
    for i, u in enumerate(users, 1):
        uid, username, fullname = u
        text += f"{i}. <a href='tg://user?id={uid}'>{fullname}</a> (@{username})\n"
    await message.answer(text)

@dp.message(F.text == "📢 Рассылка")
async def broadcast_prompt(message: Message):
    await message.answer("Отправь текст (и/или фото) для рассылки всем пользователям")
    dp.labeler.message(lambda m: m.from_user.id == ADMIN_ID)(broadcast)

async def broadcast(message: Message):
    for uid, _, _ in users:
        try:
            if message.photo:
                photo_id = message.photo[-1].file_id
                await bot.send_photo(uid, photo=photo_id, caption=message.caption or "")
            else:
                await bot.send_message(uid, text=message.text or "")
        except:
            continue
    await message.answer("✅ Рассылка завершена")

@dp.message(F.text == "➕ Добавить турнир")
async def add_tournament_prompt(message: Message):
    await message.answer("✍️ Введите данные турнира в формате:\nТип: tournament\nФормат: Duo\nДата: 14.04.2025\nВремя: 18:00\nСлот: Free\nНазвание: MEOW SCRIMS\nПриз: 15000 ₸\nСтадия: 1/4\nСлоты: 16\nПроход: top 6\nСсылка: https://t.me/meowcup_final")
    dp.labeler.message(lambda m: m.from_user.id == ADMIN_ID)(save_tournament)

async def save_tournament(message: Message):
    lines = message.text.split("\n")
    data = {}
    for line in lines:
        if ":" in line:
            k, v = line.split(":", 1)
            data[k.strip()] = v.strip()
    tournaments.append(data)
    await message.answer("✅ Турнир добавлен")

@dp.message(F.text == "🗑 Удалить турнир")
async def delete_tournament_prompt(message: Message):
    if not tournaments:
        return await message.answer("Список турниров пуст")
    text = "Удалите номер турнира:\n"
    for i, t in enumerate(tournaments, 1):
        text += f"{i}. {t['Название']} | {t['Дата']}\n"
    await message.answer(text)
    dp.labeler.message(lambda m: m.from_user.id == ADMIN_ID)(delete_by_index)

async def delete_by_index(message: Message):
    try:
        idx = int(message.text) - 1
        tournaments.pop(idx)
        await message.answer("❌ Удалено")
    except:
        await message.answer("❌ Ошибка: неверный номер")

# Пользовательская логика выбора турниров
user_state = {}

@dp.callback_query(F.data.startswith("type_"))
async def choose_format(callback: CallbackQuery):
    user_state[callback.from_user.id] = {"Тип": callback.data.split("_")[1]}
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Duo", callback_data="format_Duo"),
         InlineKeyboardButton(text="Squad", callback_data="format_Squad")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ])
    await callback.message.edit_text("🔹 Выберите формат:", reply_markup=kb)

@dp.callback_query(F.data.startswith("format_"))
async def choose_date(callback: CallbackQuery):
    user_state[callback.from_user.id]["Формат"] = callback.data.split("_")[1]
    base = datetime.strptime("14.04.2025", "%d.%m.%Y")
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=(base + timedelta(days=i)).strftime("%d.%m.%Y"), callback_data=f"date_{(base + timedelta(days=i)).strftime('%d.%m.%Y')}" ) for i in range(3)
    ], [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_format")]])
    await callback.message.edit_text("🔹 Выберите дату:", reply_markup=kb)

@dp.callback_query(F.data.startswith("date_"))
async def choose_slot(callback: CallbackQuery):
    user_state[callback.from_user.id]["Дата"] = callback.data.split("_")[1]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆓 Free", callback_data="slot_Free"),
         InlineKeyboardButton(text="💸 VIP", callback_data="slot_VIP")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_date")]
    ])
    await callback.message.edit_text("🔹 Выберите слот:", reply_markup=kb)

@dp.callback_query(F.data.startswith("slot_"))
async def choose_time(callback: CallbackQuery):
    user_state[callback.from_user.id]["Слот"] = callback.data.split("_")[1]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="18:00", callback_data="time_18:00"),
         InlineKeyboardButton(text="21:00", callback_data="time_21:00")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_slot")]
    ])
    await callback.message.edit_text("🔹 Выберите время:", reply_markup=kb)

@dp.callback_query(F.data.startswith("time_"))
async def show_result(callback: CallbackQuery):
    user_state[callback.from_user.id]["Время"] = callback.data.split("_")[1]
    data = user_state[callback.from_user.id]
    filtered = [t for t in tournaments if all(t.get(k) == v for k, v in data.items())]

    if not filtered:
        return await callback.message.edit_text("🔜 Пока нет турниров по выбранным параметрам.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_slot")]]))

    text = f"<b>✅ Вы выбрали:</b>\nТип: {data['Тип']}\nФормат: {data['Формат']}\nДата: {data['Дата']}\nСлот: {data['Слот']}\nВремя: {data['Время']}\n"
    for t in filtered:
        text += f"\n🏆 <b>{t['Название']}</b>\n𐙚 │ Призовой: {t['Приз']}\n𐙚 │ Стадия: {t['Стадия']}\n𐙚 │ Слоты: {t['Слоты']}\n𐙚 │ Проход: {t['Проход']}\n<a href='{t['Ссылка']}'>Перейти к турниру 🐾</a>"
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_slot")]]))

# Назад
@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    await menu_handler(callback.message)

@dp.callback_query(F.data == "back_to_format")
async def back_to_format(callback: CallbackQuery):
    await choose_format(callback)

@dp.callback_query(F.data == "back_to_date")
async def back_to_date(callback: CallbackQuery):
    await choose_date(callback)

@dp.callback_query(F.data == "back_to_slot")
async def back_to_slot(callback: CallbackQuery):
    await choose_slot(callback)

# Webhook
async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)

dp.startup.register(on_startup)
app = web.Application()
setup_application(app, dp, bot=bot)
web.run_app(app, port=10000)
