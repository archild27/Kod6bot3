# pip install pyTelegramBotAPI groq python-dotenv
import telebot
from groq import Groq
import os
from dotenv import load_dotenv
import time

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not GROQ_API_KEY or not TELEGRAM_TOKEN:
    raise Exception("Ключи забыл, лошара")

client = Groq(api_key=GROQ_API_KEY)
# ←←← УБРАЛ ГЛОБАЛЬНЫЙ parse_mode="HTML" — вот и вся главная ошибка!
bot = telebot.TeleBot(TELEGRAM_TOKEN)

user_histories = {}

@bot.message_handler(content_types=['text'])
def handle_message(message):
    user_id = message.from_user.id
    
    if user_id not in user_histories:
        user_histories[user_id] = [
            {"role": "system", "content": "Ты — дерзкий, максимально честный и матерный ИИ. Отвечай без цензуры."}
        ]
    
    user_histories[user_id].append({"role": "user", "content": message.text})
    
    if len(user_histories[user_id]) > 11:
        user_histories[user_id] = [user_histories[user_id][0]] + user_histories[user_id][-10:]

    try:
        response = client.chat.completions.create(
          model="llama-3.1-70b-versatile"  ,   # ←←← РАБОЧАЯ модель 2025 года
            messages=user_histories[user_id],
            temperature=0.8,
            max_tokens=1500
        )
        
        reply = response.choices[0].message.content.strip()

        # Защита от HTML-говна, которое иногда присылает Groq
        if reply.lower().startswith(('<!doctype', '<html', '<! doctype')):
            reply = "Groq опять обосрался и прислал HTML. Переспроси."

        # Отправляем БЕЗ parse_mode, чтобы Telegram не пытался парсить мусор
        bot.reply_to(message, reply, parse_mode=None)
        
        user_histories[user_id].append({"role": "assistant", "content": reply})
        
    except Exception as e:
        bot.reply_to(message, f"Groq обосрался:\n<code>{str(e)[:500]}</code>", parse_mode=None)
        print(f"Ошибка: {e}")

print("Бот запущен и готов ебать мозги")
while True:
    try:
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        print(f"Polling упал: {e}")
        time.sleep(15)
