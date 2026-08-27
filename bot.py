import asyncio
import random
import string
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# ВСТАВЬТЕ СВОЙ ТОКЕН МЕЖДУ КАВЫЧКАМИ НИЖЕ:
TOKEN = "8973582659:AAET5ERF6BdVqbQoRKoipUgazErgi1Unddc"

bot = Bot(token=TOKEN)
dp = Dispatcher()

def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(
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
    return keyboard

# Функция проверки юзернейма в Telegram
async def check_username_availability(username: str) -> bool:
    """
    Проверяет, занят ли ник в Telegram.
    Если get_chat возвращает объект, значит ник занят.
    Если падает с ошибкой (ник не найден), значит он, скорее всего, свободен.
    """
    try:
        await bot.get_chat(username)
        return False  # Ник занят
    except Exception:
        return True   # Ник свободен (или недоступен)

# Генерация случайного ника заданной длины
def generate_random_username(length: int) -> str:
    letters = string.ascii_lowercase + string.digits + "_"
    # Telegram юзернеймы должны начинаться с буквы
    first_char = random.choice(string.ascii_lowercase)
    rest = ''.join(random.choices(letters, k=length - 1))
    return f"{first_char}{rest}"

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

# Обработка кнопок автоматического поиска на 5 и 6 букв
@dp.callback_query(F.data.in_({"find_5", "find_6"}))
async def process_auto_find(callback: types.CallbackQuery):
    length = 5 if callback.data == "find_5" else 6

    await callback.message.edit_text(
        f"⏳ Ищу свободные юзернеймы длиной в **{length} символов**...\nПодождите немного.",
        parse_mode="Markdown"
    )

    found_usernames = []
    attempts = 0

    # Пытаемся найти хотя бы 3 свободных варианта за один раз
    while len(found_usernames) < 3 and attempts < 30:
        attempts += 1
        candidate = generate_random_username(length)

        # Проверяем уникальность перед запросом
        if candidate not in found_usernames:
            is_free = await check_username_availability(candidate)
            if is_free:
                found_usernames.append(candidate)
            # Небольшая пауза, чтобы не упереться в лимиты Telegram API
            await asyncio.sleep(0.4)

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Искать еще", callback_data=callback.data)],
        [InlineKeyboardButton(text="↩️ Главное меню", callback_data="btn_back")]
    ])

    if found_usernames:
        result_text = f"✨ **Найденные свободные ники ({length} символов):**\n\n"
        for user in found_usernames:
            result_text += f"@{user}\n"
    else:
        result_text = "😔 К сожалению, за эту попытку не удалось найти свободные варианты. Попробуйте еще раз!"

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

    titles = {
        "btn_filter": "⚙️ **Настройка фильтра**\nЗдесь можно настроить исключение символов.",
        "btn_trap": "🎯 **Режим ловушки**\nАвтоматический мониторинг удаления чужих ников.",
        "btn_similar": "🔄 **Похожие ники**\nГенерация вариантов на основе вашего ключевого слова."
    }

    await callback.message.edit_text(
        titles.get(callback.data, "Раздел в разработке"),
        reply_markup=back_keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
