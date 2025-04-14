import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
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

@dp.callback_query(F.data.startswith("type_"))
async def choose_format(callback: CallbackQuery):
    user_state[callback.from_user.id]["Тип"] = callback.data.split("_")[1]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Duo", callback_data="format_Duo"),
         InlineKeyboardButton(text="Squad", callback_data="format_Squad")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ])
    await callback.message.edit_text("🔹 Выберите формат:", reply_markup=kb)

@dp.callback_query(F.data.startswith("format_"))
async def choose_date(callback: CallbackQuery):
    user_state[callback.from_user.id]["Формат"] = callback.data.split("_")[1]
    base_date = datetime.strptime("14.04.2025", "%d.%m.%Y").date()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=base_date.strftime("%d.%m.%Y"), callback_data=f"date_{base_date.strftime('%d.%m.%Y')}"),
            InlineKeyboardButton(text=(base_date + timedelta(days=1)).strftime("%d.%m.%Y"), callback_data=f"date_{(base_date + timedelta(days=1)).strftime('%d.%m.%Y')}"),
            InlineKeyboardButton(text=(base_date + timedelta(days=2)).strftime("%d.%m.%Y"), callback_data=f"date_{(base_date + timedelta(days=2)).strftime('%d.%m.%Y')}")
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_format")]
    ])
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

    filtered = [t for t in tournaments if t['Тип'] == data['Тип'] and t['Формат'] == data['Формат'] and t['Дата'] == data['Дата'] and t['Слот'] == data['Слот'] and t['Время'] == data['Время']]

    if not filtered:
        await callback.message.edit_text("🔜 Пока нет турниров по выбранным параметрам.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_slot")]]))
        return

    text = (
        f"<b>✅ Вы выбрали:</b>\n"
        f"Тип: {data['Тип']}\n"
        f"Формат: {data['Формат']}\n"
        f"Дата: {data['Дата']}\n"
        f"Слот: {data['Слот']}\n"
        f"Время: {data['Время']}\n"
    )

    for t in filtered:
        text += (f"\n\n🏆 <b>{t['Название']}</b>\n"
                 f"𐙚 │ Призовой: {t['Приз']}\n"
                 f"𐙚 │ Стадия: {t['Стадия']}\n"
                 f"𐙚 │ Слоты: {t['Слоты']}\n"
                 f"𐙚 │ Проход: {t['Проход']}\n"
                 f"<a href='{t['Ссылка']}'>Перейти к турниру 🐾</a>")

    await callback.message.edit_text(text)

# === Назад ===
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

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
