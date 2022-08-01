from aiogram import Dispatcher, Bot, types
from aiogram.utils.executor import start_webhook

from parser import get_books_list, get_book
from db import BotDB

import logging
import os

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get('TOKEN')
HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')

WEBHOOK_HOST = f'https://{HEROKU_APP_NAME}.herokuapp.com'
WEBHOOK_PATH = f'/webhook/{TOKEN}'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'

WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = os.getenv('PORT', default=5000)
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
botDB = BotDB(os.environ.get('DB_URI'))


async def on_startup(dispatcher):
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)


async def on_shutdown(dispatcher):
    await bot.delete_webhook()


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id
    if not botDB.user_exists(user_id):
        botDB.add_user(user_id)
    await message.answer(f'Привет, {message.from_user.first_name}')
    await message.answer('Напиши название книги или имя автора :)')


@dp.message_handler()
async def search_book(message: types.Message):
    books = await get_books_list(message.text.strip().lower())
    if books:
        keyboard = types.InlineKeyboardMarkup()
        buttons = [types.InlineKeyboardButton(text=f"{book['title']} - {book['author']}", callback_data=book['id'])
                   for book in books]
        keyboard.add(*buttons)
        await message.answer(f"По запросу «{message.text.strip()}» найдено:", reply_markup=keyboard)
    else:
        await message.answer('По вашему запросу ничего не найдено:c')

if __name__ == '__main__':
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
