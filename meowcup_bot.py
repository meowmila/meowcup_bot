import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, InputFile
)
from aiogram.filters import CommandStart, Command
from aiogram.client.default import DefaultBotProperties

API_TOKEN = "PASTE_YOUR_TOKEN_HERE"
ADMIN_ID = 947800235

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

users = set()
tournaments = []
user_state = {}

# === START ===
@dp.message(CommandStart())
async def start(message: Message):
    users.add((message.from_user.id, message.from_user.username, message.from_user.full_name))
    user_state[message.from_user.id] = {}
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(text="🟦 Меню")]])
    if message.from_user.id == ADMIN_ID:
        kb.keyboard.append([KeyboardButton(text="🔧 Панель администратора")])
    await message.answer("Добро пожаловать в MEOW.CUP!", reply_markup=kb)

# === Меню ===
@dp.message(F.text == "🟦 Меню")
async def menu_handler(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏆 Турнир", callback_data="type_tournament")],
        [InlineKeyboardButton(text="🎉 Ивент", callback_data="type_event")]
    ])
    await message.answer("🔹 Выберите тип мероприятия:", reply_markup=kb)

# === Шаги выбора ===
@dp.callback_query(F.data.startswith("type_"))
async def choose_format(callback: CallbackQuery):
    user_state[callback.from_user.id]["Тип"] = callback.data.split("_")[1]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Duo", callback_data="format_Duo")],
        [InlineKeyboardButton(text="Squad", callback_data="format_Squad")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_start")]
    ])
    await callback.message.edit_text("🔹 Выберите формат:", reply_markup=kb)

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
    await callback.message.edit_text("🔹 Выберите дату:", reply_markup=kb)

@dp.callback_query(F.data.startswith("date_"))
async def choose_slot(callback: CallbackQuery):
    user_state[callback.from_user.id]["Дата"] = callback.data.split("_")[1]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆓 Free", callback_data="slot_Free")],
        [InlineKeyboardButton(text="💸 VIP", callback_data="slot_VIP")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_date")]
    ])
    await callback.message.edit_text("🔹 Выберите слот:", reply_markup=kb)

@dp.callback_query(F.data.startswith("slot_"))
async def choose_time(callback: CallbackQuery):
    user_state[callback.from_user.id]["Слот"] = callback.data.split("_")[1]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="18:00", callback_data="time_18:00")],
        [InlineKeyboardButton(text="21:00", callback_data="time_21:00")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_slot")]
    ])
    await callback.message.edit_text("🔹 Выберите время:", reply_markup=kb)

@dp.callback_query(F.data.startswith("time_"))
async def show_result(callback: CallbackQuery):
    user_state[callback.from_user.id]["Время"] = callback.data.split("_")[1]
    data = user_state[callback.from_user.id]
    text = (
        f"<b>✅ Вы выбрали:</b>\n"
        f"Тип: {data['Тип']}\n"
        f"Формат: {data['Формат']}\n"
        f"Дата: {data['Дата']}\n"
        f"Слот: {data['Слот']}\n"
        f"Время: {data['Время']}\n"
    )
    await callback.message.edit_text(text)

# === Назад ===
@dp.callback_query(F.data == "back_start")
async def back_to_start(callback: CallbackQuery):
    await menu_handler(callback.message)

@dp.callback_query(F.data == "back_format")
async def back_to_format(callback: CallbackQuery):
    await choose_format(callback)

@dp.callback_query(F.data == "back_date")
async def back_to_date(callback: CallbackQuery):
    await choose_date(callback)

@dp.callback_query(F.data == "back_slot")
async def back_to_slot(callback: CallbackQuery):
    await choose_slot(callback)

# === Админ-панель ===
@dp.message(F.text == "🔧 Панель администратора")
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔ Только админ может использовать эту панель.")
    await message.answer(
        "<b>Панель администратора:</b>\n"
        "• Добавить турнир — отправь в формате:\n"
        "Тип: tournament\nФормат: Duo\nДата: 14.04.2025\nВремя: 18:00\nСлот: Free\nНазвание: MEOW SCRIMS\nПриз: 15 000 ₸\nСтадия: 1/4\nСлоты: 16\nПроход: top 6\nСсылка: https://t.me/meowcup_final\n\n"
        "• Удалить турнир: номер\n• Рассылка: текст\n• Пользователи"
    )

@dp.message(F.text.startswith("Добавить турнир:"))
async def add_tournament(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        lines = message.text.splitlines()[1:]
        data = {line.split(": ")[0]: line.split(": ")[1] for line in lines}
        tournaments.append(data)
        await message.answer("✅ Турнир добавлен.")
    except:
        await message.answer("❌ Ошибка при добавлении турнира. Проверь формат.")

@dp.message(F.text.startswith("Удалить турнир:"))
async def delete_tournament(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        idx = int(message.text.split(":")[1].strip()) - 1
        tournaments.pop(idx)
        await message.answer("🗑 Турнир удалён.")
    except:
        await message.answer("❌ Не удалось удалить турнир.")

@dp.message(F.text.startswith("Рассылка:"))
async def broadcast(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    text = message.text.replace("Рассылка:", "").strip()
    for uid, _, _ in users:
        try:
            await bot.send_message(uid, f"📢 {text}")
        except:
            continue
    await message.answer("✅ Рассылка отправлена.")

@dp.message(F.text == "Пользователи")
async def show_users(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    text = "👥 Список пользователей:\n"
    for i, (uid, uname, full) in enumerate(users, 1):
        link = f'<a href="tg://user?id={uid}">{full}</a>'
        text += f"{i}. {uname or '—'} — {link}\n"
    await message.answer(text)

# === Очистка старых турниров ===
async def cleanup_old():
    while True:
        today = datetime.now().date()
        tournaments[:] = [t for t in tournaments if datetime.strptime(t['Дата'], "%d.%m.%Y").date() >= today]
        await asyncio.sleep(3 * 60 * 60)

# === Запуск ===
async def main():
    asyncio.create_task(cleanup_old())
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

