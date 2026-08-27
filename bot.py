import asyncio
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
                InlineKeyboardButton(text="🔒 5 букв", callback_data="btn_5_letters"),
                InlineKeyboardButton(text="🔍 6 букв", callback_data="btn_6_letters")
            ],
            [
                InlineKeyboardButton(text="🔒 Фильтр", callback_data="btn_filter"),
                InlineKeyboardButton(text="🔒 Ловушка", callback_data="btn_trap")
            ],
            [
                InlineKeyboardButton(text="🔒 Похожие на слово", callback_data="btn_similar")
            ],
            [
                InlineKeyboardButton(text="↩️ Назад", callback_data="btn_back")
            ]
        ]
    )
    return keyboard

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🔍 **ПОИСК ЮЗЕРНЕЙМА**\nВыберите нужный раздел:",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("btn_"))
async def process_buttons(callback: types.CallbackQuery):
    action = callback.data

    if action == "btn_6_letters":
        await callback.message.edit_text(
            "Вы выбрали поиск по **6 буквам**.\nВведите слово или маску для поиска:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="↩️ Назад", callback_data="btn_back")]
            ]),
            parse_mode="Markdown"
        )
    elif action == "btn_back":
        await callback.message.edit_text(
            "🔍 **ПОИСК ЮЗЕРНЕЙМА**\nВыберите нужный раздел:",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await callback.answer("⚠️ Этот раздел заблокирован!", show_alert=True)

    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
