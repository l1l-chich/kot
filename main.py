#!/usr/bin/python

# This is a simple echo bot using the decorator mechanism.
# It echoes any incoming text messages.
import asyncio
import os

from telebot.async_telebot import AsyncTeleBot

bot = AsyncTeleBot(os.environ["TELEGRAM_TOKEN"])


@bot.message_handler(commands=['start'])
async def send_welcome(message):
    await bot.reply_to(message, "Привет! Я твой бот. Напиши что-нибудь или воспользуйся /help.")
@bot.message_handler(commands=['help'])

async def send_help(message):
    await bot.reply_to(message, "Я могу отвечать на любые сообщения. Просто напиши мне!")

# Обработчик любого текстового сообщения
@bot.message_handler(func=lambda message: True)
async def echo_all(message):
    await bot.send_message(
        message.chat.id,
        f"Ты написал: {message.text}\n\nЭто эхо-бот 😊"
    )


if __name__ == '__main__':
    asyncio.run(bot.polling())