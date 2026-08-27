import asyncio
import random
import string
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from google import genai

TELEGRAM_TOKEN = "8973582659:AAET5ERF6BdVqbQoRKoipUgazErgi1Unddc"
GEMINI_API_KEY = "AQ.Ab8RN6I7JI5p3nxfRx-3V-Ztu4jHoxls4F6VB_lqffc-h54bZA"

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Инициализация клиента Gemini с вашим ключом
ai_client = genai.Client(api_key=GEMINI_API_KEY)

def get_main_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔤 5 букв (Автопоиск)", callback_data="find_5"),
                InlineKeyboardButton(text="🔍 6 букв (Автопоиск)", callback_data="find_6")
            ],
            [
                InlineKeyboardButton(text="⚙️ Фильтр", callback_data="btn_filter"),
                InlineKeyboardButton(text="🎯 Ловушка", callback_data="btn_trap")
            ],
            [
                InlineKeyboardButton(text="🔄 Похожие на слово", callback_data="btn_similar")
            ]
        ]
    )

async def check_username_availability(username: str) -> bool:
    try:
        await bot.get_chat(username)
        return False  # Занят
    except Exception:
        return True   # Свободен

def generate_random_username(length: int) -> str:
    letters = string.ascii_lowercase
    return ''.join(random.choices(letters, k=length))

# Функция запроса оценки к Gemini
async def evaluate_username_with_gemini(username: str) -> str:
    prompt = (
        f"Оцени телеграм-никнейм '@{username}' для рынка криптовалютных/красивых ников. "
        f"Выдай ответ строго в таком формате и больше ничего лишнего:\n\n"
        f"├── Читаемость - [цифра от 1 до 10]/10\n"
        f"├── Примерная цена - [$минимальная-$максимальная]\n"
        f"├── Ликвидность - [цифра от 1 до 10]/10\n"
        f"└── ⚡️ Свободен"
    )

    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        return (
            f"├── Читаемость - 5/10\n"
            f"├── Примерная цена - $1-$3\n"
            f"├── Ликвидность - 5/10\n"
            f"└── ⚡️ Свободен"
        )

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🔍 **ПОИСК И ПРОВЕРКА ЮЗЕРНЕЙМОВ**\nВыберите режим работы:",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "btn_back")
async def process_back(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🔍 **ПОИСК И ПРОВЕРКА ЮЗЕРНЕЙМОВ**\nВыберите режим работы:",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data.in_({"find_5", "find_6"}))
async def process_auto_find(callback: types.CallbackQuery):
    length = 5 if callback.data == "find_5" else 6

    await callback.message.edit_text(
        f"⏳ Ищу свободный ник ({length} букв). Проверяю варианты, ожидайте...",
        parse_mode="Markdown"
    )

    found_username = None

    # Бесконечный цикл поиска до победного результата
    while not found_username:
        candidate = generate_random_username(length)

        if await check_username_availability(candidate):
            found_username = candidate
            break

        # Небольшая пауза, чтобы не упереться в лимиты Telegram API по частоте запросов
        await asyncio.sleep(0.3)

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Искать еще", callback_data=callback.data)],
        [InlineKeyboardButton(text="↩️ Главное меню", callback_data="btn_back")]
    ])

    # Запрашиваем оценку у Gemini для найденного ника
    ai_evaluation = await evaluate_username_with_gemini(found_username)

    result_text = (
        f"✅ **НИК НАЙДЕН!**\n\n"
        f"@{found_username}\n\n"
        f"{ai_evaluation}"
    )

    await callback.message.edit_text(
        result_text,
        reply_markup=back_keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data.in_({"btn_filter", "btn_trap", "btn_similar"}))
async def process_other_features(callback: types.CallbackQuery):
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ Назад", callback_data="btn_back")]
    ])
    await callback.message.edit_text(
        "⚙️ Раздел в разработке",
        reply_markup=back_keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
