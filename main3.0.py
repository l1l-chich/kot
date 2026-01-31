import os
import asyncio
import logging
import aiohttp
from datetime import datetime
from telebot.async_telebot import AsyncTeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = AsyncTeleBot(os.environ["TELEGRAM_TOKEN"])

# Состояния пользователей
user_state = {}  # {user_id: 'awaiting_amount_byn' или 'awaiting_amount_rub'}

# === МЕНЮ ===
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    # Конвертации — 6 штук, в 3 строки по 2 кнопки
    conversions = [
        "💱 BYN → USD",
        "💱 USD → BYN",
        "💱 RUB → USD",
        "💱 USD → RUB",
        "💱 RUB → BYN",
        "💱 BYN → RUB"  # ← новая кнопка
    ]

    # Добавляем конвертации парами
    for i in range(0, len(conversions), 2):
        row = conversions[i:i + 2]
        if len(row) == 2:
            markup.add(KeyboardButton(row[0]), KeyboardButton(row[1]))
        else:
            markup.add(KeyboardButton(row[0]))

    # Отдельные кнопки — по одной в строке
    markup.add(KeyboardButton("📊 Курсы валют"))
    markup.add(KeyboardButton("ℹ️ О боте"))

    return markup


# === Получение курса из НБ РБ ===
async def get_rate_from_nbrb(currency: str):
    url = f"https://www.nbrb.by/api/exrates/rates/{currency}?parammode=2"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    return await resp.json()
    except Exception as e:
        logger.error(f"Ошибка при запросе {currency}: {e}")
    return None


# === /start ===
@bot.message_handler(commands=['start'])
async def send_welcome(message):
    user_state.pop(message.from_user.id, None)
    await bot.send_message(
        message.chat.id,
        "Привет! Я конвертирую валюты по официальным курсам НБ РБ.\n\nВыберите операцию:",
        reply_markup=main_menu()
    )


# === Обработчики конвертаций ===
@bot.message_handler(func=lambda msg: msg.text == "💱 BYN → USD")
async def byn_to_usd(message):
    user_state[message.from_user.id] = "awaiting_amount_byn"
    await bot.send_message(message.chat.id, "Введите сумму в *BYN*:", parse_mode="Markdown")


@bot.message_handler(func=lambda msg: msg.text == "💱 USD → BYN")
async def usd_to_byn(message):
    user_state[message.from_user.id] = "awaiting_amount_usd_to_byn"
    await bot.send_message(message.chat.id, "Введите сумму в *USD*:", parse_mode="Markdown")


@bot.message_handler(func=lambda msg: msg.text == "💱 RUB → USD")
async def rub_to_usd(message):
    user_state[message.from_user.id] = "awaiting_amount_rub"
    await bot.send_message(message.chat.id, "Введите сумму в *RUB*:", parse_mode="Markdown")


@bot.message_handler(func=lambda msg: msg.text == "💱 USD → RUB")
async def usd_to_rub(message):
    user_state[message.from_user.id] = "awaiting_amount_usd_to_rub"
    await bot.send_message(message.chat.id, "Введите сумму в *USD*:", parse_mode="Markdown")


@bot.message_handler(func=lambda msg: msg.text == "💱 RUB → BYN")
async def rub_to_byn(message):
    user_state[message.from_user.id] = "awaiting_amount_rub_to_byn"
    await bot.send_message(message.chat.id, "Введите сумму в *RUB*:", parse_mode="Markdown")


@bot.message_handler(func=lambda msg: msg.text == "💱 BYN → RUB")  # ← НОВАЯ
async def byn_to_rub(message):
    user_state[message.from_user.id] = "awaiting_amount_byn_to_rub"
    await bot.send_message(message.chat.id, "Введите сумму в *BYN*:", parse_mode="Markdown")


# === Курсы валют ===
@bot.message_handler(func=lambda msg: msg.text == "📊 Курсы валют")
async def send_rates(message):
    usd_data = await get_rate_from_nbrb("USD")
    rub_data = await get_rate_from_nbrb("RUB")
    today = datetime.now().strftime("%d.%m.%Y")

    text = f"🏦 *Курсы НБ РБ на {today}*:\n\n"

    if usd_data:
        usd_rate = usd_data["Cur_OfficialRate"]
        text += f"🇺🇸 1 USD = *{usd_rate:.4f} BYN*\n"
    else:
        text += "🇺🇸 1 USD = ❌\n"

    if rub_data:
        rub_scale = rub_data["Cur_Scale"]
        rub_rate = rub_data["Cur_OfficialRate"]
        rub_per_one = rub_rate / rub_scale
        text += f"🇷🇺 1 RUB = *{rub_per_one:.4f} BYN* (за 100 RUB: {rub_rate:.4f})\n"
    else:
        text += "🇷🇺 1 RUB = ❌\n"

    await bot.send_message(message.chat.id, text, parse_mode="Markdown")


# === О боте ===
@bot.message_handler(func=lambda msg: msg.text == "ℹ️ О боте")
async def about(message):
    await bot.send_message(
        message.chat.id,
        "🤖 Бот использует официальные курсы Национального банка Республики Беларусь.\n"
        "Данные обновляются по будням."
    )


