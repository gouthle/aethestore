import os
import logging
import json
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# --- CONFIG ---
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- ДАННЫЕ И ТЕКСТЫ ---
# Сюда вставь свою ссылку на канал с отзывами
REVIEWS_LINK = "https://t.me/your_reviews_channel" 

TEXTS = {
    'en': {
        'welcome': "<b>Welcome to aethestore Premium</b> 💎\n\nChoose a service category below to proceed:",
        'repair_btn': "🚀 Book a Repair",
        'about_btn': "ℹ️ About Aethe",
        'reviews_btn': "⭐️ Customer Reviews",
        'lang_btn': "🌐 Language / Język",
        'about_text': "<b>aethestore</b> — is a high-end electronics repair boutique.\n\n📍 Based in Kraków\n🛠 iPhone, Samsung, Xiaomi specialist\n⚡️ Express service & Genuine parts",
        'reviews_intro': "<b>What our clients say:</b>\n\nWe value transparency. You can read all 100% real reviews in our official channel.",
        'reviews_link_btn': "Read Reviews ↗️",
        'sent': "✅ <b>Success!</b>\nYour request has been delivered. We will contact you shortly."
    },
    'ru': {
        'welcome': "<b>Добро пожаловать в aethestore Premium</b> 💎\n\nВыберите нужный раздел меню:",
        'repair_btn': "🚀 Оформить ремонт",
        'about_btn': "ℹ️ О сервисе",
        'reviews_btn': "⭐️ Отзывы",
        'lang_btn': "🌐 Сменить язык",
        'about_text': "<b>aethestore</b> — премиальный бутик по ремонту электроники.\n\n📍 Локация: Краков\n🛠 Специализируемся на iPhone, Samsung, Xiaomi\n⚡️ Оригинальные запчасти и гарантия",
        'reviews_intro': "<b>Отзывы наших клиентов:</b>\n\nМы за честность. Все реальные отзывы собраны в нашем отдельном канале.",
        'reviews_link_btn': "Читать отзывы ↗️",
        'sent': "✅ <b>Готово!</b>\nВаша заявка принята. Мастер свяжется с вами в ближайшее время."
    },
    'pl': {
        'welcome': "<b>Witamy w aethestore Premium</b> 💎\n\nWybierz interesującą Cię opcję:",
        'repair_btn': "🚀 Zarezerwuj naprawę",
        'about_btn': "ℹ️ O nas",
        'reviews_btn': "⭐️ Opinie",
        'lang_btn': "🌐 Zmień język",
        'about_text': "<b>aethestore</b> — butik naprawy elektroniki premium.\n\n📍 Lokalizacja: Kraków\n🛠 Specjaliści iPhone, Samsung, Xiaomi\n⚡️ Ekspresowa usługa i oryginalne części",
        'reviews_intro': "<b>Opinie naszych klientów:</b>\n\nStawiamy na transparentność. Wszystkie opinie znajdziesz na naszym kanale.",
        'reviews_link_btn': "Zobacz opinie ↗️",
        'sent': "✅ <b>Sukces!</b>\nTwoje zgłoszenie zostało wysłane. Skontaktujemy się z Tobą wkrótce."
    }
}

# --- КЛАВИАТУРЫ ---
def main_menu(lang):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    # Главная кнопка Mini App (на всю ширину)
    kb.row(types.KeyboardButton(TEXTS[lang]['repair_btn'], web_app=types.WebAppInfo(url="https://gouthle.github.io/aethestore/")))
    # Остальные кнопки
    kb.add(
        types.KeyboardButton(TEXTS[lang]['about_btn']),
        types.KeyboardButton(TEXTS[lang]['reviews_btn'])
    )
    kb.row(types.KeyboardButton(TEXTS[lang]['lang_btn']))
    return kb

# --- HANDLERS ---

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    l = message.from_user.language_code
    lang = l if l in ['ru', 'pl'] else 'en'
    await message.answer(TEXTS[lang]['welcome'], reply_markup=main_menu(lang), parse_mode='HTML')

# Обработка "О нас"
@dp.message_handler(lambda m: any(m.text in [TEXTS[l]['about_btn'] for l in TEXTS] for _ in [1]))
async def cmd_about(message: types.Message):
    lang = 'ru' if 'сервисе' in message.text else ('pl' if 'O nas' in message.text else 'en')
    await message.answer(TEXTS[lang]['about_text'], parse_mode='HTML')

# Обработка "Отзывы" (С КНОПКОЙ-ССЫЛКОЙ)
@dp.message_handler(lambda m: any(m.text in [TEXTS[l]['reviews_btn'] for l in TEXTS] for _ in [1]))
async def cmd_reviews(message: types.Message):
    lang = 'ru' if 'Отзывы' in message.text else ('pl' if 'Opinie' in message.text else 'en')
    ikb = types.InlineKeyboardMarkup()
    ikb.add(types.InlineKeyboardButton(TEXTS[lang]['reviews_link_btn'], url=REVIEWS_LINK))
    await message.answer(TEXTS[lang]['reviews_intro'], reply_markup=ikb, parse_mode='HTML')

# Смена языка
@dp.message_handler(lambda m: any(m.text in [TEXTS[l]['lang_btn'] for l in TEXTS] for _ in [1]))
async def cmd_lang(message: types.Message):
    ikb = types.InlineKeyboardMarkup(row_width=1)
    ikb.add(
        types.InlineKeyboardButton("🇺🇸 English", callback_data="set_en"),
        types.InlineKeyboardButton("🇵🇱 Polski", callback_data="set_pl"),
        types.InlineKeyboardButton("🇷🇺 Русский", callback_data="set_ru")
    )
    await message.answer("<b>Select your interface language:</b>", reply_markup=ikb, parse_mode='HTML')

@dp.callback_query_handler(lambda c: c.data.startswith('set_'))
async def callback_lang(callback: types.CallbackQuery):
    lang = callback.data.split('_')[1]
    await callback.message.answer(f"✅ Language changed to: {lang.upper()}", reply_markup=main_menu(lang))
    await callback.answer()

# Прием данных из Mini App
@dp.message_handler(content_types=['web_app_data'])
async def web_app_handler(message: types.Message):
    data = json.loads(message.web_app_data.data)
    lang = data.get('lang', 'en')
    
    # Отчет админу
    report = (f"🚨 <b>NEW ORDER</b>\n\n"
              f"📱 <b>Device:</b> {data.get('brand')} {data.get('device')}\n"
              f"📞 <b>Tel:</b> <code>{data.get('phone')}</code>\n"
              f"📍 <b>Geo:</b> {data.get('location')}\n"
              f"🔧 <b>Problem:</b> {data.get('problem')}\n"
              f"👤 <b>User:</b> @{message.from_user.username}")
    
    await bot.send_message(ADMIN_ID, report, parse_mode='HTML')
    await message.answer(TEXTS[lang]['sent'], parse_mode='HTML')

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)