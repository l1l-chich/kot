import os
import asyncio
import logging
from telebot.async_telebot import AsyncTeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


bot = AsyncTeleBot(os.environ["TELEGRAM_TOKEN"])

# Создаём клавиатуру
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.add(KeyboardButton("ℹ️ О боте"))
    markup.add(KeyboardButton("📸 Отправить фото"))
    markup.add(KeyboardButton("🆔 Узнать свой ID"))
    return markup

# /start
@bot.message_handler(commands=['start'])
async def send_welcome(message):
    user = message.from_user
    logger.info(f"Пользователь {user.id} ({user.username or user.first_name}) запустил бота")
    await bot.send_message(
        message.chat.id,
        f"Привет, {user.first_name}! 👋\nВыбери действие:",
        reply_markup=main_menu()
    )

# /help
@bot.message_handler(commands=['help'])
async def send_help(message):
    await bot.send_message(message.chat.id, "Нажми на кнопки ниже или используй команды:\n/start — меню\n/id — твой ID")

# /id
@bot.message_handler(commands=['id'])
async def send_id(message):
    await bot.reply_to(message, f"Ваш ID: `{message.from_user.id}`", parse_mode="Markdown")

# Обработка текстовых кнопок
@bot.message_handler(func=lambda msg: msg.text == "ℹ️ О боте")
async def about(message):
    await bot.send_message(message.chat.id, "🤖 Это демо-бот с расширенным функционалом.\nРазработан для обучения и тестов.")

@bot.message_handler(func=lambda msg: msg.text == "🆔 Узнать свой ID")
async def button_id(message):
    await send_id(message)

@bot.message_handler(func=lambda msg: msg.text == "📸 Отправить фото")
async def request_photo(message):
    await bot.send_message(message.chat.id, "Отлично! Пожалуйста, отправь мне любое фото (можно с подписью).")

# Обработка фотографий
@bot.message_handler(content_types=['photo'])
async def handle_photo(message):
    user = message.from_user
    caption = message.caption or "Без подписи"
    photo_file_id = message.photo[-1].file_id  # Берём фото в наивысшем разрешении

    logger.info(f"Получено фото от {user.id}, подпись: {caption}")

    # Отправляем обратно фото с комментарием
    await bot.send_photo(
        message.chat.id,
        photo_file_id,
        caption=f"✅ Получено! Подпись: *{caption}*\nСпасибо за фото!",
        parse_mode="Markdown"
    )

# Обработка любого другого текста
@bot.message_handler(func=lambda message: True)
async def fallback(message):
    await bot.send_message(
        message.chat.id,
        "Я понял, что ты написал, но пока не умею обрабатывать такие сообщения.\n"
        "Используй меню или команды!",
        reply_markup=main_menu()
    )

# Запуск
if __name__ == "__main__":
    logger.info("🚀 Бот запускается...")
    try:
        asyncio.run(bot.polling(non_stop=True, request_timeout=60))
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")