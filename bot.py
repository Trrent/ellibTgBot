import pyshorteners
from aiogram import Dispatcher, Bot, types
from aiogram.utils.executor import start_webhook

from parser import get_books_list, get_book, get_book_info
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
        keyboard = types.InlineKeyboardMarkup(row_width=3)
        result = []
        for i, book in enumerate(books, 1):
            result.append(f"📕{book['title']} - {book['author']}")
            keyboard.add(types.InlineKeyboardButton(text=str(i), callback_data=f"book_{book['id']}"))
        result = '\n'.join(result)
        await message.answer(f"По запросу «{message.text.strip()}» найдено:\n\n📚Книги:\n{result}", reply_markup=keyboard)
    else:
        await message.answer('По вашему запросу ничего не найдено:c')


@dp.callback_query_handler(lambda x: x.data and x.data.startswith('book_'))
async def send_book_info(call: types.CallbackQuery):
    book_id = call.data.split('_')[1]
    book = await get_book_info(book_id)
    keyboard = types.InlineKeyboardMarkup()
    buttons = [types.InlineKeyboardButton(text=item[0], callback_data=pyshorteners.Shortener().tinyurl.short(item[1]))
               for item in book['links']]
    keyboard.add(*buttons)
    await bot.send_photo(chat_id=call.from_user.id,
                         photo=book['img'],
                         caption=f"Название: {book['title']}\n"
                                 f"Автор: {book['author']}\n"
                                 f"Жанр: {book['genre']}\n"
                                 f"Описание: {book['description']}\n"
                                 f"Рейтинг: {book['rating']}",
                         reply_markup=keyboard)


@dp.callback_query_handler(lambda x: x.data.startswith('http'))
async def get_file(call: types.CallbackQuery):
    filename = await get_book(call.data)
    await bot.send_document(call.from_user.id,
                            document=open(filename, 'rb'))
    os.remove(filename)


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
