# MEOW.CUP - Финальная версия с Webhook и всеми функциями (исправлены кнопки "Назад")

import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web

API_TOKEN = "8193369093:AAGaD0CRTKhx2Ma2vhXiuOHjBkrNCQp23AU"
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"https://meowcup-bot.onrender.com{WEBHOOK_PATH}"
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
async def menu(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏆 Турнир", callback_data="type_tournament"),
         InlineKeyboardButton(text="🎉 Ивент", callback_data="type_event")]
    ])
    await message.answer("🔹 Выберите тип мероприятия:", reply_markup=kb)

@dp.callback_query(F.data == "back_to_menu")
async def back_menu(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏆 Турнир", callback_data="type_tournament"),
         InlineKeyboardButton(text="🎉 Ивент", callback_data="type_event")]
    ])
    await callback.message.edit_text("🔹 Выберите тип мероприятия:", reply_markup=kb)

@dp.callback_query(F.data == "back_to_format")
async def back_format(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Duo", callback_data="format_Duo"), InlineKeyboardButton(text="Squad", callback_data="format_Squad")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ])
    await callback.message.edit_text("🔹 Выберите формат:", reply_markup=kb)

@dp.callback_query(F.data == "back_to_date")
async def back_date(callback: CallbackQuery):
    base = datetime.strptime("14.04.2025", "%d.%m.%Y")
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=(base + timedelta(days=i)).strftime("%d.%m.%Y"), callback_data=f"date_{(base + timedelta(days=i)).strftime('%d.%m.%Y')}" ) for i in range(3)
    ], [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_format")]])
    await callback.message.edit_text("🔹 Выберите дату:", reply_markup=kb)

@dp.callback_query(F.data == "back_to_slot")
async def back_slot(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆓 Free", callback_data="slot_Free"), InlineKeyboardButton(text="💸 VIP", callback_data="slot_VIP")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_date")]
    ])
    await callback.message.edit_text("🔹 Выберите слот:", reply_markup=kb)

# Остальной код остается без изменений (handlers, admin, webhook и запуск)
# Webhook и запуск:

async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)

app = web.Application()
dp.startup.register(on_startup)
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
app.router.add_get("/", lambda _: web.Response(text="MEOW.CUP OK"))

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    web.run_app(app, port=10000)
