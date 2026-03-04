import os
import logging
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# --- НАСТРОЙКИ (Environment Variables на Render) ---
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')
# Если ADMIN_ID прилетает как строка, переводим в int
if ADMIN_ID:
    ADMIN_ID = int(ADMIN_ID)

# Порт для обмана проверки Render (по умолчанию 8080)
PORT = int(os.getenv('PORT', 8080))

# Логирование для отслеживания ошибок
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- ФЕЙКОВЫЙ СЕРВЕР ДЛЯ RENDER ---
# Это нужно, чтобы Render не убивал процесс из-за отсутствия порта
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"aethestore bot is active")

    def log_message(self, format, *args):
        return # Отключаем лишний спам логов сервера

def run_dummy_server():
    server = HTTPServer(('0.0.0.0', PORT), DummyHandler)
    server.serve_forever()

# Запуск сервера в отдельном потоке
threading.Thread(target=run_dummy_server, daemon=True).start()

# --- ТЕКСТЫ ДЛЯ МУЛЬТИЯЗЫЧНОСТИ ---
TEXTS = {
    'en': {
        'start': "<b>Welcome to aethestore!</b>\n\nPremium service for your devices. Tap the button below to book a repair.",
        'btn': "🚀 Open aethestore",
        'sent': "✅ <b>Request sent!</b>\nWe have received your details and will contact you shortly in <b>PLN</b>."
    },
    'ru': {
        'start': "<b>Добро пожаловать в aethestore!</b>\n\nПремиальный сервис для ваших устройств. Нажмите кнопку ниже для записи.",
        'btn': "🚀 Открыть aethestore",
        'sent': "✅ <b>Заявка отправлена!</b>\nМы получили ваши данные и скоро свяжемся с вами. Расчет в <b>PLN</b>."
    },
    'pl': {
        'start': "<b>Witamy w aethestore!</b>\n\nPremium serwis dla Twoich urządzeń. Kliknij przycisk poniżej, aby wysłać zgłoszenie.",
        'btn': "🚀 Otwórz aethestore",
        'sent': "✅ <b>Zgłoszenie wysłane!</b>\nOtrzymaliśmy Twoje dane и skontaktujemy się wkrótce. Rozliczenie w <b>PLN</b>."
    }
}

# --- КОМАНДА /START ---
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    # Определяем язык пользователя на основе настроек его Telegram
    user_lang = message.from_user.language_code
    lang = user_lang if user_lang in ['ru', 'pl'] else 'en'
    
    # URL твоего GitHub Pages
    web_app_url = "https://gouthle.github.io/aethestore/"
    
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton(
        text=TEXTS[lang]['btn'], 
        web_app=types.WebAppInfo(url=web_app_url)
    ))
    
    await message.answer(
        TEXTS[lang]['start'], 
        parse_mode='HTML', 
        reply_markup=kb
    )

# --- ОБРАБОТКА ДАННЫХ ИЗ MINI APP ---
@dp.message_handler(content_types=['web_app_data'])
async def get_app_data(message: types.Message):
    try:
        # Парсим JSON данные из приложения
        data = json.loads(message.web_app_data.data)
        lang = data.get('lang', 'en')
        
        # Генерируем уникальный ID для заявки
        order_id = hex(message.message_id).upper()[2:]

        # Отчет для админа (тебя)
        report = (
            f"🚨 <b>NEW ORDER #{order_id}</b>\n\n"
            f"📱 <b>Device:</b> {data.get('brand')} {data.get('device')}\n"
            f"📞 <b>Tel:</b> <code>{data.get('phone')}</code>\n"
            f"📍 <b>Geo:</b> {data.get('location')}\n"
            f"🔧 <b>Problem:</b> {data.get('problem')}\n"
            f"🌐 <b>Lang:</b> {lang.upper()}\n"
            f"👤 <b>User:</b> @{message.from_user.username if message.from_user.username else 'no_username'}"
        )

        # Отправка тебе
        if ADMIN_ID:
            await bot.send_message(ADMIN_ID, report, parse_mode='HTML')
        
        # Ответ пользователю на его языке
        await message.answer(
            TEXTS[lang]['sent'], 
            parse_mode='HTML'
        )
        
    except Exception as e:
        logging.error(f"Error processing web_app_data: {e}")

# --- ЗАПУСК ---
if __name__ == '__main__':
    print(f"--- aethestore Bot is starting on port {PORT} ---")
    executor.start_polling(dp, skip_updates=True)