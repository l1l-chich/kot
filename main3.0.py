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

# Состояния пользователей: кто ждёт ввод суммы
user_state = {}  # {user_id: 'awaiting_amount'}

def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("💱 Конвертировать BYN в USD"))
    markup.add(KeyboardButton("ℹ️ О боте"))
    return markup

async def get_usd_rate_from_nbrb():
    url = "https://www.nbrb.by/api/exrates/rates/USD?parammode=2"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    rate = data.get("Cur_OfficialRate")
                    if rate and isinstance(rate, (int, float)):
                        return float(rate)
    except Exception as e:
        logger.error(f"Ошибка при запросе к НБ РБ: {e}")
    return None

@bot.message_handler(commands=['start'])
async def send_welcome(message):
    user_state.pop(message.from_user.id, None)  # сброс состояния
    await bot.send_message(
        message.chat.id,
        "Привет! Я конвертирую BYN в USD по курсу Национального банка РБ.",
        reply_markup=main_menu()
    )

# Обработка кнопки "Конвертировать"
@bot.message_handler(func=lambda msg: msg.text == "💱 Конвертировать BYN в USD")
async def ask_amount(message):
    user_id = message.from_user.id
    user_state[user_id] = 'awaiting_amount'
    await bot.send_message(
        message.chat.id,
        "Введите сумму в белорусских рублях (BYN):"
    )

# Обработка ЛЮБОГО текстового сообщения — проверяем состояние
@bot.message_handler(func=lambda message: True)
async def handle_text(message):
    user_id = message.from_user.id
    text = message.text.strip()

    # Если пользователь ожидает ввод суммы
    if user_state.get(user_id) == 'awaiting_amount':
        del user_state[user_id]  # сброс состояния
        try:
            amount_byn = float(text.replace(',', '.'))
            if amount_byn <= 0:
                raise ValueError()
        except ValueError:
            await bot.send_message(
                message.chat.id,
                "❌ Введите корректное положительное число (например: 100 или 150.5)"
            )
            return

        rate = await get_usd_rate_from_nbrb()
        if rate is None:
            await bot.send_message(
                message.chat.id,
                "⚠️ Не удалось получить курс от НБ РБ. Попробуйте позже."
            )
            return

        amount_usd = amount_byn / rate
        today = datetime.now().strftime("%d.%m.%Y")
        await bot.send_message(
            message.chat.id,
            f"💱 *{amount_byn:.2f} BYN* = *{amount_usd:.2f} USD*\n\n"
            f"Курс НБ РБ на {today}: **1 USD = {rate:.4f} BYN**",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
    else:
        # Обычное сообщение — отвечаем стандартно
        if text == "ℹ️ О боте":
            await bot.send_message(
                message.chat.id,
                "Бот использует официальный курс доллара от Национального банка Республики Беларусь."
            )
        else:
            await bot.send_message(
                message.chat.id,
                "Нажмите кнопку «💱 Конвертировать BYN в USD», чтобы начать.",
                reply_markup=main_menu()
            )

# Запуск
if __name__ == "__main__":
    logger.info("🚀 Бот запущен (без register_next_step_handler)")
    asyncio.run(bot.polling(non_stop=True))