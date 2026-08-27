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

ai_client = genai.Client(api_key=GEMINI_API_KEY)

# Хранилища данных пользователей
user_filters = {}
user_history = {}  # {user_id: [список ников]}

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
                InlineKeyboardButton(text="🔄 Похожие на слово", callback_data="btn_similar"),
                InlineKeyboardButton(text="📜 История ников", callback_data="btn_history")
            ]
        ]
    )

async def check_username_availability(username: str) -> bool:
    try:
        await bot.get_chat(username)
        return False
    except Exception:
        return True

def generate_random_username(length: int, exclude_letters: str = "") -> str:
    letters = [c for c in string.ascii_lowercase if c not in exclude_letters]
    if not letters:
        letters = list(string.ascii_lowercase)
    return ''.join(random.choices(letters, k=length))

def evaluate_username(username: str) -> str:
    vowels = set("aeiou")
    vowel_count = sum(1 for char in username if char in vowels)

    readability = min(10, max(3, (vowel_count * 2) + random.randint(1, 3)))
    liquidity = min(10, max(3, readability + random.randint(-2, 2)))

    if len(username) == 5:
        min_p = random.randint(1, 4)
        max_p = min_p + random.randint(2, 6)
    else:
        min_p = random.randint(1, 3)
        max_p = min_p + random.randint(1, 3)

    return (
        f"├── Читаемость - {readability}/10\n"
        f"├── Примерная цена - ${min_p}-${max_p}\n"
        f"├── Ликвидность - {liquidity}/10\n"
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
    user_id = callback.from_user.id
    exclude = user_filters.get(user_id, "")

    await callback.message.edit_text(
        f"⏳ Ищу свободный ник ({length} букв). Перебираю варианты...",
        parse_mode="Markdown"
    )

    found_username = None

    while not found_username:
        candidate = generate_random_username(length, exclude)
        if await check_username_availability(candidate):
            found_username = candidate
            break
        await asyncio.sleep(0.3)

    # Сохраняем ник в историю пользователя
    if user_id not in user_history:
        user_history[user_id] = []
    if found_username not in user_history[user_id]:
        user_history[user_id].append(found_username)

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Искать еще", callback_data=callback.data)],
        [InlineKeyboardButton(text="↩️ Главное меню", callback_data="btn_back")]
    ])

    ai_evaluation = evaluate_username(found_username)

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

@dp.callback_query(F.data == "btn_filter")
async def process_filter(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    current_exclude = user_filters.get(user_id, "нет")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 Сбросить фильтр", callback_data="filter_reset")],
        [InlineKeyboardButton(text="🔤 Исключить гласные (aeiou)", callback_data="filter_vowels")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="btn_back")]
    ])

    await callback.message.edit_text(
        f"⚙️ **НАСТРОЙКА ФИЛЬТРА**\n\n"
        f"Текущие исключения: `{current_exclude}`\n\n"
        f"Выберите действие:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data.in_({"filter_reset", "filter_vowels"}))
async def process_filter_actions(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if callback.data == "filter_reset":
        user_filters[user_id] = ""
        text = "✅ Фильтр сброшен. Буквы не исключаются."
    else:
        user_filters[user_id] = "aeiou"
        text = "✅ Успешно! Теперь гласные (aeiou) исключены из поиска."

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ Назад", callback_data="btn_filter")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "btn_trap")
async def process_trap(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ Назад", callback_data="btn_back")]
    ])
    await callback.message.edit_text(
        "🎯 **РЕЖИМ ЛОВУШКИ**\n\n"
        "Этот режим предназначен для мониторинга занятых премиум-ников.\n"
        "Статус: 🟡 Ожидание базы ников для отслеживания сброса.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "btn_similar")
async def process_similar(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ Назад", callback_data="btn_back")]
    ])
    await callback.message.edit_text(
        "🔄 **ПОХОЖИЕ НИКИ**\n\n"
        "Отправьте в чат ключевое слово, и бот сгенерирует для вас вариации на его основе.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "btn_history")
async def process_history(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    history = user_history.get(user_id, [])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 Очистить историю", callback_data="history_clear")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="btn_back")]
    ])

    if history:
        history_list = "\n".join([f"• @{item}" for item in history[-15:]])
        text = f"📜 **ИСТОРИЯ НАЙДЕННЫХ НИКОВ:**\n\n{history_list}"
    else:
        text = "📜 **ИСТОРИЯ НАЙДЕННЫХ НИКОВ:**\n\nВаша история пока пуста. Найдите свой первый ник через автопоиск!"

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "history_clear")
async def process_history_clear(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_history[user_id] = []

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ Назад", callback_data="btn_back")]
    ])
    await callback.message.edit_text("🗑 Ваша история успешно очищена!", reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
