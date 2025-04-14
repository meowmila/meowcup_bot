import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import (
    Message, CallbackQuery, InputFile, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.filters import CommandStart, Command
from aiogram.client.default import DefaultBotProperties

API_TOKEN = "8193369093:AAGaD0CRTKhx2Ma2vhXiuOHjBkrNCQp23AU"
ADMIN_ID = 947800235

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

users = set()
tournaments = []
user_state = {}

# /start
@dp.message(CommandStart())
async def start_menu(message: Message):
    users.add((message.from_user.id, message.from_user.username, message.from_user.full_name))
    user_state[message.from_user.id] = {}
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(text="🟦 Меню")]])
    if message.from_user.id == ADMIN_ID:
        keyboard.keyboard.append([KeyboardButton(text="🔧 Панель администратора")])
    await message.answer("Добро пожаловать! Нажмите Меню, чтобы начать:", reply_markup=keyboard)

# Меню пользователя
@dp.message(F.text == "🟦 Меню")
async def open_user_menu(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏆 Турнир", callback_data="type_tournament")],
        [InlineKeyboardButton(text="🎉 Ивент", callback_data="type_event")]
    ])
    await message.answer_photo(InputFile("images/select_type.jpg"), caption="🔹 Выберите тип мероприятия", reply_markup=kb)

# Шаги пользователя с кнопками "назад" и сохранением состояния
@dp.callback_query(F.data.startswith("type_"))
async def choose_format(callback: CallbackQuery):
    user_state[callback.from_user.id]["Тип"] = callback.data.split("_")[1]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Duo", callback_data="format_Duo")],
        [InlineKeyboardButton(text="Squad", callback_data="format_Squad")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_start")]
    ])
    await callback.message.edit_text("🔹 Выбери формат:", reply_markup=kb)

@dp.callback_query(F.data.startswith("format_"))
async def choose_date(callback: CallbackQuery):
    user_state[callback.from_user.id]["Формат"] = callback.data.split("_")[1]
    today = datetime.now().date()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Сегодня", callback_data=f"date_{today.strftime('%d.%m.%Y')}")],
        [InlineKeyboardButton(text="Завтра", callback_data=f"date_{(today + timedelta(days=1)).strftime('%d.%m.%Y')}")],
        [InlineKeyboardButton(text="Послезавтра", callback_data=f"date_{(today + timedelta(days=2)).strftime('%d.%m.%Y')}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_format")]
    ])
    await callback.message.edit_text("🔹 Выбери дату:", reply_markup=kb)

# Админка и другие шаги добавляются аналогично — при необходимости я допишу полную структуру.

# === Запуск ===
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