# === Универсальный обработчик ввода ===
@bot.message_handler(func=lambda message: True)
async def handle_amount_input(message):
    user_id = message.from_user.id
    state = user_state.get(user_id)
    text = message.text.strip()

    valid_states = {
        "awaiting_amount_byn",
        "awaiting_amount_rub",
        "awaiting_amount_rub_to_byn",
        "awaiting_amount_usd_to_byn",
        "awaiting_amount_usd_to_rub",
        "awaiting_amount_byn_to_rub"  # ← новое состояние
    }

    if state not in valid_states:
        await bot.send_message(
            message.chat.id,
            "Выберите действие из меню:",
            reply_markup=main_menu()
        )
        return

    try:
        amount = float(text.replace(',', '.'))
        if amount <= 0:
            raise ValueError
    except ValueError:
        await bot.send_message(
            message.chat.id,
            "❌ Введите положительное число (например: 100 или 500.75)"
        )
        return

    usd_data = await get_rate_from_nbrb("USD")
    rub_data = await get_rate_from_nbrb("RUB")

    reply = ""

    if state == "awaiting_amount_byn":
        if not usd_: return await bot.send_message(message.chat.id, "⚠️ Ошибка курса USD.")
        usd_rate = usd_data["Cur_OfficialRate"]
        result_usd = amount / usd_rate
        reply = f"💱 *{amount:.2f} BYN* = *{result_usd:.2f} USD*\nКурс: 1 USD = {usd_rate:.4f} BYN"

    elif state == "awaiting_amount_usd_to_byn":
        if not usd_: return await bot.send_message(message.chat.id, "⚠️ Ошибка курса USD.")
        usd_rate = usd_data["Cur_OfficialRate"]
        result_byn = amount * usd_rate
        reply = f"💱 *{amount:.2f} USD* = *{result_byn:.2f} BYN*\nКурс: 1 USD = {usd_rate:.4f} BYN"

    elif state == "awaiting_amount_rub":
        if not usd_ or not rub_: return await bot.send_message(message.chat.id, "⚠️ Ошибка курсов.")
        usd_rate = usd_data["Cur_OfficialRate"]
        rub_scale = rub_data["Cur_Scale"]
        rub_rate_total = rub_data["Cur_OfficialRate"]
        rub_to_byn = rub_rate_total / rub_scale
        byn_amount = amount * rub_to_byn
        result_usd = byn_amount / usd_rate
        reply = (
            f"💱 *{amount:.2f} RUB* = *{result_usd:.2f} USD*\n"
            f"• 1 USD = {usd_rate:.4f} BYN\n• 1 RUB = {rub_to_byn:.4f} BYN"
        )

    elif state == "awaiting_amount_usd_to_rub":
        if not usd_ or not rub_: return await bot.send_message(message.chat.id, "⚠️ Ошибка курсов.")
        usd_rate = usd_data["Cur_OfficialRate"]
        rub_scale = rub_data["Cur_Scale"]
        rub_rate_total = rub_data["Cur_OfficialRate"]
        rub_to_byn = rub_rate_total / rub_scale
        byn_amount = amount * usd_rate
        result_rub = byn_amount / rub_to_byn
        reply = (
            f"💱 *{amount:.2f} USD* = *{result_rub:.2f} RUB*\n"
            f"• 1 USD = {usd_rate:.4f} BYN\n• 1 RUB = {rub_to_byn:.4f} BYN"
        )

    elif state == "awaiting_amount_rub_to_byn":
        if not rub_: return await bot.send_message(message.chat.id, "⚠️ Ошибка курса RUB.")
        rub_scale = rub_data["Cur_Scale"]
        rub_rate_total = rub_data["Cur_OfficialRate"]
        rub_to_byn = rub_rate_total / rub_scale
        result_byn = amount * rub_to_byn
        reply = (
            f"💱 *{amount:.2f} RUB* = *{result_byn:.2f} BYN*\n"
            f"Курс: 1 RUB = {rub_to_byn:.4f} BYN"
        )

    elif state == "awaiting_amount_byn_to_rub":  # ← НОВАЯ ЛОГИКА
        if not rub_: return await bot.send_message(message.chat.id, "⚠️ Ошибка курса RUB.")
        rub_scale = rub_data["Cur_Scale"]
        rub_rate_total = rub_data["Cur_OfficialRate"]
        rub_to_byn = rub_rate_total / rub_scale  # 1 RUB
        byn_to_rub = 1 / rub_to_byn
        result_rub = amount * byn_to_rub
        reply = (
            f"💱 *{amount:.2f} BYN* = *{result_rub:.2f} RUB*\n"
            f"Курс: 1 RUB = {rub_to_byn:.4f} BYN → 1 BYN = {byn_to_rub:.4f} RUB"
        )

    del user_state[user_id]
    await bot.send_message(
        message.chat.id,
        reply,
        parse_mode="Markdown",
        reply_markup=main_menu()
    )


# === Запуск ===
if __name__ == "__main__":
    logger.info("🚀 Бот запущен. Поддержка всех пар: BYN, RUB, USD")
    asyncio.run(bot.polling(non_stop=True))